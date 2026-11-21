# OmniFactory Managed Cloud — Phase 2: Railway OAuth & encrypted vault

This is an **opt-in connection** workflow, not live deployment. It is stacked on
Phase 1 PR #28 and the earlier Automation Studio PRs.

## Implemented

- Railway Authorization Code with **S256 PKCE**, random 10-minute one-time
  state, `prompt=consent` and `offline_access` to enable refresh tokens.
- OAuth callback bound to the existing logged-in OmniFactory customer.
- Railway identity checked with `GET /oauth/me` and stable `sub`.
- Access and refresh tokens encrypted in SQL with **Fernet** using a key
  provided only through `OMNI_CLOUD_OAUTH_FERNET_KEY`.
- Refresh-token rotation; `refresh` updates both encrypted tokens.
- Local disconnect deletes tokens and invalidates unconsumed OAuth states.
- Account status displays provider user/name, approved scopes, expiry and
  refresh availability — **never returns raw credentials**.
- Browser UI on `/cloud/deploy` connects, refreshes and disconnects.
- Alembic revision `20261114_portal_06`, requiring Phase 1 revision 05.
- Tests mock Railway responses; no network or billable provider calls.

## Operator setup (required before enabling)

1. In Railway, open **Workspace Settings → Developer → New OAuth App**.
   Set an application name and the **exact** redirect URI:

   - Local (example): `http://127.0.0.1:8001/api/v1/cloud/railway/callback`
   - Hosted: `https://your-domain.example/api/v1/cloud/railway/callback`

   Railway requires exact redirect match, including port and trailing slash.

2. Copy the Railway OAuth **client ID** and **client secret**. Never ask the
   customer for their Railway password or store an account access token in
   the generated bot code.

3. Generate one secure encryption key **on the operator's machine**, not in
   Git, and store it in the hosting secret manager:

   ```powershell
   .\.venv-clean\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

   Treat this key as a long-term secret. All FastAPI instances must share it.
   Losing it makes stored connections undecryptable. Rotation needs a future
   explicit re-encryption procedure; never replace it casually.

4. Configure environment variables in the deployment secret manager:

   - `OMNI_RAILWAY_OAUTH_CLIENT_ID`
   - `OMNI_RAILWAY_OAUTH_CLIENT_SECRET`
   - `OMNI_RAILWAY_OAUTH_REDIRECT_URI`
   - `OMNI_CLOUD_OAUTH_FERNET_KEY`

   For multi-worker sessions also set `OMNI_PORTAL_CSRF_SECRET` consistently
   and use a persistent database for existing customer sessions.

5. Request only required permissions. Current stage requests:

   `openid email profile offline_access workspace:member project:member`

   Railway lets users choose which resources they share. The selected
   resources and final granted scopes must be verified again before any
   billable provisioning action.

6. Run full tests on a **confirmed development database** before migration.
   Do not point these commands at unknown production/Neon credentials:

   ```powershell
   .\.venv-clean\Scripts\python.exe -m pytest tests/test_railway_oauth.py tests/test_cloud_deploy.py -q
   .\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini current
   # Only after verifying database endpoint:
   .\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini upgrade head
   ```

## Server API

- `GET /api/v1/cloud/railway/status`: current connection summary.
- `POST /api/v1/cloud/railway/authorize`: requires customer session and
  `X-Omni-CSRF`, returns Railway authorize URL. Browser redirects to Railway.
- `GET /api/v1/cloud/railway/callback`: handles code, verifies state and
  issuer, consumes state, exchanges code, validates Railway subject, encrypts
  credentials and returns a 303 redirect to `/cloud/deploy`.
- `POST /api/v1/cloud/railway/refresh`: CSRF-protected token refresh.
- `DELETE /api/v1/cloud/railway/disconnect`: locally destroys encrypted
  tokens and cancels outstanding grants.

The callback never exposes tokens in its URL or API response. Exchange errors
return a safe status flag to the UI. Error responses must not print tokens.

## Revocation and lifecycle

Local disconnection removes OMNIFACTORY's access/refresh tokens from its
database, but does **not itself revoke Railway authorization**. The customer
can revoke authorization at **Railway → Account Settings → Apps → Revoke
Access**. Revocation at Railway immediately invalidates tokens.

Access tokens expire after about one hour. Railway refresh tokens can rotate;
the latest refresh token must replace the old one. A future worker will need
DB coordination when refreshing concurrently.

## Outstanding production blockers

- A real Railway OAuth application must be registered and e2e-tested.
- Encrypted vault key management, backups, rotation and audit must be verified
  operationally, including log redaction and reverse-proxy query-string logs.
- Railway workspace/project selection must be verified before provisioning.
- Provisioning GraphQL adapter, deployment worker, budget estimation, rollout,
  healthcheck and rollback are **next stage**, not included here.
- Managed Cloud multi-tenant data-plane isolation, billing and quotas remain
  separate work.
- BYOC customers cannot assume that granting an OAuth scope alone authorizes
  costs: explicit resource and billing confirmation is still required.

## Official sources

- https://docs.railway.com/integrations/oauth
- https://docs.railway.com/integrations/oauth/login-and-tokens
- https://docs.railway.com/integrations/oauth/scopes-and-user-consent
- https://docs.railway.com/integrations/oauth/authorized-apps
- https://docs.railway.com/integrations/api
