from pydantic import BaseModel, EmailStr, Field


class GuestUpgradeRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class EmailVerifyConfirm(BaseModel):
    token: str


class AccountDeleteRequest(BaseModel):
    # Optional: guest accounts have no password to confirm with — deletion
    # for them only requires a valid access token. Real (email/Google)
    # accounts must confirm with their current password so a stolen but
    # still-live access token alone can't destroy the account; Google-only
    # accounts (no password set) instead confirm by re-presenting a fresh
    # Google ID token via `google_id_token`.
    password: str | None = None
    google_id_token: str | None = None
