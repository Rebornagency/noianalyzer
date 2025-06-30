import os
from uuid import uuid4
from typing import List, Dict, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask

from .models import JobResponse, JobInfo, JobStatus
from .stripe_integration import create_checkout_session, verify_webhook
from .pipeline_runner import run_noi_pipeline
from .storage import upload_report, generate_presigned_url
from .emailer import send_report_email
from .job_store import global_job_store as job_store

router = APIRouter(prefix="/pay-per-use", tags=["PayPerUse"])

# In-memory job store; for production use persistent DB/Redis
# jobs: Dict[str, JobInfo] = {}


@router.post("/jobs", response_model=JobResponse)
async def create_job(
    email: str = Form(...),
    files: List[UploadFile] = File(...),
    doc_types: Optional[List[str]] = Form(None),
):
    job_id = uuid4().hex
    # Save files to temp dir associated with job_id
    temp_dir = os.path.join("/tmp", f"noi_{job_id}")
    os.makedirs(temp_dir, exist_ok=True)
    file_paths: List[str] = []
    role_map: Dict[str, str] = {}
    for upload in files:
        file_path = os.path.join(temp_dir, upload.filename)
        with open(file_path, "wb") as f:
            f.write(await upload.read())

        if doc_types and len(doc_types) == len(files):
            role_map[file_path] = doc_types[files.index(upload)]
        else:
            # naive inference based on filename
            name_lower = upload.filename.lower()
            if "budget" in name_lower:
                role_map[file_path] = "current_month_budget"
            elif "prior" in name_lower and "year" in name_lower:
                role_map[file_path] = "prior_year_actuals"
            elif "prior" in name_lower:
                role_map[file_path] = "prior_month_actuals"
            else:
                role_map[file_path] = "current_month_actuals"

        file_paths.append(file_path)

    # Initialize job record
    job_store.save(JobInfo(job_id=job_id, status=JobStatus.pending))

    checkout_url = create_checkout_session(email=email, job_id=job_id)
    return JobResponse(job_id=job_id, checkout_url=checkout_url)


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = verify_webhook(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        job_id = session["metadata"].get("job_id")
        email = session["metadata"].get("email")
        if not job_id or job_store.get(job_id) is None:
            return JSONResponse(status_code=400, content={"error": "Unknown job_id"})
        # Kick off background processing
        def process_job():
            job_store.update(job_id, status=JobStatus.processing)
            temp_dir = os.path.join("/tmp", f"noi_{job_id}")
            file_paths = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir)]
            try:
                report_path = run_noi_pipeline(temp_dir)
                object_key = upload_report(report_path, job_id)
                presigned_url = generate_presigned_url(object_key)
                send_report_email(email, presigned_url)
                job_store.update(job_id, status=JobStatus.completed, report_url=presigned_url)
                # cleanup
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as exc:
                job_store.update(job_id, status=JobStatus.failed, error=str(exc))

        background = BackgroundTask(process_job)
        return JSONResponse(status_code=200, content={"received": True}, background=background)

    return JSONResponse(status_code=200, content={"received": True})


@router.get("/jobs/{job_id}", response_model=JobInfo)
async def get_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job 