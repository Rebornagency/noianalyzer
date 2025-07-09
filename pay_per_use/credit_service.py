import os
import logging
from typing import Optional, Tuple, Dict, Any
from .database import db_service
from .models import User, TransactionType, CreditPackage
from uuid import uuid4

logger = logging.getLogger(__name__)

class CreditService:
    def __init__(self):
        self.credits_per_analysis = int(os.getenv("CREDITS_PER_ANALYSIS", "1"))
        self.free_trial_credits = int(os.getenv("FREE_TRIAL_CREDITS", "1"))
    
    def get_user_by_email(self, email: str, ip_address: str = None, user_agent: str = None) -> User:
        """Get or create user by email"""
        return db_service.get_or_create_user(email, ip_address, user_agent)
    
    def check_user_credits(self, email: str) -> Tuple[bool, int, str]:
        """
        Check if user has enough credits for analysis
        
        Returns:
            (has_enough_credits, current_credits, message)
        """
        try:
            user = self.get_user_by_email(email)
            has_enough = user.credits >= self.credits_per_analysis
            
            if has_enough:
                message = f"You have {user.credits} credits available"
            else:
                message = f"Insufficient credits. You have {user.credits} credits but need {self.credits_per_analysis}"
            
            return has_enough, user.credits, message
            
        except Exception as e:
            logger.error(f"Error checking credits for {email}: {e}")
            return False, 0, "Error checking credit balance"
    
    def use_credits_for_analysis(self, email: str, job_id: str) -> Tuple[bool, str]:
        """
        Deduct credits for analysis
        
        Returns:
            (success, message)
        """
        try:
            user = self.get_user_by_email(email)
            
            if user.credits < self.credits_per_analysis:
                return False, f"Insufficient credits. You have {user.credits} but need {self.credits_per_analysis}"
            
            # Deduct credits
            success = db_service.update_user_credits(
                user.user_id,
                -self.credits_per_analysis,
                TransactionType.usage,
                f"NOI Analysis (Job: {job_id})"
            )
            
            if success:
                remaining_credits = user.credits - self.credits_per_analysis
                message = f"Analysis started! {self.credits_per_analysis} credit(s) deducted. {remaining_credits} credits remaining."
                logger.info(f"Credits deducted for user {email}: {self.credits_per_analysis}")
                return True, message
            else:
                return False, "Failed to deduct credits. Please try again."
                
        except Exception as e:
            logger.error(f"Error using credits for {email}: {e}")
            return False, "Error processing credit usage"
    
    def get_user_dashboard_data(self, email: str) -> Dict[str, Any]:
        """Get user dashboard data"""
        try:
            user = self.get_user_by_email(email)
            transactions = db_service.get_user_transactions(user.user_id, limit=10)
            
            # Calculate savings from free trial
            free_trial_value = self.free_trial_credits * 5.00  # Assuming $5 per credit value
            
            dashboard_data = {
                "user": user,
                "recent_transactions": transactions,
                "free_trial_value": free_trial_value,
                "credits_per_analysis": self.credits_per_analysis,
                "is_new_user": user.total_credits_used == 0 and user.free_trial_used
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for {email}: {e}")
            return {}
    
    def add_credits_from_purchase(self, user_id: str, package_id: str, stripe_session_id: str) -> bool:
        """Add credits to user account from successful purchase"""
        try:
            package = db_service.get_package_by_id(package_id)
            if not package:
                logger.error(f"Package {package_id} not found")
                return False
            
            success = db_service.update_user_credits(
                user_id,
                package.credits,
                TransactionType.purchase,
                f"Purchased {package.name} ({package.credits} credits)",
                stripe_session_id
            )
            
            if success:
                logger.info(f"Added {package.credits} credits to user {user_id} from package {package_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding credits from purchase: {e}")
            return False
    
    def get_credit_packages(self) -> list[CreditPackage]:
        """Get available credit packages"""
        return db_service.get_active_packages()
    
    def refund_credits(self, user_id: str, amount: int, reason: str) -> bool:
        """Refund credits to user (admin function)"""
        try:
            success = db_service.update_user_credits(
                user_id,
                amount,
                TransactionType.refund,
                f"Credit refund: {reason}"
            )
            
            if success:
                logger.info(f"Refunded {amount} credits to user {user_id}: {reason}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error refunding credits: {e}")
            return False
    
    def get_pricing_display(self) -> Dict[str, Any]:
        """Get pricing information for display"""
        packages = self.get_credit_packages()
        
        # Calculate per-credit costs
        pricing_data = []
        for package in packages:
            per_credit_cost = package.price_cents / package.credits / 100  # Convert to dollars
            
            # Calculate discount compared to smallest package
            if packages:
                base_per_credit = packages[0].price_cents / packages[0].credits / 100
                discount_percent = ((base_per_credit - per_credit_cost) / base_per_credit) * 100
            else:
                discount_percent = 0
            
            pricing_data.append({
                "package": package,
                "per_credit_cost": per_credit_cost,
                "discount_percent": max(0, discount_percent),
                "total_analyses": package.credits // self.credits_per_analysis
            })
        
        return {
            "packages": pricing_data,
            "credits_per_analysis": self.credits_per_analysis,
            "free_trial_credits": self.free_trial_credits
        }

# Global credit service instance
credit_service = CreditService() 