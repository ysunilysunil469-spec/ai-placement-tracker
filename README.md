# Career Passport AI

Real full-stack hackathon app: React/Vite frontend + FastAPI backend + SQLite database.

## Local run

### Backend (Windows CMD)
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload

Open http://localhost:8000/health. It must show database=connected and opportunities=5.

### Frontend (second CMD)
cd frontend
npm install
npm run dev

Open http://localhost:5173.

## API connection
The frontend uses VITE_API_URL. Locally it defaults to http://localhost:8000.
For deployment set VITE_API_URL to your deployed FastAPI URL before building.

## Database
SQLite file is created automatically at backend/career_passport.db. Tables: students, opportunities, applications, notifications.

## Deploy
Backend start command: uvicorn main:app --host 0.0.0.0 --port $PORT
Frontend build command: npm install && npm run build
Frontend publish directory: dist

For persistent production storage, use PostgreSQL if your host does not provide persistent disk. This MVP uses SQLite for fastest hackathon setup.
