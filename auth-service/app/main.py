from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from db import SessionLocal, engine
from models import Base, User
from schemas import TokenResponse, UserLogin, UserRegister, UserResponse
from security import (
    create_access_token,
    get_current_claims,
    get_current_token,
    get_password_hash,
    revoke_token,
    verify_password,
)

app = FastAPI(title="Auth Service")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"service": "auth-service", "status": "ok"}


@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=email,
        password_hash=get_password_hash(payload.password),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    token, expires_in = create_access_token(str(user.id), user.email, user.role)
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=user,
    )


@app.get("/auth/me")
def me(claims: dict = Depends(get_current_claims), db: Session = Depends(get_db)):
    try:
        user_id = int(claims["sub"])
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject") from error

    user = db.query(User).filter(User.id == user_id).first()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not available")

    return {
        "sub": claims["sub"],
        "email": user.email,
        "role": user.role,
        "exp": claims["exp"],
        "is_active": user.is_active,
    }


@app.get("/auth/verify")
def verify_token(claims: dict = Depends(get_current_claims)):
    return claims


@app.post("/auth/logout")
def logout(token: str = Depends(get_current_token), claims: dict = Depends(get_current_claims)):
    revoke_token(token, claims["exp"])
    return {"message": "Logged out successfully"}
