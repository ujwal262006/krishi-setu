
# Krishi Setu — Frontend

React + Vite Progressive Web App (PWA) for Krishi Setu — helps Indian farmers discover
government agricultural schemes, search in plain/colloquial language, and check their
eligibility instantly.

## Tech Stack

- React 18 + Vite
- Tailwind CSS v4
- react-router-dom (routing)
- axios (API calls)
- vite-plugin-pwa (installable, offline-capable PWA)

## Prerequisites

- Node.js 18+ and npm
- Backend running locally (see `/backend/README.md`) at `http://localhost:8000`

## Setup

```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend/` root:

VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_ADMIN_PASSWORD=<choose-a-password>


- `VITE_API_BASE_URL` — base URL of the backend API.
- `VITE_ADMIN_PASSWORD` — gates access to `/admin`, `/crawler`, `/master` on the frontend
  (see Known Limitations below).

## Running locally

```bash
npm run dev
```

App runs at `http://localhost:5173`.

## Building for production / testing the PWA

```bash
npm run build
npm run preview
```

`preview` serves the production build (default `http://localhost:4173`) — required to test
PWA install and offline behavior, since these don't work in dev mode.

If testing on a different port than `5173`, add it to `ALLOWED_ORIGINS` in the backend's
`.env` (e.g. `["http://localhost:5173", "http://localhost:4173"]`) or the browser will
block API requests with a CORS error.

## App Structure

src/
api/ # axios calls, one file per backend resource
components/ # shared UI (Navbar, AdminNavbar)
context/ # AuthContext — farmer + admin auth state
pages/ # one file per route
utils/ # helpers (phone number normalization)


## Routes

| Route | Access | Description |
|---|---|---|
| `/login`, `/register` | Public | Farmer auth |
| `/browse` | Farmer | Search & browse schemes |
| `/schemes/:id` | Farmer | Full scheme detail |
| `/eligibility` | Farmer | Run eligibility checks |
| `/eligibility-history` | Farmer | Past eligibility results |
| `/assistant` | Farmer | AI chat (streaming, RAG-based) |
| `/profile` | Farmer | Edit profile / delete account |
| `/admin-login` | Public | Admin password gate |
| `/admin` | Admin | Stats, scheme CRUD, farmers, search logs |
| `/crawler` | Admin | Trigger crawls, view job status/detail |
| `/master` | Admin | Ministry & source CRUD |

## Authentication

Two separate auth flows, intentionally kept independent:

1. **Farmer auth** — JWT issued by the backend on login, stored in `localStorage`,
   attached via an axios interceptor.
2. **Admin auth** — a single shared password (`VITE_ADMIN_PASSWORD`) gates the frontend
   routes under `/admin`, `/crawler`, `/master`. This is a **frontend-only** gate.

## Known Limitations

- **Admin routes are not protected on the backend.** The `/admin/*` API endpoints have
  no authentication of their own (the backend code notes this should be added — API key
  or role-based auth — before production). The frontend password gate prevents accidental
  access through the UI, but the API itself is still open if called directly. Backend-side
  auth should be added before this is considered production-ready.
- **No change-password flow.** The backend does not currently expose an endpoint to
  change a farmer's password.
- **Ministry has no delete guard.** Deleting a ministry that still has linked schemes or
  sources may fail at the database level; the UI surfaces the resulting error but does
  not pre-check for linked records.
- **Some crawled scheme records have incomplete eligibility data.** A handful of schemes
  ingested by the crawler have an empty `eligibility_criteria` JSON, so the eligibility
  engine correctly reports "no requirement specified" for every criterion rather than a
  real result. This is a data-completeness issue in the crawled source, not a bug in the
  eligibility display — schemes with populated criteria return correct, specific