#!/usr/bin/env python3
"""
Tool Version Audit & Notification System - Installation Script

This script handles common installation issues including SSL errors
and provides multiple installation methods.
"""

import os
import sys
import subprocess
import platform

def run_command(cmd, description):
    """Run a command and handle errors gracefully"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python():
    """Check if Python 3 is available"""
    print("🐍 Checking Python installation...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is too old. Need Python 3.7+")
        return False

def create_virtual_env():
    """Create virtual environment"""
    if os.path.exists("venv"):
        print("📁 Virtual environment already exists")
        return True
    
    return run_command("python3 -m venv venv", "Creating virtual environment")

def install_packages_method1():
    """Install packages using standard pip"""
    print("\n🔧 Method 1: Standard pip install")
    activate_cmd = "source venv/bin/activate" if platform.system() != "Windows" else "venv\\Scripts\\activate"
    
    cmd = f"{activate_cmd} && pip install --upgrade pip && pip install -r requirements.txt"
    return run_command(cmd, "Installing packages with standard method")

def install_packages_method2():
    """Install packages with SSL workarounds"""
    print("\n🔧 Method 2: SSL workaround install")
    activate_cmd = "source venv/bin/activate" if platform.system() != "Windows" else "venv\\Scripts\\activate"
    
    trusted_hosts = "--trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org"
    cmd = f"{activate_cmd} && pip install --upgrade pip {trusted_hosts} && pip install {trusted_hosts} -r requirements.txt"
    return run_command(cmd, "Installing packages with SSL workaround")

def install_packages_method3():
    """Install packages individually"""
    print("\n🔧 Method 3: Individual package install")
    activate_cmd = "source venv/bin/activate" if platform.system() != "Windows" else "venv\\Scripts\\activate"
    
    packages = [
        "Flask==2.3.3",
        "requests==2.32.4", 
        "packaging==25.0",
        "beautifulsoup4==4.13.4",
        "lxml==6.0.0",
        "schedule==1.2.2"
    ]
    
    trusted_hosts = "--trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org"
    
    for package in packages:
        cmd = f"{activate_cmd} && pip install {trusted_hosts} {package}"
        if not run_command(cmd, f"Installing {package}"):
            return False
    
    return True

def test_installation():
    """Test if the installation works"""
    print("\n🧪 Testing installation...")
    activate_cmd = "source venv/bin/activate" if platform.system() != "Windows" else "venv\\Scripts\\activate"
    
    test_cmd = f'{activate_cmd} && python3 -c "from database import db; print(\\"✅ Database module working\\"); from version_checker import version_checker; print(\\"✅ Version checker working\\"); from app import app; print(\\"✅ Flask app working\\"); print(\\"🎉 All modules imported successfully!\\")"'
    
    return run_command(test_cmd, "Testing core modules")

def main():
    print("🚀 Tool Version Audit & Notification System - Installation")
    print("=" * 60)
    
    # Check Python version
    if not check_python():
        print("\n❌ Please install Python 3.7 or higher and try again.")
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_env():
        print("\n❌ Failed to create virtual environment.")
        sys.exit(1)
    
    # Try different installation methods
    installation_success = False
    
    # Method 1: Standard install
    if install_packages_method1():
        installation_success = True
    else:
        print("⚠️  Standard installation failed, trying SSL workaround...")
        
        # Method 2: SSL workaround
        if install_packages_method2():
            installation_success = True
        else:
            print("⚠️  SSL workaround failed, trying individual install...")
            
            # Method 3: Individual packages
            if install_packages_method3():
                installation_success = True
    
    if not installation_success:
        print("\n❌ All installation methods failed.")
        print("\n🔧 Manual installation steps:")
        print("1. Activate virtual environment:")
        if platform.system() == "Windows":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        print("2. Upgrade pip:")
        print("   pip install --upgrade pip")
        print("3. Install packages with SSL workaround:")
        print("   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org Flask requests packaging beautifulsoup4 lxml schedule")
        sys.exit(1)
    
    # Test installation
    if test_installation():
        print("\n🎉 Installation completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Configure email settings in .env file (copy from .env.example)")
        print("2. Start the web application:")
        if platform.system() == "Windows":
            print("   venv\\Scripts\\activate && python app.py")
        else:
            print("   source venv/bin/activate && python app.py")
        print("3. Visit http://localhost:5000 in your browser")
        print("4. Check the help page at http://localhost:5000/help for documentation")
    else:
        print("\n⚠️  Installation completed but testing failed.")
        print("You may still be able to run the application manually.")

if __name__ == "__main__":
    main()