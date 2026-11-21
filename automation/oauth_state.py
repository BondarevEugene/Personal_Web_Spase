"""OAuth state issuance and atomic one-time redemption.

No provider OAuth exchange is performed here. Callback handlers must verify the
authenticated browser session and use the returned connection ID for token exchange.
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import timedelta

from sqlalchemy import update

from automation.connection_vault import oauth_nonce
from portal.models import AutomationOAuthState, utcnow


def issue_state(db, *, customer_id: str, connection_id: str) -> str:
    nonce = oauth_nonce()
    db.add(AutomationOAuthState(
        nonce_hash=hashlib.sha256(nonce.encode()).hexdigest(),
        customer_id=customer_id,
        connection_id=connection_id,
        expires_at=utcnow() + timedelta(minutes=10),
    ))
    db.commit()
    return nonce


def consume_state(db, *, nonce: str, customer_id: str) -> str | None:
    if not isinstance(nonce, str) or len(nonce) > 256 or len(nonce) < 32:
        return None
    digest = hashlib.sha256(nonce.encode()).hexdigest()
    # No provider tokens are written here. CAS prevents replay across workers.
    row = db.get(AutomationOAuthState, digest)
    if row is None or not hmac.compare_digest(row.customer_id, customer_id):
        return None
    if row.expires_at <= utcnow() or row.consumed_at is not None:
        return None
    result = db.execute(update(AutomationOAuthState).where(
        AutomationOAuthState.nonce_hash == digest,
        AutomationOAuthState.customer_id == customer_id,
        AutomationOAuthState.consumed_at.is_(None),
        AutomationOAuthState.expires_at > utcnow(),
    ).values(consumed_at=utcnow()))
    db.commit()
    return row.connection_id if result.rowcount == 1 else None
