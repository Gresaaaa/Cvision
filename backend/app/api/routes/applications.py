from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def apply():
    return {"msg": "application submitted"}

@router.get("/my")
def my_applications():
    return {"applications": []}

@router.get("/job/{job_id}")
def job_applications(job_id: int):
    return {"job_id": job_id, "applications": []}

@router.patch("/{application_id}")
def update_application(application_id: int):
    return {"msg": f"application {application_id} updated"}