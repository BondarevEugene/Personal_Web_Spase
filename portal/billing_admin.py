"""Owner-only terminal tooling for plan catalog. No public admin route.

A price is never picked by the customer, and editing the catalog never changes
the immutable amount/currency of an existing invoice.
"""
from __future__ import annotations

import argparse
import json
import os

from portal.db import session_factory
from portal.models import BillingPlan, PlanPriceChange
from portal.billing import PAID_PLANS, BillingRuleError


def configure_plan(db, code: str, price_minor: int, actor: str,
                   *, enable: bool = False) -> BillingPlan:
    if code not in PAID_PLANS or price_minor < 1 or price_minor > 100_000_000:
        raise BillingRuleError("Choose a paid plan and a positive, bounded price in kopecks")
    if not actor or len(actor) > 100:
        raise BillingRuleError("Operator identity is required for audit")
    plan = db.get(BillingPlan, code)
    if not plan or plan.currency != "UAH" or plan.period_months != 1:
        raise BillingRuleError("Unrecognized or non-UAH monthly plan")
    old_price = plan.price_minor
    if old_price != price_minor:
        db.add(PlanPriceChange(plan_code=code, old_price_minor=old_price,
                               new_price_minor=price_minor, currency="UAH", actor=actor))
        plan.price_minor = price_minor
    if enable:
        plan.is_enabled = True
    db.flush()
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="OmniFactory local billing operator CLI")
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("plans", help="List catalog without exposing client data")
    update = subs.add_parser("set-price", help="Set monthly UAH plan price in kopecks")
    update.add_argument("--code", choices=PAID_PLANS, required=True)
    update.add_argument("--minor", type=int, required=True)
    update.add_argument("--actor", default=os.getenv("OMNI_BILLING_OPERATOR", ""))
    update.add_argument("--enable", action="store_true",
                        help="Allow PENDING invoice requests; NOT real online checkout")
    args = parser.parse_args()
    with session_factory()() as db:
        if args.command == "set-price":
            result = configure_plan(db, args.code, args.minor, args.actor, enable=args.enable)
            db.commit()
            print(f"Updated {result.code}: {result.price_minor} {result.currency} minor units; "
                  f"invoice requests enabled={result.is_enabled}. Online checkout remains OFF.")
        else:
            plans = db.query(BillingPlan).order_by(BillingPlan.code).all()
            print(json.dumps([{
                "code": p.code, "name": p.name,
                "price_minor": p.price_minor, "currency": p.currency,
                "enabled_for_pending_invoices": p.is_enabled,
                "period_months": p.period_months,
            } for p in plans], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
