# OmniFactory Bot Lab — Security, Telegram Vault & Specific User Access

## Business requirement

A customer owns each bot. Later, that customer can grant access to named
registered users. Access must be explicit, bot-specific, revocable, auditable,
and must **never** imply access to other bots, Railway, other organizations'
data, costs, or Telegram secrets.

This phase implements a deliberately narrow policy:

| Principal | Bot metadata | Secret status | Change token | Invite users | Existing Graph Studio editing | Railway mutations |
| --- | --- | --- | --- | --- | --- | --- |
| Owner | Yes | Yes | Yes | Yes | Existing owner API | No |
| Invited viewer | Shared card only | No | No | No | No | No |
| Invited operator | Shared card only | No | No | No | No | No |

An operator label **does not yet grant** deploy/restart/graph-edit privileges.
Those would require each downstream API to implement dedicated, audited
per-project permission checks before we enable the corresponding action.

## Telegram token vault

- A per-project, owner-only encrypted Fernet record. Different key from
  Railway OAuth: `OMNI_BOT_VAULT_FERNET_KEY`.
- Plaintext token accepted **only** through HTTPS and an authenticated,
  CSRF-protected `PUT /api/v1/bot-security/bots/{id}/credential` JSON body.
- No `GET` endpoint returns plaintext, encrypted bytes, or token fingerprint.
- Ciphertext payload includes the owner ID and project ID. Decryption rejects
  cross-project or cross-owner substitutions.
- Explicit `POST .../credential/verify` uses a fixed endpoint
  `api.telegram.org/bot<TOKEN>/getMe` and stores only the confirmed
  Telegram bot identity. Until verification, UI says "not verified".
- Secret rotation invalidates previous verification until checked again.
- Local deletion removes the OMNIFACTORY copy; it does **not** revoke the
  token at BotFather. To revoke a compromised BotFather token, the customer
  must use Telegram's BotFather tooling.
- A missing encryption key fails closed with 503. No auto-generated
  production vault key.
- This phase does **not** deploy a bot, inject the token into Railway or
  guarantee the absence of upstream proxy/request-body logging.

### Key setup

On the operator's secure machine (Windows PowerShell):

```powershell
.\.venv-clean\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy that value into your **hosting secret manager** as
`OMNI_BOT_VAULT_FERNET_KEY`, **not** Git, screenshots, chat, user-facing bot
settings, or a published ZIP archive. Use the same key across all web workers.
Back it up securely: if lost, existing encrypted credentials cannot be
recovered. Key rotation/multi-key decrypt strategy still needs implementation.

### Production hardening required

1. Disable reverse-proxy access logging of sensitive Telegram `/bot<TOKEN>/`
   URLs, including if the upstream Telegram client logs URLs. Never log
   request bodies or Authorization header. Redact at ingress, APM and error
   reporting.
2. Encrypt DB backups and restrict operator/admin access to encrypted columns.
3. Add distributed rate limiting for token verification, invitations and
   sign-in. Current per-project pending invitation count is limited to 10;
   it is not a distributed per-minute abuse guard.
4. Use a cloud KMS or dedicated Secrets Manager for enterprise Managed Cloud
   in preference to storing secrets in the operational DB.
5. Implement key versioning and staged rotation; no user-facing export.
6. Review session security, HTTPS proxy configuration, email verification,
   MFA, recovery, deletion, privacy requirements and incident response before
   production.

## Explicit per-user invitation

- Owner chooses an **existing active username** and role `viewer` or
  `operator` (both metadata-only initially).
- A random one-time secret is shown once; only SHA-256 of the capability is
  stored in DB.
- The invited person must sign into **their own matching account** and
  submit the invitation code in the Lab.
- 24-hour expiry; atomic compare-and-swap consumes capability once.
- The owner may cancel pending invitations or revoke an accepted grant.
- Only minimal shared bot metadata is returned to invitees via
  `GET /api/v1/bot-security/shared`. The older Graph Studio endpoints retain
  owner-only restrictions. **Do not use the shared metadata response to bypass
  those restrictions.**
- Audit events record actions and target customer IDs without tokens.

The invitation is an *out-of-band capability*, not automatic email delivery;
email verification and trusted delivery channels will be a subsequent phase.
Invitation codes must not be placed in a URL query string.

## New API

- `GET /api/v1/bot-security/capabilities`
- `GET/PUT/DELETE /api/v1/bot-security/bots/{id}/credential`
- `POST /api/v1/bot-security/bots/{id}/credential/verify`
- `POST/GET /api/v1/bot-security/bots/{id}/invitations`
- `DELETE /api/v1/bot-security/bots/{id}/invitations/{invitation_id}`
- `POST /api/v1/bot-security/invitations/accept`
- `GET /api/v1/bot-security/bots/{id}/access`
- `DELETE /api/v1/bot-security/bots/{id}/access/{grantee_id}`
- `GET /api/v1/bot-security/shared`
- `GET /api/v1/bot-security/bots/{id}/audit`

All sensitive mutations require existing portal session and
`X-Omni-CSRF` header. Read APIs return minimal, role-scoped data.

## Database and deployment

Alembic `20261114_portal_09` depends on `08` and introduces:
`portal_bot_credentials`, `portal_bot_access_invitations`,
`portal_bot_access_grants`, `portal_bot_security_audit`.

Verify that target DB is a **development** database before migrating:

```powershell
git fetch origin
git switch -c feat/bot-lab-tenant-security-20261114 --track origin/feat/bot-lab-tenant-security-20261114
.\.venv-clean\Scripts\python.exe -m pytest -q tests/test_bot_security.py tests/test_bot_lab.py --tb=short
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini current
# Only after verifying DB target, backup and full tests:
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini upgrade head
```

Open `/bots/lab` and select an owned bot. The "Безопасность и доступ"
workbench allows token insertion, verification, rotation/deletion, targeted
invites, grant revocation and audit inspection.

## Next work: production-safe release

No live Railway provisioning in this PR. Next changes: customer consent and
verified spending; secret injection by isolated worker; immutable runtime
image digest; deployment reconciliation; actual Telegram webhook/health
verification; audited live operations; eventually dedicated role-scoped
Graph Studio collaboration.
