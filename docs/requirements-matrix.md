# Requirements Matrix

## Planner Coverage

- Candidate features: implemented through `/auth`, `/users/profile`, `/resumes`, `/jobs`, `/applications`, `/saved-jobs`, `/ai`.
- Company features: implemented through `/auth/register`, `/companies/me`, `/jobs`, `/jobs/{id}/applications`, `/applications/{id}/status`, `/search/candidates`.
- Admin features: implemented through `/admin/users`, `/admin/companies`, `/admin/skills`, `/admin/categories`, `/admin/system-overview`, `/admin/audit-logs`.
- AI suggestions: implemented with resume analysis, job match preview, persisted application score, and cover letter generation.
- Multi-tenancy: enforced through `company_id` ownership and scoped candidate/resume access.

## PDF Requirement Coverage

1. Client-server architecture:
   - React frontend and FastAPI backend are fully separated.
2. HTTP/HTTPS communication:
   - All application behavior runs through REST endpoints.
3. Minimum 20 endpoints:
   - The backend includes well over 20 endpoints.
4. RESTful API and framework:
   - FastAPI with structured routing.
5. OOP:
   - Service classes and model-driven domain structure.
6. Swagger:
   - Automatic FastAPI docs at `/docs`.
7. ORM and database:
   - SQLAlchemy + PostgreSQL.
8. Authentication and authorization:
   - JWT auth and role-based access control.
9. Middleware:
   - Request logging and token-aware middleware.
10. Frontend React + Context:
   - Implemented with multiple context providers.
11. Testing + CI/CD:
   - Pytest + GitHub Actions.
12. Minimum 20 models and migrations:
   - 20+ SQLAlchemy models and Alembic scaffold.
13. Project documentation:
   - README and architecture/project docs included.
14. Project management:
   - Documented board and delivery flow in project-management notes.
15. Git collaboration:
   - GitHub Actions and PR-oriented workflow documented.
16. OpenAI integration:
   - AI service supports OpenAI API and fallback behavior.
17. Caching:
   - Redis-backed cache service.
18. Background jobs:
   - Resume analysis and application scoring run in background tasks.
19. Multi-tenancy:
   - Company-scoped access implemented.
20. Search and filtering:
   - Job search and candidate search endpoints implemented.
