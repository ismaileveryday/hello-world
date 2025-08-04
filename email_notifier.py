import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self):
        # Email configuration - can be set via environment variables
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL', 'your-email@company.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', 'your-app-password')
        self.sender_name = os.getenv('SENDER_NAME', 'Tool Version Monitor')
    
    def create_email_template(self, submission: Dict, upgrade_info: Dict) -> str:
        """Create HTML email template for version update notification"""
        
        template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }}
                .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; 
                         border-radius: 4px; padding: 15px; margin: 15px 0; }}
                .version-info {{ background: white; padding: 15px; border-radius: 4px; 
                               border-left: 4px solid #667eea; margin: 15px 0; }}
                .upgrade-steps {{ background: white; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                .upgrade-steps ol {{ padding-left: 20px; }}
                .upgrade-steps li {{ margin: 8px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .button {{ background: #667eea; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }}
                .links {{ margin: 15px 0; }}
                .links a {{ color: #667eea; text-decoration: none; }}
                .links a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Tool Version Update Available</h1>
                    <p>Your {submission['tool_name']} version needs attention</p>
                </div>
                
                <div class="content">
                    <div class="alert">
                        <strong>⚠️ Version Update Required</strong><br>
                        Your current version of {submission['tool_name']} is outdated and should be updated.
                    </div>
                    
                    <div class="version-info">
                        <h3>📊 Version Comparison</h3>
                        <p><strong>Tool:</strong> {submission['tool_name']}</p>
                        <p><strong>Your Current Version:</strong> <span style="color: #e74c3c;">{submission['current_version']}</span></p>
                        <p><strong>Latest Available Version:</strong> <span style="color: #27ae60;">{submission['latest_version']}</span></p>
                        <p><strong>Submitted on:</strong> {submission['submitted_at']}</p>
                    </div>
                    
                    <div class="upgrade-steps">
                        <h3>🔧 Upgrade Instructions</h3>
                        <p><strong>What's New:</strong></p>
                        <p>{upgrade_info['version_improvements']}</p>
                        
                        <p><strong>Upgrade Steps:</strong></p>
                        <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace;">
                            {upgrade_info['upgrade_steps'].replace(chr(10), '<br>')}
                        </div>
                    </div>
                    
                    <div class="links">
                        <h3>📚 Documentation & Resources</h3>
                        <p>For detailed upgrade instructions, please refer to:</p>
                        <ul>
        """
        
        # Add documentation links
        for link in upgrade_info['documentation_links']:
            template += f'<li><a href="{link}" target="_blank">{link}</a></li>'
        
        template += f"""
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <p><strong>⏰ Action Required:</strong> Please update your {submission['tool_name']} 
                        to ensure security and compatibility.</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This notification was sent by the Tool Version Audit & Notification System</p>
                    <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>If you have questions, please contact your IT administrator.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return template
    
    def send_notification(self, submission: Dict, upgrade_info: Dict) -> bool:
        """Send email notification to user about outdated tool"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔔 {submission['tool_name']} Update Available - Version {submission['latest_version']}"
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = submission['email']
            
            # Create HTML content
            html_content = self.create_email_template(submission, upgrade_info)
            html_part = MIMEText(html_content, 'html')
            
            # Create plain text version
            text_content = f"""
Tool Version Update Notification

Tool: {submission['tool_name']}
Your Current Version: {submission['current_version']}
Latest Available Version: {submission['latest_version']}

What's New:
{upgrade_info['version_improvements']}

Upgrade Steps:
{upgrade_info['upgrade_steps']}

Documentation Links:
{chr(10).join(upgrade_info['documentation_links'])}

Please update your {submission['tool_name']} to ensure security and compatibility.

---
This notification was sent by the Tool Version Audit & Notification System
Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            text_part = MIMEText(text_content, 'plain')
            
            # Attach parts
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {submission['email']} for {submission['tool_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {submission['email']}: {e}")
            return False
    
    def send_test_email(self, recipient_email: str) -> bool:
        """Send a test email to verify email configuration"""
        try:
            msg = MIMEMultipart()
            msg['Subject'] = "Test Email - Tool Version Monitor"
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email
            
            body = """
            This is a test email from the Tool Version Audit & Notification System.
            
            If you received this email, the email configuration is working correctly.
            
            System Information:
            - SMTP Server: {}
            - SMTP Port: {}
            - Sender: {}
            
            Generated on: {}
            """.format(
                self.smtp_server,
                self.smtp_port,
                self.sender_email,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Test email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            return False

# Create global email notifier instance
email_notifier = EmailNotifier()