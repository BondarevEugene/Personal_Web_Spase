"""Read-only organization finance statements from recorded invoices and verified payments.

No endpoint here settles a payment or mutates subscriptions. Monetary totals
are computed in minor units, per currency, and verified payment status only.
"""
from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select

from portal.db import session_factory
from portal.models import Invoice, PaymentRecord
from portal.routes import current_customer, form_page
from portal.security import secure_request

router = APIRouter(prefix="/account/finance", tags=["Customer Finance"])
_PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_STATUSES = {"pending": "Ожидает оплаты", "paid": "Оплачен",
             "draft": "Черновик", "cancelled": "Отменён",
             "expired": "Срок истёк", "refunded": "Возврат"}


def month_bounds(raw: str | None):
    value = raw or datetime.utcnow().strftime("%Y-%m")
    if not _PERIOD.fullmatch(value):
        raise HTTPException(422, "Период должен быть в формате YYYY-MM")
    year, month = map(int, value.split("-"))
    if year < 2000 or year > 2100:
        raise HTTPException(422, "Период вне допустимого диапазона")
    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
    return value, start, end


def statement(db, org_id: str, start: datetime, end: datetime):
    invoices = db.scalars(select(Invoice).where(
        Invoice.org_id == org_id,
        Invoice.created_at >= start,
        Invoice.created_at < end,
    ).order_by(Invoice.created_at.desc(), Invoice.id.desc())).all()
    # Payment records are only recognized when the gateway verified the event.
    payments = db.scalars(select(PaymentRecord).where(
        PaymentRecord.org_id == org_id,
        PaymentRecord.status == "confirmed",
        PaymentRecord.verified_at.is_not(None),
        PaymentRecord.verified_at >= start,
        PaymentRecord.verified_at < end,
    ).order_by(PaymentRecord.verified_at.desc(), PaymentRecord.id.desc())).all()
    totals = defaultdict(lambda: {"invoiced": 0, "pending": 0, "confirmed": 0})
    for invoice in invoices:
        totals[invoice.currency]["invoiced"] += invoice.amount_minor
        if invoice.status == "pending":
            totals[invoice.currency]["pending"] += invoice.amount_minor
    for payment in payments:
        totals[payment.currency]["confirmed"] += payment.amount_minor
    return invoices, payments, dict(sorted(totals.items()))


@router.get("")
@router.get("/")
def finance_page(request: Request, period: str | None = None):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            return RedirectResponse("/account/login", status_code=303)
        selected, start, end = month_bounds(period)
        invoices, payments, totals = statement(db, user.org_id, start, end)
        return form_page(request, "client_finance.html", user=user,
                         period=selected, totals=totals, invoices=invoices,
                         payments=payments, invoice_statuses=_STATUSES)


def excel_safe(value: object) -> str:
    """Prefix formula-looking CSV cell values; retain quoted UTF-8 content."""
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


@router.get("/export.csv")
def export_csv(request: Request, period: str | None = None):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            raise HTTPException(401, "Войдите в аккаунт")
        selected, start, end = month_bounds(period)
        invoices, payments, _ = statement(db, user.org_id, start, end)
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\r\n")
        writer.writerow(["type", "date", "id", "description", "status",
                         "amount_minor", "currency"])
        for invoice in invoices:
            writer.writerow(["invoice", invoice.created_at.isoformat(),
                             excel_safe(invoice.id), excel_safe(invoice.description),
                             excel_safe(invoice.status), invoice.amount_minor,
                             excel_safe(invoice.currency)])
        for payment in payments:
            writer.writerow(["verified_payment", payment.verified_at.isoformat(),
                             excel_safe(payment.id), excel_safe(payment.provider),
                             "confirmed", payment.amount_minor,
                             excel_safe(payment.currency)])
        payload = "\ufeff" + output.getvalue()
        return Response(content=payload, media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition":
                                 f'attachment; filename="omni-finance-{selected}.csv"',
                                 "Cache-Control": "private, no-store",
                                 "X-Content-Type-Options": "nosniff"})
