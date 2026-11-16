# OMNIFACTORY FOUNDERS — INSTALL ASSETS

Website HTML and stylesheet are in this GitHub branch. The two real photos are provided in an additional archive to preserve the original generated binary files; the GitHub text connector does not support sending local binary assets directly.

Put exactly these two generated images in your local Git checkout:

- `omni_site/static/founders/founder-01.webp`
- `omni_site/static/founders/founder-02.webp`

Then commit both images to **the same branch**:

```powershell
git add omni_site/static/founders/founder-01.webp omni_site/static/founders/founder-02.webp
git commit -m "assets(site): add matched founders portraits"
git push origin feat/founders-omni-editorial-20261116
```

Do not merge until those assets are present and `/studio-assets/founders/founder-01.webp` and `/studio-assets/founders/founder-02.webp` return HTTP 200. The PR code alone will show empty/broken images.

The names and titles are intentionally generic and should be replaced with verified names/titles if the founders authorize them. Originals and edited portraits should not be accidentally committed outside the explicit public site assets location. Image publication should be approved by the people pictured.

Run the existing portal with `.venv-omni`, not the broken older `.venv`:

```powershell
.\.venv-omni\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8010
```

Open `http://127.0.0.1:8010/#founders`.
