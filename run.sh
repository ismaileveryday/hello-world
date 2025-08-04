#!/bin/bash

# Tool Version Audit & Notification System Startup Script

echo "🔧 Starting Tool Version Audit & Notification System..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data static templates

# Set permissions
chmod +x daily_check.py

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before running the system."
fi

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from database import db; db.init_database(); print('Database initialized successfully!')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the web application:"
echo "   python3 app.py"
echo ""
echo "🔄 To run daily checks:"
echo "   python3 daily_check.py run"
echo ""
echo "⏰ To set up automated daily checks, add this to your crontab:"
echo "   0 9 * * * cd $(pwd) && source venv/bin/activate && python3 daily_check.py run"
echo ""
echo "📚 Visit http://localhost:5000/help for complete documentation"
echo ""

# Ask if user wants to start the application
read -p "🤔 Would you like to start the web application now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting web application..."
    python3 app.py
fi