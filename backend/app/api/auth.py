"""
auth.py — All authentication APIs:
  1)  POST /auth/login          — Username+Password → JWT → saved in response (frontend stores in cookie)
  2)  POST /auth/reset-password — Send OTP mail to user
  3)  GET  /auth/profile        — Read JWT from header, return user profile
  4)  GET  /auth/profile/full   — Get JWT from cookie, fetch profile + image
  13) POST /auth/confirm-email  — Confirmation email OTP API (new registrations)
  POST /auth/signup             — Create account
  POST /auth/verify-otp         — Verify OTP for email confirmation
  POST /auth/reset-password/verify  — Verify reset OTP & set new password
"""
import random, uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user_id
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token
from app.core.email import send_email, otp_email_html
from app.db.models import User, EmailOTP

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── SCHEMAS ───────────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    otp_type: str = "EMAIL_VERIFY"   # EMAIL_VERIFY | PASSWORD_RESET | CONFIRM

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class SetNewPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

class ConfirmEmailRequest(BaseModel):
    email: EmailStr

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── HELPERS ───────────────────────────────────────────────────────────────
def _generate_otp() -> str:
    return str(random.randint(100000, 999999))

def _save_otp(db: Session, user_id: str, otp_code: str, otp_type: str):
    # Invalidate old OTPs of same type
    db.query(EmailOTP).filter(
        EmailOTP.UserId == user_id,
        EmailOTP.OtpType == otp_type,
        EmailOTP.IsUsed == False,
    ).update({"IsUsed": True})
    otp = EmailOTP(
        UserId=user_id,
        OtpCode=otp_code,
        OtpType=otp_type,
        ExpiresAt=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(otp)
    db.commit()


# ── 1) LOGIN — Username + Password → JWT saved to cookie ─────────────────
@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.Email == req.email, User.IsActive == True).first()
    if not user or not verify_password(req.password, user.PasswordHash):
        raise HTTPException(401, "Invalid email or password")
    if not user.IsEmailVerified:
        raise HTTPException(403, "Email not verified. Please check your inbox for the OTP.")
    user.LastLoginAt = datetime.utcnow()
    db.commit()
    token = create_access_token(subject=str(user.UserId))
    # Save JWT in HTTP-only cookie (API #1 from notes)
    response.set_cookie(
        key="rag_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax",
    )
    return AuthResponse(access_token=token)


# ── SIGNUP ────────────────────────────────────────────────────────────────
@router.post("/signup", status_code=201)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.Email == req.email).first():
        raise HTTPException(409, "Email already registered")
    user = User(
        Name=req.name,
        Email=req.email,
        PasswordHash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    otp_code = _generate_otp()
    _save_otp(db, user.UserId, otp_code, "EMAIL_VERIFY")
    send_email(req.email, "Verify your email — Production RAG", otp_email_html(otp_code, "Email Verification"))
    return {"message": "Account created! OTP sent to your email."}


# ── VERIFY OTP (email verify / password reset / confirm) ─────────────────
@router.post("/verify-otp")
def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.Email == req.email).first()
    if not user:
        raise HTTPException(404, "User not found")
    otp = db.query(EmailOTP).filter(
        EmailOTP.UserId == user.UserId,
        EmailOTP.OtpCode == req.otp,
        EmailOTP.OtpType == req.otp_type,
        EmailOTP.IsUsed == False,
        EmailOTP.ExpiresAt > datetime.utcnow(),
    ).first()
    if not otp:
        raise HTTPException(400, "Invalid or expired OTP")
    otp.IsUsed = True
    if req.otp_type in ("EMAIL_VERIFY", "CONFIRM"):
        user.IsEmailVerified = True
    user.UpdatedAt = datetime.utcnow()
    db.commit()
    return {"message": "OTP verified successfully"}


# ── 2) RESET PASSWORD — Send OTP mail to user ─────────────────────────────
@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.Email == req.email, User.IsActive == True).first()
    if not user:
        raise HTTPException(404, "No account found with this email")
    otp_code = _generate_otp()
    _save_otp(db, user.UserId, otp_code, "PASSWORD_RESET")
    send_email(req.email, "Reset your password — Production RAG", otp_email_html(otp_code, "Password Reset"))
    return {"message": "Password reset OTP sent to your email"}


# ── RESET PASSWORD VERIFY & SET NEW PASSWORD ──────────────────────────────
@router.post("/reset-password/confirm")
def reset_password_confirm(req: SetNewPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.Email == req.email).first()
    if not user:
        raise HTTPException(404, "User not found")
    otp = db.query(EmailOTP).filter(
        EmailOTP.UserId == user.UserId,
        EmailOTP.OtpCode == req.otp,
        EmailOTP.OtpType == "PASSWORD_RESET",
        EmailOTP.IsUsed == False,
        EmailOTP.ExpiresAt > datetime.utcnow(),
    ).first()
    if not otp:
        raise HTTPException(400, "Invalid or expired OTP")
    otp.IsUsed = True
    user.PasswordHash = hash_password(req.new_password)
    user.UpdatedAt = datetime.utcnow()
    db.commit()
    return {"message": "Password reset successfully. Please log in."}


# ── 13) CONFIRMATION EMAIL API — Confirm new registration ─────────────────
@router.post("/confirm-email")
def confirm_email(req: ConfirmEmailRequest, db: Session = Depends(get_db)):
    """Send a fresh confirmation OTP (for re-sending or new registrations)."""
    user = db.query(User).filter(User.Email == req.email).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.IsEmailVerified:
        return {"message": "Email is already verified"}
    otp_code = _generate_otp()
    _save_otp(db, user.UserId, otp_code, "CONFIRM")
    send_email(req.email, "Confirm your email — Production RAG", otp_email_html(otp_code, "Email Confirmation"))
    return {"message": "Confirmation email sent"}


# ── 3) USER PROFILE — Read JWT from cookie ───────────────────────────────
@router.get("/profile-from-cookie")
def profile_from_cookie(request: Request, db: Session = Depends(get_db)):
    """API #3: Read cookies to get user profile."""
    token = request.cookies.get("rag_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    from jose import JWTError
    from app.core.jwt import decode_token
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return _user_response(user)


# ── 4) USER PROFILE API — Get JWT from header, fetch profile + image ─────
@router.get("/profile")
def get_profile(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """API #4: Get JWT from Authorization header, fetch profile + profile image."""
    user = db.query(User).filter(User.UserId == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return _user_response(user)


def _user_response(user):
    return {
        "user_id": user.UserId,
        "name": user.Name,
        "email": user.Email,
        "profile_pic_url": user.ProfilePicUrl or "",
        "is_email_verified": user.IsEmailVerified,
        "created_at": user.CreatedAt,
        "last_login_at": user.LastLoginAt,
    }


# ── LOGOUT (clear cookie) ─────────────────────────────────────────────────
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("rag_token")
    return {"message": "Logged out successfully"}
