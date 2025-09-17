import os
from uuid import uuid4
from typing import List, Dict, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.background import BackgroundTask

from .models import JobResponse, JobInfo, JobStatus, CreditPackage
from .stripe_integration import create_checkout_session, create_credit_checkout_session, verify_webhook
from .credit_service import credit_service
from .database import db_service
# Import the processing function for the NOI pipeline
from .pipeline_runner import run_noi_pipeline

from .storage import upload_report, generate_presigned_url
from .emailer import send_report_email
from .job_store import global_job_store as job_store

router = APIRouter(prefix="/pay-per-use", tags=["PayPerUse"])

# INITIALIZATION ENDPOINT
@router.post("/init")
async def initialize_system():
    """Initialize the credit system with default packages"""
    try:
        db_service.create_default_packages()
        return {"message": "System initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NEW CREDIT-BASED ENDPOINTS

@router.get("/credits/{email}")
async def get_user_credits(email: str, request: Request):
    """Get user's current credit balance and info"""
    try:
        # Get IP address and user agent for tracking
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Pass IP info when getting user data
        user = credit_service.get_user_by_email(email, ip_address or "", user_agent)
        dashboard_data = credit_service.get_user_dashboard_data(email)
        if not dashboard_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "email": email,
            "credits": dashboard_data["user"].credits,
            "total_purchased": dashboard_data["user"].total_credits_purchased,
            "total_used": dashboard_data["user"].total_credits_used,
            "free_trial_used": dashboard_data["user"].free_trial_used,
            "recent_transactions": [
                {
                    "type": tx.type.value,
                    "amount": tx.amount,
                    "description": tx.description,
                    "created_at": tx.created_at.isoformat()
                } for tx in dashboard_data["recent_transactions"]
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packages")
async def get_credit_packages():
    """Get available credit packages"""
    try:
        packages = credit_service.get_credit_packages()
        return [
            {
                "package_id": pkg.package_id,
                "name": pkg.name,
                "credits": pkg.credits,
                "price_cents": pkg.price_cents,
                "price_dollars": pkg.price_cents / 100,
                "description": pkg.description,
                "per_credit_cost": pkg.price_cents / pkg.credits / 100
            } for pkg in packages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/credits/purchase")
async def purchase_credits(
    request: Request,
    email: str = Form(...),
    package_id: str = Form(...)
):
    """Create checkout session for credit purchase"""
    try:
        # Get IP address for tracking
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Verify package exists
        package = db_service.get_package_by_id(package_id)
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Purchase request - Email: {email}, Package: {package_id}")
        logger.info(f"Package details: {package}")
        
        # Ensure the package has a valid Stripe price ID
        if not package.stripe_price_id:
            # Log environment variables for debugging
            env_vars = {
                "STRIPE_STARTER_PRICE_ID": os.getenv("STRIPE_STARTER_PRICE_ID", "NOT SET"),
                "STRIPE_PROFESSIONAL_PRICE_ID": os.getenv("STRIPE_PROFESSIONAL_PRICE_ID", "NOT SET"),
                "STRIPE_BUSINESS_PRICE_ID": os.getenv("STRIPE_BUSINESS_PRICE_ID", "NOT SET")
            }
            logger.error(f"Package {package.name} doesn't have a valid Stripe price ID. Environment variables: {env_vars}")
            raise HTTPException(
                status_code=500, 
                detail=f"Package {package.name} doesn't have a valid Stripe price ID. Check environment variables: STRIPE_STARTER_PRICE_ID, STRIPE_PROFESSIONAL_PRICE_ID, STRIPE_BUSINESS_PRICE_ID"
            )
        
        # Create or get user (this will track IP if it's a new user)
        user = credit_service.get_user_by_email(email, ip_address or "", user_agent)
        
        try:
            checkout_url = create_credit_checkout_session(email, package_id)
            return {"checkout_url": checkout_url, "package": package.name}
        except RuntimeError as e:
            # Handle Stripe configuration errors
            raise HTTPException(status_code=500, detail=f"Stripe integration error: {str(e)}")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs", response_model=JobResponse)
async def create_job(
    request: Request,
    email: str = Form(...),
    files: List[UploadFile] = File(...),
    doc_types: Optional[List[str]] = Form(None),
    use_credits: bool = Form(True)  # Default to credit-based system
):
    """Create analysis job - credit-based by default, legacy payment as fallback"""
    # Basic email validation to reject disposable / invalid addresses early
    from utils.email_utils import is_valid_email, is_disposable_email
    if not is_valid_email(email) or is_disposable_email(email):
        raise HTTPException(status_code=400, detail="Disposable or invalid email address not allowed")
    # Get IP address and user agent for abuse prevention
    ip_address = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")
    job_id = uuid4().hex
    
    # Save files to temp dir associated with job_id
    temp_dir = os.path.join("/tmp", f"noi_{job_id}")
    file_paths: List[str] = []
    role_map: Dict[str, str] = {}
    
    try:
        os.makedirs(temp_dir, exist_ok=True)
        for upload in files:
            if upload.filename is None:
                raise HTTPException(status_code=400, detail="File name is required")
                
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

        if use_credits:
            # NEW CREDIT-BASED FLOW
            # First get/create user with IP tracking - this handles abuse prevention
            user = credit_service.get_user_by_email(email, ip_address or "", user_agent)
            
            has_credits, current_credits, message = credit_service.check_user_credits(email)
            
            if has_credits:
                # User has credits - deduct and start processing immediately
                success, deduct_message = credit_service.use_credits_for_analysis(email, job_id)
                if success:
                    
                    # Initialize job record with user info
                    job_store.save(JobInfo(
                        job_id=job_id, 
                        status=JobStatus.processing,
                        user_id=user.user_id,
                        credits_used=credit_service.credits_per_analysis
                    ))
                    
                    # Start processing immediately
                    def process_job():
                        try:
                            report_path = run_noi_pipeline(temp_dir)
                            object_key = upload_report(report_path, job_id)
                            presigned_url = generate_presigned_url(object_key)
                            send_report_email(email, presigned_url)
                            job_store.update(job_id, status=JobStatus.completed, report_url=presigned_url)
                        except Exception as exc:
                            job_store.update(job_id, status=JobStatus.failed, error=str(exc))
                        finally:
                            # cleanup temp directory
                            import shutil
                            shutil.rmtree(temp_dir, ignore_errors=True)

                    background = BackgroundTask(process_job)
                    return JSONResponse(
                        status_code=200, 
                        content={
                            "job_id": job_id, 
                            "message": deduct_message,
                            "credits_deducted": credit_service.credits_per_analysis,
                            "status": "processing"
                        }, 
                        background=background
                    )
                else:
                    # Failed to deduct credits
                    raise HTTPException(status_code=400, detail=deduct_message)
            else:
                # Insufficient credits - return info for user to buy more
                packages = credit_service.get_credit_packages()
                return JSONResponse(
                    status_code=402,  # Payment Required
                    content={
                        "error": "insufficient_credits",
                        "message": message,
                        "current_credits": current_credits,
                        "needed_credits": credit_service.credits_per_analysis,
                        "available_packages": [
                            {
                                "package_id": pkg.package_id,
                                "name": pkg.name,
                                "credits": pkg.credits,
                                "price_dollars": pkg.price_cents / 100
                            } for pkg in packages
                        ]
                    }
                )
        else:
            # LEGACY PAYMENT FLOW
            job_store.save(JobInfo(job_id=job_id, status=JobStatus.pending))
            checkout_url = create_checkout_session(email=email, job_id=job_id)
            return JobResponse(job_id=job_id, checkout_url=checkout_url)
    except Exception as e:
        # Clean up temp directory on error
        if 'temp_dir' in locals() and temp_dir:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if sig_header is None:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
    try:
        event = verify_webhook(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        session_type = metadata.get("type", "legacy_payment")
        
        if session_type == "credit_purchase":
            # Handle credit purchase
            user_id = metadata.get("user_id")
            package_id = metadata.get("package_id")
            email = metadata.get("email")
            
            if not user_id or not package_id:
                return JSONResponse(status_code=400, content={"error": "Missing credit purchase metadata"})
            
            # Add credits to user account
            success = credit_service.add_credits_from_purchase(user_id, package_id, session["id"])
            if success:
                return JSONResponse(status_code=200, content={"received": True, "credits_added": True})
            else:
                return JSONResponse(status_code=500, content={"error": "Failed to add credits"})
                
        elif session_type == "legacy_payment":
            # Handle legacy direct payment
            job_id = metadata.get("job_id")
            email = metadata.get("email")
            
            if not job_id or job_store.get(job_id) is None:
                return JSONResponse(status_code=400, content={"error": "Unknown job_id"})
            
            # Kick off background processing for legacy payment
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
                except Exception as exc:
                    job_store.update(job_id, status=JobStatus.failed, error=str(exc))
                finally:
                    # cleanup temp directory
                    if 'temp_dir' in locals():
                        import shutil
                        shutil.rmtree(temp_dir, ignore_errors=True)

            background = BackgroundTask(process_job)
            return JSONResponse(status_code=200, content={"received": True}, background=background)

    return JSONResponse(status_code=200, content={"received": True})


@router.get("/jobs/{job_id}", response_model=JobInfo)
async def get_job(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ADMIN ENDPOINTS FOR ABUSE PREVENTION
@router.get("/admin/suspicious-ips")
async def get_suspicious_ips(min_trials: int = 3, admin_key: str = ""):
    """Get IP addresses with suspicious activity (admin only)"""
    # Simple admin authentication - in production use proper auth
    if admin_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        suspicious_ips = db_service.get_suspicious_ips(min_trials)
        return {"suspicious_ips": suspicious_ips}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/block-ip")
async def block_ip_address(
    ip_address: str = Form(...),
    reason: str = Form(...),
    admin_key: str = Form(...)
):
    """Block an IP address (admin only)"""
    # Simple admin authentication - in production use proper auth
    if admin_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        db_service.block_ip_address(ip_address, reason)
        return {"message": f"IP {ip_address} has been blocked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 