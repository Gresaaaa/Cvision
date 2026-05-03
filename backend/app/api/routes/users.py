from fastapi import APIRouter

router = APIRouter()

@router.get("/profile")
def get_profile():
    return {"msg": "user profile"}

@router.put("/profile")
def update_profile():
    return {"msg": "profile updated"}

@router.get("/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}