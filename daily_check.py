#!/usr/bin/env python3
"""
Daily Version Check Script

This script runs daily to:
1. Check all pending submissions for version updates
2. Compare current versions with latest available versions
3. Send email notifications for outdated tools
4. Update the database with results

Usage:
    python daily_check.py

For automated execution, add to crontab:
    0 9 * * * /usr/bin/python3 /path/to/daily_check.py
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import schedule
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db
from version_checker import version_checker
from email_notifier import email_notifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/daily_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_single_submission(submission):
    """Check a single submission for version updates"""
    try:
        logger.info(f"Checking {submission['tool_name']} version {submission['current_version']} for {submission['email']}")
        
        # Get version source information
        source_info = db.get_version_source(submission['tool_name'])
        if not source_info:
            logger.warning(f"No version source configured for {submission['tool_name']}")
            return False
        
        # Fetch latest version
        latest_version = version_checker.get_latest_version(submission['tool_name'], source_info)
        if not latest_version:
            logger.error(f"Could not fetch latest version for {submission['tool_name']}")
            return False
        
        # Compare versions
        is_outdated = version_checker.compare_versions(submission['current_version'], latest_version)
        
        # Update database with results
        db.update_version_check(submission['id'], latest_version, is_outdated)
        
        logger.info(f"Version check complete: {submission['tool_name']} - Current: {submission['current_version']}, Latest: {latest_version}, Outdated: {is_outdated}")
        
        # Send notification if outdated and not already sent
        if is_outdated and not submission['notification_sent']:
            return send_notification(submission, latest_version)
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking submission {submission['id']}: {e}")
        return False

def send_notification(submission, latest_version):
    """Send email notification for outdated tool"""
    try:
        # Update submission with latest version for notification
        submission['latest_version'] = latest_version
        
        # Get upgrade instructions
        upgrade_info = version_checker.get_upgrade_instructions(
            submission['tool_name'], 
            submission['current_version'], 
            latest_version
        )
        
        # Send email notification
        success = email_notifier.send_notification(submission, upgrade_info)
        
        if success:
            # Mark notification as sent
            db.mark_notification_sent(submission['id'])
            logger.info(f"Notification sent successfully to {submission['email']} for {submission['tool_name']}")
        else:
            logger.error(f"Failed to send notification to {submission['email']} for {submission['tool_name']}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending notification for submission {submission['id']}: {e}")
        return False

def run_daily_check():
    """Main function to run daily version checks"""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"Starting daily version check at {start_time}")
    logger.info("=" * 60)
    
    try:
        # Get all submissions that need checking
        pending_submissions = db.get_pending_checks()
        logger.info(f"Found {len(pending_submissions)} submissions to check")
        
        if not pending_submissions:
            logger.info("No submissions need checking at this time")
            return
        
        # Statistics
        checked_count = 0
        outdated_count = 0
        notification_count = 0
        error_count = 0
        
        # Process each submission
        for submission in pending_submissions:
            try:
                success = check_single_submission(submission)
                if success:
                    checked_count += 1
                    
                    # Check if it's outdated after the check
                    updated_submissions = db.get_all_submissions()
                    updated_submission = next((s for s in updated_submissions if s['id'] == submission['id']), None)
                    
                    if updated_submission and updated_submission['is_outdated']:
                        outdated_count += 1
                        if updated_submission['notification_sent']:
                            notification_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Unexpected error processing submission {submission['id']}: {e}")
                error_count += 1
            
            # Small delay between checks to be respectful to external APIs
            time.sleep(1)
        
        # Log summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("Daily check summary:")
        logger.info(f"  • Duration: {duration}")
        logger.info(f"  • Submissions checked: {checked_count}")
        logger.info(f"  • Outdated tools found: {outdated_count}")
        logger.info(f"  • Notifications sent: {notification_count}")
        logger.info(f"  • Errors encountered: {error_count}")
        logger.info(f"Completed daily version check at {end_time}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Critical error in daily check: {e}")
        raise

def check_outdated_notifications():
    """Check for outdated submissions that haven't been notified yet"""
    try:
        outdated_submissions = db.get_outdated_submissions()
        logger.info(f"Found {len(outdated_submissions)} outdated submissions without notifications")
        
        notification_count = 0
        for submission in outdated_submissions:
            success = send_notification(submission, submission['latest_version'])
            if success:
                notification_count += 1
        
        logger.info(f"Sent {notification_count} additional notifications for previously outdated tools")
        
    except Exception as e:
        logger.error(f"Error checking outdated notifications: {e}")

def setup_scheduler():
    """Set up the scheduled tasks"""
    # Schedule daily check at 9:00 AM
    schedule.every().day.at("09:00").do(run_daily_check)
    
    # Schedule notification check every 4 hours for any missed notifications
    schedule.every(4).hours.do(check_outdated_notifications)
    
    logger.info("Scheduler configured:")
    logger.info("  • Daily version check: 9:00 AM")
    logger.info("  • Notification check: Every 4 hours")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'run':
            # Run check immediately
            run_daily_check()
        elif command == 'notify':
            # Check for missed notifications
            check_outdated_notifications()
        elif command == 'schedule':
            # Run as scheduled service
            setup_scheduler()
            logger.info("Starting scheduled service... Press Ctrl+C to stop")
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduled service stopped")
        elif command == 'test':
            # Test mode - check only first 3 submissions
            logger.info("Running in test mode - checking first 3 submissions only")
            pending_submissions = db.get_pending_checks()[:3]
            for submission in pending_submissions:
                check_single_submission(submission)
        else:
            print("Usage: python daily_check.py [run|notify|schedule|test]")
            print("  run      - Run version check immediately")
            print("  notify   - Check for missed notifications")
            print("  schedule - Run as scheduled service")
            print("  test     - Test mode (first 3 submissions only)")
    else:
        # Default behavior - run once
        run_daily_check()

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Initialize database
    db.init_database()
    
    # Run main function
    main()