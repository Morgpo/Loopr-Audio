import os
import sys
import subprocess
import shutil
from pathlib import Path

def setup_virtualenv():
    #
    #           Set up a virtual environment for any project.
    #           This script should be placed in <Project>/setup/setup_venv.py
    #           Requirements should be in <Project>/setup/requirements.txt
    #           Virtual environment will be created at <Project>/.venv
    #
    
    # Get the script's directory (setup folder)
    script_dir = Path(__file__).parent.absolute()
    
    # Get the project root directory (parent of setup folder)
    project_root = script_dir.parent
    
    # Define paths
    venv_path = project_root / ".venv"
    requirements_path = script_dir / "requirements.txt"
    
    print(f"Project root: {project_root}")
    print(f"Virtual environment path: {venv_path}")
    print(f"Requirements file: {requirements_path}")
    
    # Check if requirements.txt exists
    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False
    
    # Remove existing virtual environment if it exists
    if venv_path.exists():
        print(f"Removing existing virtual environment at {venv_path}")
        
        # Check if we're currently in the virtual environment we're trying to delete
        current_venv = os.environ.get('VIRTUAL_ENV')
        if current_venv and Path(current_venv).resolve() == venv_path.resolve():
            print("\nERROR: Cannot delete the virtual environment while it's currently activated!")
            print("Please deactivate the virtual environment first by running:")
            print("deactivate")
            print("Then run this script again.")
            return False
        
        try:
            shutil.rmtree(venv_path)
            print("Existing virtual environment removed successfully")
        except PermissionError as e:
            print(f"Permission Error: {e}")
            print("This usually happens when the virtual environment is active or files are in use.")
            print("Please:")
            print("1. Deactivate the virtual environment: deactivate")
            print("2. Close any programs using Python from this environment")
            print("3. Run this script again")
            return False
        except Exception as e:
            print(f"Error removing existing virtual environment: {e}")
            return False
    
    # Create new virtual environment
    print("Creating new virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False
    
    # Determine the correct python executable path in the virtual environment
    if os.name == 'nt':  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:  # Unix-like (macOS, Linux)
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Upgrade pip first
    print("Upgrading pip...")
    try:
        subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print("Pip upgraded successfully")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not upgrade pip: {e}")
    
    # Install requirements
    print(f"Installing requirements from {requirements_path}")
    try:
        # Check if requirements.txt is empty
        if requirements_path.stat().st_size == 0:
            print("Requirements.txt is empty, skipping package installation")
        else:
            subprocess.run([str(pip_exe), "install", "-r", str(requirements_path)], check=True)
            print("Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False
    
    print("\n" + "="*50)
    print("Virtual environment setup completed successfully!")
    print(f"Virtual environment location: {venv_path}")
    print("\nTo activate the virtual environment, run this from the project directory:")
    
    if os.name == 'nt':  # Windows
        print("  .\\.venv\\Scripts\\activate")
    else:  # Unix-like
        print("  source ./.venv/bin/activate")
    
    print("="*50)
    return True

def main():
    """Main function to run the setup"""
    print("Setting up virtual environment...")
    print("="*50)
    
    success = setup_virtualenv()
    
    if success:
        sys.exit(0)
    else:
        print("Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()