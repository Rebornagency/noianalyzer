3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transactions (id, email, package_type, credits, amount, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_id, email, package_type, credits, amount, status))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error in log_transaction: {str(e)}")
            if conn:
                conn.close()
    
    def update_user_status(self, email, status):
        """Update user status"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First, ensure the status column exists
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            cursor.execute("UPDATE users SET status = ? WHERE email = ?", (status, email))
            rows_affected = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                return True, f"Status updated to {status}"
            else:
                return False, "User not found"
        except Exception as e:
            logger.error(f"Error in update_user_status: {str(e)}")
            if conn:
                conn.close()
            return False, str(e)

class CreditAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db = DatabaseManager()
        super().__init__(*args, **kwargs)
    
    def _send_json_response(self, data, status=200):
        """Send JSON response with CORS headers"""
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.end_headers()
        
            response = json.dumps(data)
            self.wfile.write(response.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error in _send_json_response: {str(e)}")
            # Try to send a basic error response
            try:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"error": "Failed to send response"}')
            except:
                pass

    def _send_error(self, message, status=400):
        """Send error response"""
        try:
            self._send_json_response({"error": message}, status)
        except Exception as e:
            logger.error(f"Error in _send_error: {str(e)}")
            # Try to send a basic error response
            try:
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(f'{{"error": "{message}"}}'.encode('utf-8'))
            except:
                pass
    
    def serve_docs(self):
        """Serve API documentation"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # Simple HTML documentation page
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>NOI Analyzer Credit API Documentation</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 1000px; margin: 0 auto; padding: 20px; background: #f8f9fa; }
                .container { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1, h2, h3 { color: #2c3e50; }
                h1 { border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                h2 { border-left: 4px solid #3498db; padding-left: 15px; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .endpoint { background: #f8f9fa; border-left: 4px solid #27ae60; padding: 15px; margin: 15px 0; border-radius: 0 4px 4px 0; }
                .method { background: #3498db; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.9em; }
                .url { font-family: 'Courier New', monospace; background: #eee; padding: 2px 6px; border-radius: 3px; }
                code { background: #f1f2f6; padding: 2px 4px; border-radius: 3px; }
                pre { background: #2c3e50; color: #fff; padding: 15px; border-radius: 5px; overflow-x: auto; }
                .note { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 0 4px 4px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>💳 NOI Analyzer Credit API</h1>
                <p>API for managing credits in the NOI Analyzer financial analysis tool.</p>
                
                <h2>📦 Credit Packages</h2>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/packages</span>
                    <p>Get available credit packages for purchase.</p>
                    <p><strong>Response:</strong> Array of package objects with id, name, credits, and price.</p>
                </div>
                
                <h2>👤 User Credits</h2>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/pay-per-use/credits/{email}</span>
                    <p>Get credit balance for a specific user.</p>
                    <p><strong>Response:</strong> Object with email and credit count.</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="url">/pay-per-use/use-credits</span>
                    <p>Deduct one credit for NOI analysis.</p>
                    <p><strong>Body:</strong> <code>{"email": "user@example.com"}</code></p>
                    <p><strong>Response:</strong> Success status and remaining credits.</p>
                </div>
                
                <h2>💰 Credit Purchase</h2>
                <div class="endpoint">
                    <span class="method">POST</span> <span class="url">/pay-per-use/credits/purchase</span>
                    <p>Create a Stripe checkout session for credit purchase.</p>
                    <p><strong>Body:</strong> <code>{"email": "user@example.com", "package_id": "professional"}</code></p>
                    <p><strong>Response:</strong> Checkout URL for payment.</p>
                </div>
                
                <h2>🛡️ Admin Endpoints</h2>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/pay-per-use/admin/users?admin_key=SECRET</span>
                    <p>Get all users (requires admin key).</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/pay-per-use/admin/transactions?admin_key=SECRET</span>
                    <p>Get all transactions (requires admin key).</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="url">/pay-per-use/admin/adjust-credits</span>
                    <p>Manually adjust user credits (requires admin key).</p>
                </div>
                
                <h2>🔧 Health & Info</h2>
                <div class="endpoint">
                    <span class="method">GET</span> <span class="url">/health</span>
                    <p>Health check endpoint.</p>
                </div>
                
                <div class="note">
                    <strong>Note:</strong> All POST requests should use <code>application/x-www-form-urlencoded</code> or <code>application/json</code> content type.
                </div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))
    
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query_params = parse_qs(parsed_path.query)
            
            # DEBUG ENDPOINT - Special endpoint to get detailed system information
            if path == '/debug-system-info':
                self.serve_debug_info()
                return
            
            # Serve Terms of Service page
            if path == '/terms-of-service':
                self.serve_terms_of_service()
                return
            
            # Serve Privacy Policy page
            if path == '/privacy-policy':
                self.serve_privacy_policy()
                return
                
            # Serve main API documentation
            if path == '/' or path == '/docs':
                self.serve_docs()
                return
            
            # Serve health check
            if path == '/health':
                self.serve_health()
                return
            
            # ADD MISSING ENDPOINT: Credit success page
            if path == '/credit-success':
                self.serve_credit_success(query_params)
                return
            
            # Serve credit packages
            if path == '/packages' or path == '/pay-per-use/packages':
                packages_list = []
                for package_id, package_info in CREDIT_PACKAGES.items():
                    # Calculate per credit cost
                    per_credit = package_info["price"] / 100 / package_info["credits"]
                    packages_list.append({
                        "package_id": package_id,
                        "name": package_info["name"],
                        "credits": package_info["credits"],
                        "price_cents": package_info["price"],
                        "price_dollars": package_info["price"] / 100,
                        "per_credit_cost": per_credit,
                        "description": f"Top up {package_info['credits']} credits"
                    })
                self._send_json_response(packages_list)
                return
            
            # Serve user credits - NEW ENDPOINT IMPLEMENTATION
            if path.startswith('/pay-per-use/credits/'):
                # Extract email from path
                email = path.split('/pay-per-use/credits/')[-1]
                if not email:
                    self._send_error("Email required")
                    return
                credits = self.db.get_credits(email)
                self._send_json_response({"email": email, "credits": credits, "recent_transactions": []})
                return
            
            # Serve user credits (old endpoint)
            if path == '/credits':
                email = query_params.get('email', [None])[0]
                if not email:
                    self._send_error("Email parameter required")
                    return
                credits = self.db.get_credits(email)
                self._send_json_response({"email": email, "credits": credits})
                return
            
            # ADMIN GET ENDPOINTS
            if path.startswith('/pay-per-use/admin/'):
                try:
                    # Check admin authentication
                    admin_key = query_params.get('admin_key', [None])[0]
                    if not admin_key or not self.db.verify_admin_key(admin_key):
                        self._send_json_response({"error": "Unauthorized"}, 403)
                        return
                        
                    # Get all users
                    if path == '/pay-per-use/admin/users':
                        users = self.db.get_all_users()
                        self._send_json_response({"users": users})
                        return
                        
                    # Get all transactions
                    elif path == '/pay-per-use/admin/transactions':
                        transactions = self.db.get_all_transactions()
                        self._send_json_response({"transactions": transactions})
                        return
                        
                    # Get system stats
                    elif path == '/pay-per-use/admin/stats':
                        stats = self.db.get_system_stats()
                        self._send_json_response({"stats": stats})
                        return
                        
                    # Get user details
                    elif path.startswith('/pay-per-use/admin/user/'):
                        email = path.split('/pay-per-use/admin/user/')[-1]
                        if not email:
                            self._send_json_response({"error": "Email required"}, 400)
                            return
                            
                        user_details = self.db.get_user_details(email)
                        if not user_details:
                            self._send_json_response({"error": "User not found"}, 404)
                            return
                            
                        self._send_json_response(user_details)
                        return
                except Exception as e:
                    logger.error(f"Error in admin GET endpoints: {str(e)}")
                    self._send_json_response({"error": f"Internal server error: {str(e)}"}, 500)
                    return
            
            # If no endpoint matched, return 404
            self._send_error("Endpoint not found", 404)
        except Exception as e:
            logger.error(f"Error in do_GET: {str(e)}")
            self._send_json_response({"error": f"Internal server error: {str(e)}"}, 500)
    
    def do_POST(self):
        """Handle POST requests for credit operations"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            if path == "/deduct-credit":
                # For NOI analysis usage
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    email = data.get('email')
                    if not email:
                        self._send_json_response({"error": "Email required"}, 400)
                        return
                    
                    success = self.db.deduct_credits(email, 1)
                    if success:
                        remaining_credits = self.db.get_credits(email)
                        self._send_json_response({
                            "success": True,
                            "message": "Credit deducted for NOI analysis",
                            "remaining_credits": remaining_credits
                        })
                    else:
                        self._send_json_response({
                            "success": False,
                            "error": "Insufficient credits",
                            "remaining_credits": 0
                        }, 402)
                        
                except Exception as e:
                    self._send_json_response({"error": f"Invalid request: {str(e)}"}, 400)
                    
            elif path == "/pay-per-use/use-credits":
                # Main website expects this endpoint
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    
                    # Handle both JSON and form data
                    if 'application/json' in self.headers.get('Content-Type', ''):
                        data = json.loads(post_data.decode('utf-8'))
                    else:
                        # Parse form data
                        from urllib.parse import parse_qs
                        parsed_data = parse_qs(post_data.decode('utf-8'))
                        data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed_data.items()}
                    
                    email = data.get('email')
                    if not email:
                        self._send_json_response({"error": "Email required"}, 400)
                        return
                    
                    success = self.db.deduct_credits(email, 1)
                    if success:
                        remaining_credits = self.db.get_credits(email)
                        self._send_json_response({
                            "success": True,
                            "message": "Credit deducted for NOI analysis",
                            "credits_remaining": remaining_credits,
                            "analysis_id": data.get('analysis_id', 'unknown')
                        })
                    else:
                        self._send_json_response({
                            "success": False,
                            "error": "Insufficient credits",
                            "credits_remaining": 0
                        }, 402)
                        
                except Exception as e:
                    self._send_json_response({"error": f"Invalid request: {str(e)}"}, 400)
                    
            elif path == "/pay-per-use/credits/purchase":
                # Credit purchase endpoint - now with proper Stripe integration
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    
                    # Handle both JSON and form data (like the /pay-per-use/use-credits endpoint)
                    if 'application/json' in self.headers.get('Content-Type', ''):
                        data = json.loads(post_data.decode('utf-8'))
                    else:
                        # Parse form data
                        from urllib.parse import parse_qs
                        parsed_data = parse_qs(post_data.decode('utf-8'))
                        # Convert lists to single values
                        data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed_data.items()}
                    
                    # Extract email and package_id, ensuring they are strings
                    email = data.get('email')
                    package_id = data.get('package_id')
                    
                    # Handle case where email or package_id might be a list
                    if isinstance(email, list):
                        email = email[0] if email else ""
                    if isinstance(package_id, list):
                        package_id = package_id[0] if package_id else ""
                    
                    if not email or not package_id:
                        self._send_json_response({"error": "Email and package_id required"}, 400)
                        return
                    
                    if package_id not in CREDIT_PACKAGES:
                        self._send_json_response({"error": "Invalid package_id"}, 400)
                        return
                    
                    # Debug information
                    logger.info(f"🔍 Purchase request - Email: {email}, Package: {package_id}")
                    logger.info(f"   STRIPE_AVAILABLE: {STRIPE_AVAILABLE}")
                    # Check if stripe is available and has api_key attribute
                    stripe_api_key_set = False
                    try:
                        import stripe as stripe_module
                        if hasattr(stripe_module, 'api_key'):
                            stripe_api_key_set = bool(stripe_module.api_key)
                    except:
                        pass
                    logger.info(f"   stripe.api_key set: {stripe_api_key_set}")
                    
                    # Check if Stripe is available and properly configured
                    if STRIPE_AVAILABLE and stripe_api_key_set:
                        # Get the appropriate Stripe price ID directly from environment variables
                        env_var_name = STRIPE_PRICE_ID_ENV_MAP.get(package_id)
                        stripe_price_id = os.getenv(env_var_name) if env_var_name else None
                        
                        logger.info(f"   Environment variable name: {env_var_name}")
                        logger.info(f"   Stripe price ID from env: {stripe_price_id}")
                        
                        if not stripe_price_id:
                            self._send_json_response({
                                "error": "Stripe price ID not configured for this package",
                                "message": "Missing Stripe configuration - contact administrator",
                                "package": CREDIT_PACKAGES[package_id],
                                "debug": {
                                    "env_var_name": env_var_name,
                                    "env_var_value": os.getenv(env_var_name) if env_var_name else None
                                }
                            }, 500)
                            return
                        
                        # Build success URL with email parameter
                        base_success_url = os.getenv("CREDIT_SUCCESS_URL")
                        
                        # Ensure email is a string for quote function
                        email_str = str(email) if email else ""
                        
                        if base_success_url:
                            # If environment variable is set, use it but ensure email is included
                            if "email=" not in base_success_url and "{email}" not in base_success_url:
                                separator = "&" if "?" in base_success_url else "?"
                                success_url_with_email = f"{base_success_url}{separator}email={quote(email_str)}"
                            elif "{email}" in base_success_url:
                                # Replace {email} placeholder with actual email
                                success_url_with_email = base_success_url.replace("{email}", quote(email_str))
                            else:
                                success_url_with_email = base_success_url
                        else:
                            # Default URL with both session_id and email
                            success_url_with_email = f"https://noianalyzer-1.onrender.com/credit-success?session_id={{CHECKOUT_SESSION_ID}}&email={quote(email_str)}"
                        
                        # Create Stripe checkout session
                        try:
                            logger.info(f"   Creating Stripe session for price ID: {stripe_price_id}")
                            # Check if stripe module is available before using it
                            import stripe as stripe_module
                            session = stripe_module.checkout.Session.create(
                                payment_method_types=["card"],
                                mode="payment",
                                customer_email=email_str,
                                line_items=[{"price": stripe_price_id, "quantity": 1}],
                                success_url=success_url_with_email,
                                cancel_url=os.getenv("CREDIT_CANCEL_URL", "https://noianalyzer-1.onrender.com/payment-cancel"),
                                metadata={
                                    "type": "credit_purchase",
                                    "package_id": package_id,
                                    "email": email_str
                                },
                            )
                            
                            # Return the checkout URL
                            self._send_json_response({
                                "checkout_url": session.url,
                                "package": CREDIT_PACKAGES[package_id]
                            })
                        except Exception as e:
                            # Handle both Stripe errors and general exceptions
                            logger.error(f"❌ Error creating Stripe session: {str(e)}")
                            # Check if it's a Stripe error
                            try:
                                import stripe as stripe_module
                                if hasattr(e, 'code'):
                                    self._send_json_response({
                                        "error": "Stripe error",
                                        "message": str(e),
                                        "package": CREDIT_PACKAGES[package_id]
                                    }, 500)
                                else:
                                    self._send_json_response({
                                        "error": "Failed to create Stripe checkout session",
                                        "message": str(e),
                                        "package": CREDIT_PACKAGES[package_id]
                                    }, 500)
                            except:
                                self._send_json_response({
                                    "error": "Failed to create Stripe checkout session",
                                    "message": str(e),
                                    "package": CREDIT_PACKAGES[package_id]
                                }, 500)
                    else:
                        # Stripe not available - return placeholder response with clear instructions
                        package_info = CREDIT_PACKAGES[package_id]
                        # Check if stripe is available and has api_key attribute for debug info
                        stripe_api_key_set_debug = False
                        try:
                            import stripe as stripe_module
                            if hasattr(stripe_module, 'api_key'):
                                stripe_api_key_set_debug = bool(stripe_module.api_key)
                        except:
                            pass
                        self._send_json_response({
                            "message": "Credit purchase endpoint ready",
                            "package": package_info,
                            "next_step": "Set up Stripe integration for real payments",
                            "checkout_url": None,
                            "debug": {
                                "STRIPE_AVAILABLE": STRIPE_AVAILABLE,
                                "stripe_api_key_set": stripe_api_key_set_debug,
                                "required_env_vars": {
                                    "STRIPE_SECRET_KEY": bool(os.getenv("STRIPE_SECRET_KEY")),
                                    "STRIPE_STARTER_PRICE_ID": bool(os.getenv("STRIPE_STARTER_PRICE_ID")),
                                    "STRIPE_PROFESSIONAL_PRICE_ID": bool(os.getenv("STRIPE_PROFESSIONAL_PRICE_ID")),
                                    "STRIPE_BUSINESS_PRICE_ID": bool(os.getenv("STRIPE_BUSINESS_PRICE_ID"))
                                }
                            },
                            "setup_instructions": [
                                "1. Create a Stripe account at https://stripe.com",
                                "2. Create products in Stripe Dashboard for each credit package",
                                "3. Copy the price IDs from each product",
                                "4. Set STRIPE_SECRET_KEY and STRIPE_*_PRICE_ID environment variables",
                                "5. Restart the server"
                            ]
                        })
                    
                except Exception as e:
                    self._send_json_response({"error": f"Invalid request: {str(e)}"}, 400)
        
            # ADD MISSING ENDPOINT: Stripe webhook handler
            elif path == "/pay-per-use/stripe/webhook":
                self.handle_stripe_webhook()
                return
                
            # ADMIN POST ENDPOINTS
            elif path.startswith("/pay-per-use/admin/"):
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    
                    # Parse form data
                    from urllib.parse import parse_qs
                    parsed_data = parse_qs(post_data.decode('utf-8'))
                    # Convert lists to single values
                    data = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in parsed_data.items()}
                    
                    # Check admin authentication
                    admin_key = data.get('admin_key')
                    # Handle case where admin_key might be a list
                    if isinstance(admin_key, list):
                        admin_key = admin_key[0] if admin_key else ""
                    
                    if not self.db.verify_admin_key(admin_key):
                        self._send_json_response({"error": "Unauthorized"}, 403)
                        return
                    
                    if path == "/pay-per-use/admin/adjust-credits":
                        email = data.get('email')
                        credit_change = data.get('credit_change')
                        reason = data.get('reason')
                        
                        # Handle case where these might be lists
                        if isinstance(email, list):
                            email = email[0] if email else ""
                        if isinstance(credit_change, list):
                            credit_change = credit_change[0] if credit_change else ""
                        if isinstance(reason, list):
                            reason = reason[0] if reason else ""
                        
                        if not email or not reason or credit_change is None:
                            self._send_json_response({"error": "Email, credit_change, and reason are required"}, 400)
                            return
                        
                        try:
                            # Ensure credit_change is an integer
                            if isinstance(credit_change, str):
                                credit_change = int(credit_change)
                            else:
                                credit_change = int(credit_change)
                        except ValueError:
                            self._send_json_response({"error": "credit_change must be a number"}, 400)
                            return
                        
                        if credit_change == 0:
                            self._send_json_response({"error": "Credit change cannot be zero"}, 400)
                            return
                        
                        success, result = self.db.admin_adjust_credits(email, credit_change, reason)
                        
                        if success:
                            self._send_json_response({
                                "success": True,
                                "message": f"Credits adjusted for {email}",
                                "credit_change": credit_change,
                                "new_balance": result,
                                "reason": reason
                            })
                        else:
                            self._send_json_response({"error": f"Failed to adjust credits: {result}"}, 400)
                    
                    elif path == "/pay-per-use/admin/user-status":
                        email = data.get('email')
                        status = data.get('status')
                        
                        # Handle case where these might be lists
                        if isinstance(email, list):
                            email = email[0] if email else ""
                        if isinstance(status, list):
                            status = status[0] if status else ""
                        
                        if not email or not status:
                            self._send_json_response({"error": "Email and status are required"}, 400)
                            return
                        
                        # Update user status in the database
                        success, message = self.db.update_user_status(email, status)
                        
                        if success:
                            self._send_json_response({
                                "success": True,
                                "message": message,
                                "email": email,
                                "status": status
                            })
                        else:
                            self._send_json_response({"error": message}, 400)
                    
                    else:
                        self._send_json_response({"error": "Admin endpoint not found"}, 404)
                
                except Exception as e:
                    self._send_json_response({"error": f"Invalid request: {str(e)}"}, 400)
            
            else:
                self._send_json_response({"error": "Endpoint not found"}, 404)
        except Exception as e:
            logger.error(f"Error in do_POST: {str(e)}")
            self._send_json_response({"error": f"Internal server error: {str(e)}"}, 500)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.end_headers()

    def serve_health(self):
        """Serve health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "NOI Analyzer Credit API"
        }
        self.wfile.write(json.dumps(health_data).encode())
    
    def serve_credit_success(self, query_params):
        """Credit purchase success page"""
        # Extract parameters from query
        session_id = query_params.get('session_id', [None])[0]
        email = query_params.get('email', [None])[0]
        
        # Get main app URL from environment or use default
        main_app_url = os.getenv("MAIN_APP_URL", "https://noianalyzer.streamlit.app")
        
        # Handle email parameter properly - avoid None string
        email_param = email if email and email.lower() != 'none' else ""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html_content = f"""
        <html>
            <head>
                <title>Credits Purchase Successful</title>
                <meta charset='utf-8'/>
                <style>
                    body {{
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 2rem;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .card {{
                        background: white; 
                        color: #333;
                        border-radius: 12px; 
                        padding: 3rem 2rem; 
                        max-width: 500px; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                        animation: slideIn 0.5s ease-out;
                    }} 
                    @keyframes slideIn {{
                        from {{ opacity: 0; transform: translateY(20px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                    h1 {{ color: #28a745; margin-bottom: 1rem; font-size: 2rem; }}
                    .success-icon {{ font-size: 4rem; margin-bottom: 1rem; }}
                    p {{ color: #666666; line-height: 1.6; margin-bottom: 1rem; }}
                    .session-id {{ font-family: monospace; font-size: 0.9rem; color: #666666; }}
                    .action-btn {{
                        background: #28a745;
                        color: white;
                        padding: 12px 24px;
                        border: none;
                        border-radius: 6px;
                        font-size: 1rem;
                        cursor: pointer;
                        text-decoration: none;
                        display: inline-block;
                        margin: 0.5rem;
                        transition: background 0.3s;
                    }}
                    .action-btn:hover {{ background: #218838; }}
                    .secondary-btn {{
                        background: #6c757d;
                        color: white;
                        padding: 8px 16px;
                        border: none;
                        border-radius: 4px;
                        font-size: 0.9rem;
                        cursor: pointer;
                        text-decoration: none;
                        display: inline-block;
                        margin: 0.25rem;
                    }}
                </style>
            </head>
            <body>
                <div class='card'>
                    <div class='success-icon'>🎉</div>
                    <h1>Credits Purchase Successful!</h1>
                    <p><strong>Thank you for your purchase!</strong></p>
                    <p>Your credits have been added to your account and are ready to use for NOI analysis.</p>
                    
                    <div style="margin: 2rem 0;">
                        <a href="#" onclick="closeAndReturn()" class="action-btn">Return to NOI Analyzer</a>
                    </div>
                    
                    <p style="font-size: 0.9rem; color: #666666;">
                        You can now close this tab and continue using the NOI Analyzer app.
                        Your credit balance should update automatically.
                    </p>
                </div>
                
                <script>
                    function closeAndReturn() {{
                        // First try to communicate with parent window if it exists
                        if (window.opener) {{
                            try {{
                                window.opener.postMessage({{
                                    type: 'CREDIT_PURCHASE_SUCCESS',
                                    action: 'RETURN_TO_MAIN'
                                }}, '*');
                                window.opener.focus();
                                // Close this window after messaging parent
                                setTimeout(function() {{ window.close(); }}, 1000);
                                return;
                            }} catch(e) {{
                                console.log('Could not message parent window:', e);
                            }}
                        }}
                        
                        // If no parent window or messaging failed, redirect to main app
                        console.log('Redirecting to main app: {main_app_url}');
                        const emailParam = '{email_param}' ? '&email={email_param}' : '';
                        window.location.href = '{main_app_url}?credit_success=1&return_to_main=1' + emailParam;
                    }}
                    
                    // Auto-redirect after 3 seconds (reduced from 5)
                    setTimeout(function() {{
                        closeAndReturn();
                    }}, 3000);
                    
                    // Also try immediate redirect if user doesn't click button
                    setTimeout(function() {{
                        if (document.visibilityState === 'visible') {{
                            console.log('Page still visible, attempting redirect...');
                            const emailParam = '{email_param}' ? '&email={email_param}' : '';
                            window.location.href = '{main_app_url}?credit_success=1&return_to_main=1' + emailParam;
                        }}
                    }}, 8000);
                </script>
            </body>
        </html>
        """
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_terms_of_service(self):
        """Serve Terms of Service page"""
        try:
            with open('TERMS_OF_SERVICE.md', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert markdown to HTML (basic conversion)
            html_content = self.markdown_to_html(content)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_page = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Terms of Service - NOI Analyzer</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    a {{ color: #3498db; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    .container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    code {{ background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
                    pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    {html_content}
                </div>
            </body>
            </html>
            """
            self.wfile.write(html_page.encode('utf-8'))
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Terms of Service Not Found</h1>")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error loading Terms of Service</h1><p>{str(e)}</p>".encode())

    def serve_privacy_policy(self):
        """Serve Privacy Policy page"""
        try:
            with open('PRIVACY_POLICY.md', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert markdown to HTML (basic conversion)
            html_content = self.markdown_to_html(content)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_page = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Privacy Policy - NOI Analyzer</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    a {{ color: #3498db; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    .container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    code {{ background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
                    pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <div class="container">
                    {html_content}
                </div>
            </body>
            </html>
            """
            self.wfile.write(html_page.encode('utf-8'))
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Privacy Policy Not Found</h1>")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error loading Privacy Policy</h1><p>{str(e)}</p>".encode())
    
    def serve_debug_info(self):
        """Serve detailed system information for debugging"""
        import subprocess
        import sys
        
        debug_data = {
            "timestamp": time.time(),
            "platform": "Render" if os.getenv('RENDER') else "Local",
            "python_version": sys.version,
            "python_executable": sys.executable,
            "current_directory": os.getcwd(),
            "directory_contents": [],
            "environment_variables": {},
            "requirements_file": {},
            "installed_packages": [],
            "stripe_status": {
                "import_success": False,
                "import_error": None,
                "version": None,
                "api_key_set": False
            }
        }
        
        # Get directory contents
        try:
            debug_data["directory_contents"] = os.listdir('.')
        except Exception as e:
            debug_data["directory_contents"] = f"Error: {str(e)}"
        
        # Get environment variables (filtered for security)
        sensitive_vars = ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET']
        for key, value in os.environ.items():
            if key in sensitive_vars:
                # Mask sensitive values
                masked = f"{value[:3]}...{value[-4:]}" if len(value) > 7 else "Too short"
                debug_data["environment_variables"][key] = masked
            else:
                debug_data["environment_variables"][key] = value
        
        # Check requirements file
        if os.path.exists('requirements-api.txt'):
            try:
                with open('requirements-api.txt', 'r') as f:
                    content = f.read()
                    debug_data["requirements_file"] = {
                        "status": "found",
                        "lines": content.split('\n'),
                        "stripe_line": [line for line in content.split('\n') if 'stripe' in line.lower() and not line.startswith('#')]
                    }
            except Exception as e:
                debug_data["requirements_file"] = {"status": "error", "message": str(e)}
        else:
            debug_data["requirements_file"] = {"status": "missing"}
        
        # Get installed packages
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                debug_data["installed_packages"] = result.stdout.split('\n')
            else:
                debug_data["installed_packages"] = f"Error: {result.stderr}"
        except Exception as e:
            debug_data["installed_packages"] = f"Error: {str(e)}"
        
        # Check Stripe specifically
        try:
            import stripe
            debug_data["stripe_status"]["import_success"] = True
            debug_data["stripe_status"]["version"] = getattr(stripe, 'VERSION', 'Unknown')
            
            # Check if API key can be set
            stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
            if stripe_key:
                stripe.api_key = stripe_key
                debug_data["stripe_status"]["api_key_set"] = True
        except ImportError as e:
            debug_data["stripe_status"]["import_error"] = str(e)
        except Exception as e:
            debug_data["stripe_status"]["import_error"] = f"Other error: {str(e)}"
        
        self._send_json_response(debug_data)
    
    def markdown_to_html(self, markdown_text):
        """Convert basic markdown to HTML"""
        import re
        
        # Convert headers
        markdown_text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', markdown_text, flags=re.MULTILINE)
        
        # Convert bold and italic
        markdown_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', markdown_text)
        markdown_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', markdown_text)
        
        # Convert lists
        markdown_text = re.sub(r'^- (.*?)$', r'<li>\1</li>', markdown_text, flags=re.MULTILINE)
        markdown_text = re.sub(r'(<li>.*?</li>\n)+', r'<ul>\n\g<0></ul>\n', markdown_text)
        
        # Convert links
        markdown_text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', markdown_text)
        
        # Convert paragraphs
        paragraphs = markdown_text.split('\n\n')
        html_paragraphs = []
        for p in paragraphs:
            if not p.startswith('<'):
                p = f'<p>{p}</p>'
            html_paragraphs.append(p)
        
        return '\n'.join(html_paragraphs)

    def handle_stripe_webhook(self):
        """Handle Stripe webhooks for credit purchases only"""
        logger.info("🎯 WEBHOOK RECEIVED - Processing Stripe webhook")
        
        try:
            # Read the payload
            content_length = int(self.headers.get('Content-Length', 0))
            payload = self.rfile.read(content_length)
            
            # Get the signature header
            sig_header = self.headers.get('Stripe-Signature')
            
            logger.info(f"Webhook payload size: {len(payload)} bytes")
            logger.info(f"Stripe signature header present: {bool(sig_header)}")
            
            # Verify webhook signature if secret is available
            webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
            
            if webhook_secret and sig_header:
                try:
                    # For now, we'll just log that we received the webhook
                    # In a production environment, you would verify the signature
                    logger.info("✅ Webhook signature verification would happen here (simplified for HTTP server)")
                except Exception as e:
                    logger.error(f"❌ Webhook verification failed: {e}")
                    self._send_json_response({"error": "Webhook verification failed"}, 400)
                    return
            elif webhook_secret:
                logger.warning("⚠️  Webhook secret configured but no signature header received")
            
            # Parse the event
            try:
                event = json.loads(payload)
                event_type = event.get("type", "unknown")
                logger.info(f"✅ Webhook parsed successfully - Event type: {event_type}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse webhook payload: {e}")
                self._send_json_response({"error": "Invalid JSON payload"}, 400)
                return
            
            # Process the event
            if event_type == "checkout.session.completed":
                logger.info("💳 Processing checkout.session.completed event")
                session = event.get("data", {}).get("object", {})
                metadata = session.get("metadata", {})
                session_type = metadata.get("type", "credit_purchase")
                
                logger.info(f"Session metadata: {metadata}")
                
                if session_type == "credit_purchase":
                    # Handle credit purchase
                    user_id = metadata.get("user_id")  # This might not be available in simple version
                    package_id = metadata.get("package_id")
                    email = metadata.get("email")
                    
                    logger.info(f"Credit purchase - user_id: {user_id}, package_id: {package_id}, email: {email}")
                    
                    # For the simple version, we'll use email as the identifier
                    if not email or not package_id:
                        logger.error(f"❌ Missing metadata - email: {email}, package_id: {package_id}")
                        self._send_json_response({"error": "Missing credit purchase metadata"}, 400)
                        return
                    
                    # Add credits to user account
                    if package_id in CREDIT_PACKAGES:
                        credits_to_add = CREDIT_PACKAGES[package_id]["credits"]
                        logger.info(f"🏦 Adding {credits_to_add} credits to user {email}")
                        
                        # Add credits to user's account
                        self.db.add_credits(email, credits_to_add)
                        
                        # Log the transaction
                        transaction_id = str(uuid.uuid4())
                        self.db.log_transaction(transaction_id, email, package_id, credits_to_add, 
                                              CREDIT_PACKAGES[package_id]["price"], "completed")
                        
                        logger.info(f"✅ Credits successfully added to user {email}")
                        self._send_json_response({"received": True, "credits_added": True})
                        return
                    else:
                        logger.error(f"❌ Invalid package_id: {package_id}")
                        self._send_json_response({"error": "Invalid package_id"}, 400)
                        return
            else:
                logger.info(f"ℹ️ Received webhook event type: {event_type} (not processed)")
            
            # Send success response
            self._send_json_response({"received": True})
            
        except Exception as e:
            logger.error(f"❌ Error processing webhook: {e}")
            self._send_json_response({"error": f"Error processing webhook: {str(e)}"}, 500)

def run_server():
    """Run the HTTP server"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), CreditAPIHandler)
    logger.info(f"🚀 Starting Credit API server on port {port}")
    logger.info(f"   - Health check: http://localhost:{port}/health")
    logger.info(f"   - Packages: http://localhost:{port}/packages")
    logger.info(f"   - Credits: http://localhost:{port}/credits?email=test@example.com")
    logger.info("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    run_server()