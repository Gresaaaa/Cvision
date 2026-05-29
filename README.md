# CVision

CVision is a full-stack distributed recruitment platform built from the supplied planner and PDF requirements. It supports three roles, multi-tenancy by company, Ollama-powered resume analysis and cover letters, background processing, Redis caching, automatic Swagger docs, and a React Context API frontend.

## Stack

- Backend: FastAPI
- Frontend: React + Context API + Vite
- Database: PostgreSQL
- ORM: SQLAlchemy
- Authentication: JWT
- Cache: Redis
- Docs: FastAPI Swagger / OpenAPI
- AI integration: Ollama with deterministic local fallback

## Included Features

- Candidate flow:
  - Register and login
  - Edit profile
  - Upload versioned resumes
  - Trigger AI resume analysis
  - Search and filter jobs
  - Save jobs
  - Apply to jobs
  - Track application status and AI score
  - Generate cover letter drafts
  - Open interview alerts and see date, location, meeting link, and notes
- Company flow:
  - Register company accounts
  - Manage company profile
  - Create, view, update, and deactivate jobs
  - Add custom job requirements when a skill is not listed
  - View job applications
  - Read submitted cover letters from applications
  - Rank candidates by score
  - Search candidates within tenant-safe scope
- Admin flow:
  - Manage users and companies
  - Manage skills and categories
  - Inspect system overview and audit logs
- Platform features:
  - Swagger docs at `/docs`
  - Redis-backed caching with in-memory fallback
  - Background jobs for resume analysis and application scoring
  - Role-based authorization and tenant checks
  - Alembic migration scaffold
  - Pytest backend tests
  - GitHub Actions CI
  - Docker Compose setup

## Project Structure

```text
backend/     FastAPI app, models, routes, services, tests, Alembic
frontend/    React app with Context API, role-based pages, shared styling
docs/        Architecture, requirement coverage, project management notes
uploads/     Resume storage mount point
```

## Quick Start

### 1. Run with Docker

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 2. Run locally without Docker

Backend:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Make sure PostgreSQL and Redis are running, and copy the example env files if you want to customize settings.

## Seeded Admin

- Email: `admin@cvision.io`
- Password: `Admin123!`

The seed step also creates starter categories, skills, and a demo company.

## Testing

Backend tests:

```bash
cd backend
pytest
```

## Ollama Integration

Install Ollama locally, pull a model such as `llama3.2`, and keep the Ollama app running while the backend is on.

Example local setup:

```bash
ollama pull llama3.2
```

The backend reads:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`

When Ollama is not available, the project still works through deterministic fallback logic.

## Requirement Coverage

See:

- [Architecture notes](docs/architecture.md)
- [Requirements matrix](docs/requirements-matrix.md)
- [Project management notes](docs/project-management.md)
