#!/usr/bin/env python3
"""
Debug version of the Tool Version Audit & Notification System
This version includes detailed logging to help troubleshoot issues
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database import db
from version_checker import version_checker
from email_notifier import email_notifier
import logging
from datetime import datetime
import os
import traceback

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'debug-secret-key')

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
    logger.info("Index page accessed")
    return render_template('index.html', tools=COMMON_TOOLS)

@app.route('/submit', methods=['POST'])
def submit_version():
    """Handle tool version submission with detailed debugging"""
    logger.info("=== FORM SUBMISSION DEBUG ===")
    
    try:
        # Log all form data
        logger.info(f"Form method: {request.method}")
        logger.info(f"Form data: {dict(request.form)}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Get form data
        tool_name = request.form.get('tool_name', '').strip()
        version = request.form.get('version', '').strip()
        email = request.form.get('email', '').strip()
        custom_tool_name = request.form.get('custom_tool_name', '').strip()
        
        logger.info(f"Parsed data - Tool: '{tool_name}', Version: '{version}', Email: '{email}', Custom: '{custom_tool_name}'")
        
        # Handle custom tool name
        if tool_name == 'Other' and custom_tool_name:
            tool_name = custom_tool_name
            logger.info(f"Using custom tool name: '{tool_name}'")
        
        # Detailed validation
        validation_errors = []
        
        if not tool_name:
            validation_errors.append("Tool name is required")
        if not version:
            validation_errors.append("Version is required")
        if not email:
            validation_errors.append("Email is required")
        
        # Email format validation
        if email and '@' not in email:
            validation_errors.append("Invalid email format - missing @")
        if email and '.' not in email.split('@')[-1]:
            validation_errors.append("Invalid email format - missing domain extension")
        
        # Version validation
        import re
        if version and not re.search(r'\d', version):
            validation_errors.append("Version must contain at least one number")
        
        if validation_errors:
            logger.error(f"Validation errors: {validation_errors}")
            for error in validation_errors:
                flash(error, 'error')
            return redirect(url_for('index'))
        
        logger.info("All validations passed")
        
        # Add submission to database
        logger.info("Attempting to add submission to database...")
        submission_id = db.add_submission(tool_name, version, email)
        logger.info(f"Successfully added submission with ID: {submission_id}")
        
        success_message = f'Successfully submitted {tool_name} version {version}! You will be notified if an update is available.'
        flash(success_message, 'success')
        logger.info(f"Success: {success_message}")
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        error_message = f"Error submitting version: {str(e)}"
        logger.error(f"Exception in submit_version: {error_message}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        flash('An error occurred while submitting your information. Please check the logs and try again.', 'error')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Dashboard showing all submissions and their status"""
    logger.info("Dashboard accessed")
    try:
        submissions = db.get_all_submissions()
        logger.info(f"Retrieved {len(submissions)} submissions for dashboard")
        
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
        logger.error(f"Traceback: {traceback.format_exc()}")
        flash('An error occurred while loading the dashboard.', 'error')
        return render_template('dashboard.html', submissions=[])

@app.route('/debug')
def debug_info():
    """Debug information page"""
    logger.info("Debug info page accessed")
    
    debug_data = {
        'database_path': db.db_path,
        'database_exists': os.path.exists(db.db_path),
        'total_submissions': len(db.get_all_submissions()),
        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        'flask_version': None,
        'working_directory': os.getcwd(),
        'environment_variables': {
            'SECRET_KEY': 'SET' if os.getenv('SECRET_KEY') else 'NOT SET',
            'DEBUG': os.getenv('DEBUG', 'False'),
            'PORT': os.getenv('PORT', '5000')
        }
    }
    
    try:
        import flask
        debug_data['flask_version'] = flask.__version__
    except:
        debug_data['flask_version'] = 'Unknown'
    
    return f"""
    <html>
    <head><title>Debug Information</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h1>🐛 Debug Information</h1>
        <h2>System Status</h2>
        <ul>
            <li>Database Path: {debug_data['database_path']}</li>
            <li>Database Exists: {debug_data['database_exists']}</li>
            <li>Total Submissions: {debug_data['total_submissions']}</li>
            <li>Python Version: {debug_data['python_version']}</li>
            <li>Flask Version: {debug_data['flask_version']}</li>
            <li>Working Directory: {debug_data['working_directory']}</li>
        </ul>
        
        <h2>Environment Variables</h2>
        <ul>
            {''.join([f'<li>{k}: {v}</li>' for k, v in debug_data['environment_variables'].items()])}
        </ul>
        
        <h2>Recent Log Entries</h2>
        <pre style="background: #f0f0f0; padding: 10px; max-height: 300px; overflow-y: scroll;">
        {'Log file not found or empty' if not os.path.exists('data/debug.log') else open('data/debug.log').read()[-2000:]}
        </pre>
        
        <h2>Test Form Submission</h2>
        <form method="POST" action="/submit">
            <p>Tool Name: <select name="tool_name">
                <option value="Python">Python</option>
                <option value="SQL Server">SQL Server</option>
                <option value="Node.js">Node.js</option>
            </select></p>
            <p>Version: <input type="text" name="version" value="3.9.1" required></p>
            <p>Email: <input type="email" name="email" value="debug@test.com" required></p>
            <p><button type="submit">Test Submit</button></p>
        </form>
        
        <p><a href="/">← Back to Main Page</a> | <a href="/dashboard">Dashboard</a></p>
    </body>
    </html>
    """

@app.route('/api/check-version', methods=['POST'])
def api_check_version():
    """API endpoint to manually trigger version check for a specific submission"""
    logger.info("API version check called")
    try:
        submission_id = request.json.get('submission_id')
        logger.info(f"Checking version for submission ID: {submission_id}")
        
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
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Initialize database
    logger.info("Initializing database...")
    db.init_database()
    logger.info("Database initialized successfully")
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    
    print(f"""
    🐛 DEBUG MODE - Tool Version Audit & Notification System
    
    📝 Main Form: http://localhost:{port}
    📊 Dashboard: http://localhost:{port}/dashboard  
    🐛 Debug Info: http://localhost:{port}/debug
    📋 Debug Log: data/debug.log
    
    This version includes detailed logging for troubleshooting.
    """)
    
    app.run(host='0.0.0.0', port=port, debug=True)