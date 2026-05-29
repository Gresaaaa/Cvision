from fastapi import APIRouter

from app.api.routes import admin, ai, applications, auth, companies, jobs, notifications, resumes, saved_jobs, search, taxonomy, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(resumes.router)
api_router.include_router(ai.router)
api_router.include_router(jobs.router)
api_router.include_router(applications.router)
api_router.include_router(search.router)
api_router.include_router(taxonomy.router)
api_router.include_router(saved_jobs.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
