from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_jobs():
    return {"jobs": []}

@router.post("/")
def create_job():
    return {"msg": "job created"}

@router.get("/{job_id}")
def get_job(job_id: int):
    return {"job_id": job_id}

@router.put("/{job_id}")
def update_job(job_id: int):
    return {"msg": f"job {job_id} updated"}

@router.delete("/{job_id}")
def delete_job(job_id: int):
    return {"msg": f"job {job_id} deleted"}