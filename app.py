from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database import db
from version_checker import version_checker
from email_notifier import email_notifier
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Common tools for the dropdown
COMMON_TOOLS = [
    'SQL Server',
    'Python',
    'Node.js',
    'Java',
    '.NET Framework',
    'Oracle Database',
    'MySQL',
    'PostgreSQL',
    'Visual Studio',
    'Docker',
    'Kubernetes',
    'Git',
    'Other'
]

@app.route('/')
def index():
    """Main page with submission form"""
    return render_template('index.html', tools=COMMON_TOOLS)

@app.route('/submit', methods=['POST'])
def submit_version():
    """Handle tool version submission"""
    try:
        tool_name = request.form.get('tool_name', '').strip()
        version = request.form.get('version', '').strip()
        email = request.form.get('email', '').strip()
        
        # Basic validation
        if not all([tool_name, version, email]):
            flash('All fields are required!', 'error')
            return redirect(url_for('index'))
        
        # Validate email format (basic)
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address!', 'error')
            return redirect(url_for('index'))
        
        # Add submission to database
        submission_id = db.add_submission(tool_name, version, email)
        
        flash(f'Successfully submitted {tool_name} version {version}! You will be notified if an update is available.', 'success')
        logger.info(f"New submission: {tool_name} {version} by {email}")
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Error submitting version: {e}")
        flash('An error occurred while submitting your information. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Dashboard showing all submissions and their status"""
    try:
        submissions = db.get_all_submissions()
        
        # Add status information
        for submission in submissions:
            if submission['last_checked']:
                if submission['is_outdated']:
                    submission['status'] = 'Outdated'
                    submission['status_class'] = 'status-outdated'
                else:
                    submission['status'] = 'Up to date'
                    submission['status_class'] = 'status-current'
            else:
                submission['status'] = 'Pending check'
                submission['status_class'] = 'status-pending'
        
        return render_template('dashboard.html', submissions=submissions)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('An error occurred while loading the dashboard.', 'error')
        return render_template('dashboard.html', submissions=[])

@app.route('/api/check-version', methods=['POST'])
def api_check_version():
    """API endpoint to manually trigger version check for a specific submission"""
    try:
        submission_id = request.json.get('submission_id')
        if not submission_id:
            return jsonify({'error': 'Submission ID required'}), 400
        
        # Get submission details
        submissions = db.get_all_submissions()
        submission = next((s for s in submissions if s['id'] == submission_id), None)
        
        if not submission:
            return jsonify({'error': 'Submission not found'}), 404
        
        # Get version source info
        source_info = db.get_version_source(submission['tool_name'])
        if not source_info:
            return jsonify({'error': 'No version source configured for this tool'}), 400
        
        # Check latest version
        latest_version = version_checker.get_latest_version(submission['tool_name'], source_info)
        if not latest_version:
            return jsonify({'error': 'Could not fetch latest version'}), 500
        
        # Compare versions
        is_outdated = version_checker.compare_versions(submission['current_version'], latest_version)
        
        # Update database
        db.update_version_check(submission_id, latest_version, is_outdated)
        
        return jsonify({
            'success': True,
            'latest_version': latest_version,
            'is_outdated': is_outdated,
            'current_version': submission['current_version']
        })
        
    except Exception as e:
        logger.error(f"Error in API version check: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/send-test-email', methods=['POST'])
def api_send_test_email():
    """API endpoint to send a test email"""
    try:
        email = request.json.get('email')
        if not email:
            return jsonify({'error': 'Email address required'}), 400
        
        success = email_notifier.send_test_email(email)
        
        if success:
            return jsonify({'success': True, 'message': 'Test email sent successfully'})
        else:
            return jsonify({'error': 'Failed to send test email'}), 500
            
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/admin')
def admin():
    """Admin page for system management"""
    try:
        # Get system statistics
        all_submissions = db.get_all_submissions()
        pending_checks = db.get_pending_checks()
        outdated_submissions = db.get_outdated_submissions()
        
        stats = {
            'total_submissions': len(all_submissions),
            'pending_checks': len(pending_checks),
            'outdated_tools': len(outdated_submissions),
            'up_to_date': len([s for s in all_submissions if s['last_checked'] and not s['is_outdated']])
        }
        
        return render_template('admin.html', stats=stats, submissions=all_submissions)
        
    except Exception as e:
        logger.error(f"Error loading admin page: {e}")
        flash('An error occurred while loading the admin page.', 'error')
        return render_template('admin.html', stats={}, submissions=[])

@app.route('/help')
def help_page():
    """Help page with documentation"""
    return render_template('help.html')

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Initialize database
    db.init_database()
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"""
    🚀 Tool Version Audit & Notification System Started!
    
    📝 Web Form: http://localhost:{port}
    📊 Dashboard: http://localhost:{port}/dashboard
    ⚙️  Admin Panel: http://localhost:{port}/admin
    ❓ Help: http://localhost:{port}/help
    
    Press Ctrl+C to stop the server.
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)