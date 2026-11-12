from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import SendOTPRequest, VerifyOTPRequest, TokenResponse
from app.services import auth_service
from app.core.security import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/send-otp")
async def send_otp(body: SendOTPRequest):
    otp = auth_service.generate_otp(body.identifier)
    # Check if user already exists to tell frontend if this is sign-in or sign-up
    user_exists = auth_service.check_user_exists(body.identifier)
    return {
        "success": True,
        "message": "OTP sent successfully.",
        "is_existing_user": user_exists,
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(body: VerifyOTPRequest):
    is_valid = auth_service.verify_otp(body.identifier, body.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Please try again.",
        )

    user = auth_service.get_or_create_user(body.identifier)

    token_data = {
        "sub": user["id"],
        "role": user.get("role", "customer"),
        "email": user.get("email"),
        "phone": user.get("phone"),
    }
    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user.get("name"),
            "email": user.get("email"),
            "phone": user.get("phone"),
            "role": user.get("role"),
            "saved_address": user.get("saved_address"),
        },
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = auth_service.get_user_by_id(current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"success": True, "message": "Logged out successfully."}


@router.put("/profile")
async def update_profile(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    updated_user = auth_service.update_user_profile(current_user["sub"], body)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated_user


@router.post("/check-user")
async def check_user(body: SendOTPRequest):
    """Check if a user already exists (for sign-in vs sign-up detection)."""
    exists = auth_service.check_user_exists(body.identifier)
    return {"exists": exists}
