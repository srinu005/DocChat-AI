# Deployment (free tier)

DocChat-AI deploys on **Render** (free Web Service) + **Upstash** (free Redis,
two instances). Total cost: $0.

## Why this looks different from a typical frontend+backend+database deploy

This project's architecture needs three running pieces locally (FastAPI, Celery
worker, Redis) -- but **Render's free tier only supports Web Services. Background
Workers require a paid plan (~$7/mo minimum).**

The workaround: a dedicated [`Dockerfile.render`](../Dockerfile.render) runs the
Celery worker and the Uvicorn server **in the same container**, as two processes
in one Render free Web Service. This keeps the existing, tested Celery-based
architecture intact -- no code or test changes -- and stays fully free.

> This is a one-container-does-both workaround, not a textbook production setup.
> It has no process supervisor: if the Celery worker process dies, it doesn't
> auto-restart until the whole container restarts. Fine for a portfolio demo;
> a real production deployment would use a paid worker service or a proper
> process manager (e.g. supervisord).

## Why `Dockerfile.render` exists as a separate file from the main `Dockerfile`

The main `Dockerfile` has multi-stage `app` and `worker` targets. The `worker`
stage deliberately doesn't copy `frontend/` (it doesn't need it for its own
separate-container use case). Docker builds the **last** stage in a file by
default when no target is specified -- which here is `worker`. A naive build
without an explicit target would produce an image missing `frontend/`, and the
app would crash on boot:
```
RuntimeError: Directory 'frontend/static' does not exist
```
(Confirmed by direct testing.) `Dockerfile.render` avoids this ambiguity entirely
by copying everything, unconditionally, in one single-stage file.

## 1. Redis -- Upstash (two free instances)

Go to [upstash.com](https://upstash.com) → sign up → **Create Database** (free tier: 256MB, 500K commands/month, permanent -- no expiry).

Create **two** separate databases:
- `docchat-main` -- used for both `REDIS_URL` and `CELERY_BROKER_URL`
- `docchat-results` -- used for `CELERY_RESULT_BACKEND`

**Why two instances instead of one with database indexes `/0` and `/1`** (which
is what the code defaults to locally): Upstash's support for Redis's `SELECT`
command (logical multi-database separation within one instance) couldn't be
confirmed with certainty. Creating two separate free instances instead
sidesteps that question completely -- each gets its own unique host, guaranteed
isolated, with no `SELECT` involved. Upstash allows 10 free database instances
per account, so this costs nothing extra.

For each database, copy the connection string shown as **"Redis URL"** (or
build it from the host/port/password shown) -- it'll look like:
```
rediss://default:AbC123xyz@humble-whale-12345.upstash.io:6379
```
Note the double `s` in `rediss://` -- that's TLS, required by Upstash.

## 2. Backend + worker -- Render

[render.com](https://render.com) → sign in with GitHub → **New → Blueprint** →
select this repo. Render reads [`render.yaml`](../render.yaml) and proposes a
single `docchat-ai` web service.

Fill in the `sync: false` variables:

| Variable | Value |
|---|---|
| `GOOGLE_API_KEY` | Your real Gemini key |
| `REDIS_URL` | Your `docchat-main` Upstash connection string |
| `CELERY_BROKER_URL` | **Same value** as `REDIS_URL` |
| `CELERY_RESULT_BACKEND` | Your `docchat-results` Upstash connection string (the *other* instance) |

Click **Deploy Blueprint**.

### If you hit an SSL/TLS connection error

Upstash's certificates are standard, CA-signed (not self-signed), so this
shouldn't be necessary -- but if Celery's Redis transport complains about SSL
verification, append this query parameter to both the broker and backend URLs:
```
rediss://default:AbC123xyz@humble-whale-12345.upstash.io:6379?ssl_cert_reqs=CERT_REQUIRED
```

### Gotcha: Render's free tier has no Shell

Same as any other Render free service -- there's no interactive shell to debug
inside the running container. Use the **Logs** tab for everything; you can see
both the Uvicorn and Celery worker output interleaved there, same as the local
`docker compose` logs you're already used to reading.

## 3. Verify it's actually working

Once deployed, visit your Render URL. You should see the DocChat-AI UI itself
(not just an API) -- this one app serves both the frontend and the API from the
same origin, so there's no separate frontend deploy step and no CORS
configuration needed, unlike a split frontend/backend project.

Upload a document, ask a question, and watch the **Logs** tab -- you should see
the same pattern as local testing: `Task ... received` followed eventually by
`Task ... succeeded in X.Ys`.

### Expect it to be slow, and plan your `POLL_MAX_RETRIES` accordingly

Real Gemini responses for this project have been observed taking up to ~176
seconds (see `frontend/static/js/app.js`'s `POLL_MAX_RETRIES` comment). Free-tier
Render instances also have less CPU than a local machine. Don't be alarmed if a
question takes 1-3 minutes end to end on this deployment.

### Cold start

Same free-tier behavior as any Render free Web Service: after 15 minutes with
no incoming HTTP requests, the container sleeps. The **Celery worker sleeps
with it** (it's the same container) -- so if you queue a question right as the
service wakes from sleep, expect the first request after a gap to take longer
than usual.