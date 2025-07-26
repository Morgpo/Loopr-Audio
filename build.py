import subprocess
import sys
import os
from pathlib import Path

def build_app():
    """Build the Loopr Audio application using PyInstaller"""
    
    # Get the project root directory (current working directory)
    project_root = Path.cwd()
    
    # Path to the main Python file
    main_file = project_root / "loopr_audio.py"
    
    if not main_file.exists():
        print(f"Error: Main file not found at {main_file}")
        return False
    
    # Check for existing icons in _internal directory (prioritize .ico for Windows)
    internal_dir = project_root / "_internal"
    ico_path = internal_dir / "loopr_icon.ico"
    png_path = internal_dir / "loopr_icon.png"
    
    icon_path = None
    if ico_path.exists():
        icon_path = ico_path
        print(f"Found Windows icon: {ico_path}")
    elif png_path.exists():
        icon_path = png_path
        print(f"Found PNG icon: {png_path}")
        print("Note: Converting PNG to ICO format would be better for Windows applications")
    else:
        print("Warning: No icon files found in _internal/ directory (loopr_icon.ico or loopr_icon.png)")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onedir",              # Create one-directory bundle
        "--windowed",            # Don't show console window
        "--name", "LooprAudio",  # Application name
        "--distpath", "dist",    # Distribution directory
        "--workpath", "build",   # Work directory
        "-y",                    # Replace output directory without confirmation
    ]
    
    # Add icon files as data files so they're available at runtime in the _internal directory
    if ico_path.exists():
        cmd.extend(["--add-data", f"{ico_path};."])
        print(f"Including ICO file in build: {ico_path}")
    
    if png_path.exists():
        cmd.extend(["--add-data", f"{png_path};."])
        print(f"Including PNG file in build: {png_path}")
    
    # Add icon for executable if available
    if icon_path:
        cmd.extend(["--icon", str(icon_path)])
        print(f"Using executable icon: {icon_path}")
    else:
        print("Building without custom executable icon")
    
    # Add the main file
    cmd.append(str(main_file))
    
    print("Building Loopr Audio application...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Change to project root directory
        os.chdir(project_root)
        
        # Run PyInstaller
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("Build completed successfully!")
        print(f"Application built in: {project_root / 'dist' / 'LooprAudio'}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("Loopr Audio Build Script")
    print("=" * 40)
    
    success = build_app()
    
    if success:
        print("\nBuild completed successfully!")
        print("You can find the executable in the 'dist/LooprAudio' folder.")
    else:
        print("\nBuild failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
