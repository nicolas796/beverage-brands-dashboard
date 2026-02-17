#!/usr/bin/env python3
"""
Setup script for the web interface backend
"""
import os
import sys
import subprocess

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 9):
        print("Error: Python 3.9+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def create_virtual_env():
    """Create virtual environment"""
    venv_path = "venv"
    if not os.path.exists(venv_path):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
    print("✓ Virtual environment ready")

def install_requirements():
    """Install Python dependencies"""
    print("Installing requirements...")
    pip_cmd = "venv/bin/pip" if os.name != 'nt' else "venv\\Scripts\\pip"
    subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
    print("✓ Requirements installed")

def init_database():
    """Initialize database with sample data"""
    print("Initializing database...")
    python_cmd = "venv/bin/python" if os.name != 'nt' else "venv\\Scripts\\python"
    subprocess.run([python_cmd, "init_db.py"], check=True)
    print("✓ Database initialized")

def main():
    print("Setting up Beverage Brands Web Interface...")
    print("-" * 50)
    
    check_python_version()
    create_virtual_env()
    install_requirements()
    init_database()
    
    print("-" * 50)
    print("Setup complete!")
    print("\nTo start the development server:")
    print("  cd backend")
    print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print("  uvicorn app:app --reload")
    print("\nFrontend (in another terminal):")
    print("  cd frontend")
    print("  npm install")
    print("  npm start")

if __name__ == "__main__":
    main()
