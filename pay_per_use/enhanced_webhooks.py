"""
Enhanced Webhook Handler with Retry Logic and Reliability Improvements
"""
import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .stripe_integration import verify_webhook
from .credit_service import credit_service
from .enhanced_database import enhanced_db_service

logger = logging.getLogger(__name__)

class EnhancedWebhookHandler:
    """Enhanced webhook handler with retry logic and reliability features"""
    
    def __init__(self):
        self.redis_client = self._init_redis() if REDIS_AVAILABLE else None
        self.max_retries = int(os.getenv("WEBHOOK_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("WEBHOOK_RETRY_DELAY", "60"))  # seconds
        
    def _init_redis(self):
        """Initialize Redis for job queue (if available)"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            client = redis.from_url(redis_url)
            client.ping()  # Test connection
            logger.info("Redis connected for webhook queue")
            return client
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            return None
    
    async def process_webhook(self, request: Request, background_tasks: BackgroundTasks):
        """Main webhook processing endpoint with enhanced reliability"""
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        try:
            # Verify webhook signature
            event = verify_webhook(payload, sig_header)
            event_type = event["type"]
            
            logger.info(f"Webhook received: {event_type}")
            
            if event_type == "checkout.session.completed":
                session = event["data"]["object"]
                session_id = session["id"]
                
                # Check for idempotency - prevent duplicate processing
                if enhanced_db_service.is_webhook_processed(session_id):
                    logger.info(f"Webhook already processed: {session_id}")
                    return JSONResponse(
                        status_code=200, 
                        content={"received": True, "status": "already_processed"}
                    )
                
                # Process webhook with retry logic
                if self.redis_client:
                    # Use Redis queue for background processing
                    background_tasks.add_task(self._process_webhook_async, session)
                else:
                    # Process immediately if no Redis
                    success = await self._process_checkout_session(session)
                    if success:
                        enhanced_db_service.mark_webhook_processed(session_id, "processed")
                    else:
                        enhanced_db_service.mark_webhook_processed(session_id, "failed")
                
                return JSONResponse(status_code=200, content={"received": True})
            
            else:
                logger.info(f"Unhandled webhook type: {event_type}")
                return JSONResponse(status_code=200, content={"received": True})
                
        except ValueError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _process_webhook_async(self, session: Dict[str, Any]):
        """Process webhook asynchronously with retry logic"""
        session_id = session["id"]
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                success = await self._process_checkout_session(session)
                
                if success:
                    enhanced_db_service.mark_webhook_processed(session_id, "processed")
                    logger.info(f"Webhook processed successfully: {session_id}")
                    return True
                else:
                    raise Exception("Checkout session processing failed")
                    
            except Exception as e:
                retry_count += 1
                error_msg = f"Webhook processing failed (attempt {retry_count}): {e}"
                logger.error(error_msg)
                
                enhanced_db_service.log_webhook_error(session_id, str(e), retry_count)
                
                if retry_count <= self.max_retries:
                    # Wait before retry (exponential backoff)
                    delay = self.retry_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying webhook in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # Max retries exceeded
                    enhanced_db_service.mark_webhook_processed(session_id, "failed")
                    logger.error(f"Webhook processing failed permanently: {session_id}")
                    
                    # Send alert to admin
                    await self._send_admin_alert(session, str(e))
                    return False
        
        return False
    
    async def _process_checkout_session(self, session: Dict[str, Any]) -> bool:
        """Process individual checkout session"""
        try:
            metadata = session.get("metadata", {})
            session_type = metadata.get("type", "legacy_payment")
            session_id = session["id"]
            
            if session_type == "credit_purchase":
                # Handle credit purchase
                user_id = metadata.get("user_id")
                package_id = metadata.get("package_id")
                email = metadata.get("email")
                
                if not user_id or not package_id:
                    logger.error(f"Missing credit purchase metadata: {metadata}")
                    return False
                
                # Add credits to user account
                success = credit_service.add_credits_from_purchase(user_id, package_id, session_id)
                
                if success:
                    logger.info(f"Credits added successfully: {package_id} to user {user_id}")
                    
                    # Log successful purchase
                    enhanced_db_service.log_admin_action(
                        user_id=user_id,
                        action="credit_purchase_completed",
                        details={
                            "package_id": package_id,
                            "stripe_session_id": session_id,
                            "email": email,
                            "amount_paid": session.get("amount_total", 0) / 100,  # Convert from cents
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    return True
                else:
                    logger.error(f"Failed to add credits for session: {session_id}")
                    return False
                    
            elif session_type == "legacy_payment":
                # Handle legacy direct payment (if still supported)
                logger.info(f"Processing legacy payment: {session_id}")
                # ... legacy processing logic
                return True
            
            else:
                logger.warning(f"Unknown session type: {session_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing checkout session: {e}")
            return False
    
    async def _send_admin_alert(self, session: Dict[str, Any], error: str):
        """Send alert to admin about failed webhook"""
        try:
            # This could be email, Slack, or other notification
            admin_email = os.getenv("ADMIN_EMAIL")
            if admin_email:
                # Send email alert
                alert_data = {
                    "session_id": session["id"],
                    "customer_email": session.get("customer_email"),
                    "amount": session.get("amount_total", 0) / 100,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.critical(f"ADMIN ALERT: Webhook failed permanently: {json.dumps(alert_data, indent=2)}")
                
                # TODO: Implement actual email sending
                # await send_admin_email("Webhook Processing Failed", alert_data)
                
        except Exception as e:
            logger.error(f"Failed to send admin alert: {e}")
    
    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook processing statistics"""
        try:
            conn = enhanced_db_service.get_connection()
            cursor = conn.cursor()
            
            # Get webhook stats for last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            cursor.execute('''
                SELECT 
                    status,
                    COUNT(*) as count,
                    AVG(retry_count) as avg_retries
                FROM webhook_log 
                WHERE processed_at > %s
                GROUP BY status
            ''', (thirty_days_ago,))
            
            stats = {}
            for row in cursor.fetchall():
                stats[row['status']] = {
                    'count': row['count'],
                    'avg_retries': float(row['avg_retries']) if row['avg_retries'] else 0
                }
            
            # Get recent failures
            cursor.execute('''
                SELECT stripe_session_id, last_error, retry_count, processed_at
                FROM webhook_log 
                WHERE status = 'failed' 
                ORDER BY processed_at DESC 
                LIMIT 10
            ''')
            
            recent_failures = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                "stats_by_status": stats,
                "recent_failures": recent_failures,
                "total_processed": sum(s['count'] for s in stats.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook stats: {e}")
            return {}
    
    async def retry_failed_webhook(self, session_id: str) -> bool:
        """Manually retry a failed webhook (admin function)"""
        try:
            # Get session details from Stripe
            import stripe
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Process the session
            success = await self._process_checkout_session(session)
            
            if success:
                enhanced_db_service.mark_webhook_processed(session_id, "processed")
                logger.info(f"Webhook manually retried successfully: {session_id}")
                return True
            else:
                logger.error(f"Manual webhook retry failed: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error manually retrying webhook: {e}")
            return False

# Create global webhook handler instance
webhook_handler = EnhancedWebhookHandler()

# Router for webhook endpoints
webhook_router = APIRouter(prefix="/stripe", tags=["Webhooks"])

@webhook_router.post("/webhook")
async def stripe_webhook_enhanced(request: Request, background_tasks: BackgroundTasks):
    """Enhanced Stripe webhook endpoint with reliability features"""
    return await webhook_handler.process_webhook(request, background_tasks)

@webhook_router.get("/webhook/stats")
async def webhook_stats(admin_key: str = ""):
    """Get webhook processing statistics (admin only)"""
    if admin_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return webhook_handler.get_webhook_stats()

@webhook_router.post("/webhook/retry/{session_id}")
async def retry_webhook(session_id: str, admin_key: str = ""):
    """Manually retry a failed webhook (admin only)"""
    if admin_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    success = await webhook_handler.retry_failed_webhook(session_id)
    
    if success:
        return {"message": f"Webhook {session_id} retried successfully"}
    else:
        raise HTTPException(status_code=500, detail="Webhook retry failed")