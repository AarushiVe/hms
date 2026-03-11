# Hospital Management System (HMS)

This is my MAD-2 Hospital Management System project.
I kept the backend in Flask + SQLite and built the UI in Vue.

Project structure:

```text
HMS/
  frontend/
    src/
      components/
        LoginPage.vue
        RegisterPage.vue
        DashboardPage.vue
      services/
        api.js
      App.vue
      main.js
    index.html
    package.json
    vite.config.js
  backend/
    routes/
      api.py
    models/
      models.py
    app.py
    celery_worker.py
  app/                 # active Flask implementation
  templates/
  static/
  run.py
  celery_worker.py
```

`frontend/` has Vue components (`.vue`) and router pages.
`backend/` keeps the expected folder layout for routes and models.

## Tech Stack
- Flask (API)
- Vue.js (frontend)
- Bootstrap
- SQLite
- Redis
- Celery + Redis

## Default Admin
- Username: `admin`
- Password: `admin123`

## Backend Run
```bash
cd /Users/aarushiverma/Documents/Playground/HMS
source .venv/bin/activate
python run.py
```

## Celery Worker + Beat
```bash
cd /Users/aarushiverma/Documents/Playground/HMS
source .venv/bin/activate
celery -A celery_worker:celery worker --loglevel=info
celery -A celery_worker:celery beat --loglevel=info
```

## Frontend Run (Vue CLI-style project)
```bash
cd /Users/aarushiverma/Documents/Playground/HMS/frontend
npm install
npm run dev
```

The Vue frontend proxies `/api` calls to `http://127.0.0.1:5000`.

## Notes
- Database is created programmatically via SQLAlchemy.
- Appointment times are restricted to 30-minute slots (`:00` and `:30`).
- Optional enhancement used: Chart.js in Vue dashboard.
- Monthly report remains HTML-based (no PDF generation used).

## What I Focused On
- Role-based workflows (Admin, Doctor, Patient)
- Slot-based booking rules to avoid clashes
- Clean API separation between frontend and backend
- Keeping UI simple and easy to demo in viva

## Known Limitations
- Monthly report is generated as HTML, but mail integration is basic.
- UI is responsive for common laptop/mobile sizes, but not deeply optimized for tablets.
