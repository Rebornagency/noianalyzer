from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

# NEW CREDIT SYSTEM MODELS
class UserStatus(str, Enum):
    active = "active"
    suspended = "suspended"
    banned = "banned"

class TransactionType(str, Enum):
    purchase = "purchase"
    usage = "usage"
    refund = "refund"
    bonus = "bonus"  # For free trial credits

class User(BaseModel):
    user_id: str
    email: EmailStr
    credits: int = 0
    total_credits_purchased: int = 0
    total_credits_used: int = 0
    status: UserStatus = UserStatus.active
    created_at: datetime
    last_active: datetime
    free_trial_used: bool = False

class CreditTransaction(BaseModel):
    transaction_id: str
    user_id: str
    type: TransactionType
    amount: int  # Positive for additions, negative for deductions
    description: str
    stripe_session_id: Optional[str] = None
    created_at: datetime

class CreditPackage(BaseModel):
    package_id: str
    name: str
    credits: int
    price_cents: int  # Price in cents for Stripe
    stripe_price_id: str
    description: str
    is_active: bool = True

class JobCreate(BaseModel):
    email: EmailStr

class JobResponse(BaseModel):
    job_id: str
    checkout_url: Optional[str] = None  # Only for credit purchases
    credits_deducted: Optional[int] = None  # For usage tracking

class JobInfo(BaseModel):
    job_id: str
    status: JobStatus
    report_url: Optional[str] = None
    error: Optional[str] = None
    user_id: Optional[str] = None
    credits_used: Optional[int] = None 