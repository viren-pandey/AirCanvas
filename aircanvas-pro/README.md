<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# AirCanvas Pro Frontend

Angular frontend for AirCanvas Pro. It now connects to the same FastAPI backend contract used by the Python desktop UI.

## Run Locally

Prerequisites:
- Node.js
- FastAPI backend running on `http://127.0.0.1:8000` (or set `localStorage.aircanvas_api_base_url`)

1. Install dependencies:
   `npm install`
2. Start frontend:
   `npm run dev`
3. Log in from the frontend. JWT is stored in localStorage as `aircanvas_user_token`.
4. Open Settings -> **Python UI Connection** and copy the `.env` block for desktop runtime:
   - `API_BASE_URL`
   - `AIRCANVAS_API_BASE_URL`
   - `AIRCANVAS_JWT_TOKEN`

This keeps web frontend and Python UI synced to the same user/session/frame backend.
