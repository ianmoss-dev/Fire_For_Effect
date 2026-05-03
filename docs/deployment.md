# Deployment

Target MVP setup:

- Backend API: Render web service from `api/`
- Frontend app: Cloudflare Pages from `web/`
- State: browser-owned planning session, stateless API requests
- Secrets: environment variables only, never committed

## Render API

The root `render.yaml` defines the FastAPI service:

- Runtime: `python`
- Root directory: `api`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- Plan: `free`

Render setup path:

1. Create a new Render Blueprint or Web Service from the GitHub repo.
2. Use branch `rebuild/web-api` while we are rebuilding, then switch to `main` at cutover.
3. Confirm the service root directory is `api`.
4. Confirm the health check path is `/health`.
5. After deploy, test `https://<service>.onrender.com/health`.

Notes:

- `api/.python-version` pins local and Render Python intent to `3.13.5`.
- If the free Render service sleeps, first requests can be slow. That is acceptable for MVP testing.
- Add paid hosting only after the app has real usage or launch pressure.

## Cloudflare Pages Frontend

Once `web/` exists, Cloudflare Pages should use:

- Root directory: `web`
- Build command: `npm run build`
- Build output directory: `dist`

Required environment variable:

- `VITE_API_BASE_URL=https://<render-service>.onrender.com`

Cloudflare setup path:

1. Create a Pages project from the GitHub repo.
2. Set the project root to `web`.
3. Set the build command to `npm run build`.
4. Set the output directory to `dist`.
5. Add `VITE_API_BASE_URL` in Pages environment variables.
6. Deploy previews from the rebuild branch before production cutover.

## Local Checks Before Deploy

Backend:

```powershell
cd api
.\.venv\Scripts\python -m unittest discover -s tests -v
uvicorn app.main:app --reload
```

Frontend after scaffold:

```powershell
cd web
npm install
npm run build
```

## References

- Render Blueprint YAML reference: https://render.com/docs/blueprint-spec
- Render FastAPI deploy guide: https://render.com/docs/deploy-fastapi
- Cloudflare Pages build configuration: https://developers.cloudflare.com/pages/configuration/build-configuration/
