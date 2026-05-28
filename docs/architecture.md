# Architecture

## Overview

CVision follows a clean client-server architecture:

- React frontend communicates only through REST endpoints.
- FastAPI backend exposes all business operations and Swagger docs.
- PostgreSQL stores normalized relational data through SQLAlchemy models.
- Redis caches search results, taxonomy lists, and AI-derived responses.
- Background jobs run after resume uploads and job applications.

## Multi-Tenancy

Each company acts as a tenant.

- `users.company_id` links recruiter accounts to a company.
- `job_posts.company_id` scopes job ownership.
- Candidate visibility for company users is restricted to applications tied to that company.
- Resume and candidate detail access also respect tenant boundaries.

## Roles

- `candidate`
- `company`
- `admin`

Roles are stored in the database and seeded together with permissions.

## Major Backend Modules

- `app/models.py`: 20+ SQLAlchemy models covering users, resumes, jobs, applications, AI results, notifications, and audit data.
- `app/api/routes/*`: feature-based API routing.
- `app/services/ai_service.py`: OpenAI-enabled resume analysis, job scoring, and cover letter generation.
- `app/services/background_jobs.py`: post-upload and post-application work.
- `app/services/cache_service.py`: Redis wrapper with in-memory fallback.
- `app/middleware/request_context.py`: request logging and token-aware context.

## Frontend Structure

- Context providers:
  - `AuthContext`
  - `UserContext`
  - `JobContext`
  - `NotificationContext`
- Page groups:
  - public
  - candidate
  - company
  - admin

## Background Processing

- Resume uploads enqueue AI analysis.
- New applications enqueue match-score generation.
- Status updates create candidate notifications.

This satisfies the asynchronous/background requirement while keeping the app straightforward to demo.
