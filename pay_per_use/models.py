from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class JobCreate(BaseModel):
    email: EmailStr

class JobResponse(BaseModel):
    job_id: str
    checkout_url: str

class JobInfo(BaseModel):
    job_id: str
    status: JobStatus
    report_url: Optional[str] = None
    error: Optional[str] = None 