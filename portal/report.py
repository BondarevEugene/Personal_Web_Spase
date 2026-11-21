"""Read-only owner-side commercial accounting CLI; no public admin endpoint."""
import json
from collections import Counter
from datetime import datetime, timezone
from sqlalchemy import func, select
from portal.db import session_factory
from portal.models import (Customer, Invoice, Organization, PaymentRecord,
                           RegistrationEvent, Subscription)

def summarize(db):
    events = db.scalars(select(RegistrationEvent.created_at)).all()
    months = Counter(value.strftime("%Y-%m") for value in events)
    invoice_rows = db.execute(select(Invoice.status, func.count()).group_by(Invoice.status)).all()
    plan_rows = db.execute(select(Subscription.plan_code, func.count()).group_by(Subscription.plan_code)).all()
    confirmed_rows = db.execute(
        select(PaymentRecord.currency, func.sum(PaymentRecord.amount_minor))
        .where(PaymentRecord.status == "confirmed", PaymentRecord.verified_at.is_not(None))
        .group_by(PaymentRecord.currency)
    ).all()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "organizations": db.scalar(select(func.count(Organization.id))),
        "customers": db.scalar(select(func.count(Customer.id))),
        "registration_events": len(events),
        "registrations_by_month": dict(sorted(months.items())),
        "subscriptions_by_plan": dict(sorted(plan_rows)),
        "invoices_by_status": dict(sorted(invoice_rows)),
        "confirmed_revenue_by_currency_minor": {currency: int(amount) for currency, amount in confirmed_rows},
        "currency_note": "Payment values in minor units, no FX conversions.",
        "payment_gateway_connected": False,
    }

def main():
    with session_factory()() as db:
        print(json.dumps(summarize(db), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
