import os
import sys
import shutil
import subprocess
from pathlib import Path
import site

def build_exe():
    """Build the PhotoDisarm executable with proper OpenCV configuration."""
    print("\n🔨 Starting PhotoDisarm build process...")
    
    # Clean previous build artifacts
    for dir_name in ['build', 'dist', '_temp_build']:
        if os.path.exists(dir_name):
            print(f"   Cleaning {dir_name} directory...")
            shutil.rmtree(dir_name)
    
    # Create a temporary directory for build preparations
    os.makedirs("_temp_build", exist_ok=True)
    
    # Create a more robust entry point script for PyInstaller
    entry_script = """
import sys
import os
import site
import cv2

# Add the directory containing your package to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Ensure OpenCV finds its configuration
cv2_base_path = os.path.dirname(cv2.__file__)
if hasattr(sys, '_MEIPASS'):
    # Running as a PyInstaller bundle
    cv2_path = os.path.join(sys._MEIPASS, 'cv2')
    if os.path.exists(cv2_path):
        sys.path.insert(0, cv2_path)

# Create a simple wrapper script to launch the app
if __name__ == "__main__":
    # Import after OpenCV is configured
    try:
        # First try importing the explicit main function if available
        from photodisarm.__main__ import main
        main()
    except (ImportError, AttributeError):
        # Fall back to running the module directly
        import photodisarm.__main__
"""
    
    with open("_temp_build/launcher.py", "w") as f:
        f.write(entry_script)
    
    # Find and copy OpenCV configuration files
    print("\n📦 Finding OpenCV configuration files...")
    import cv2
    cv2_base_path = os.path.dirname(cv2.__file__)
    cv2_config_file = os.path.join(cv2_base_path, 'config.py')
    cv2_config_template = os.path.join(cv2_base_path, 'config-3.py')
    
    # Create cv2 directory in _temp_build
    cv2_temp_dir = os.path.join('_temp_build', 'cv2')
    os.makedirs(cv2_temp_dir, exist_ok=True)
    
    # Copy config files if they exist
    if os.path.exists(cv2_config_file):
        print(f"   Found config.py at {cv2_config_file}")
        shutil.copy2(cv2_config_file, os.path.join(cv2_temp_dir, 'config.py'))
    elif os.path.exists(cv2_config_template):
        print(f"   Found config-3.py at {cv2_config_template}")
        shutil.copy2(cv2_config_template, os.path.join(cv2_temp_dir, 'config.py'))
    else:
        print("   ⚠️ OpenCV config files not found. Creating default config.py...")
        # Create a minimal config.py file
        with open(os.path.join(cv2_temp_dir, 'config.py'), 'w') as f:
            f.write("""
BINARIES_PATHS = []
PYTHON_EXTENSIONS_PATHS = []
LOADER_DIR = ''
""")
    
    # Copy __init__.py from OpenCV to ensure it works
    init_file = os.path.join(cv2_base_path, '__init__.py')
    if os.path.exists(init_file):
        shutil.copy2(init_file, os.path.join(cv2_temp_dir, '__init__.py'))
    
    # Prepare a directory to copy a modified version of the package
    package_dir = "_temp_build/photodisarm"
    os.makedirs(package_dir, exist_ok=True)
    
    # Process and copy all Python files
    print("\n📝 Processing source files...")
    for src_file in Path("photodisarm").glob("*.py"):
        dest_file = Path(package_dir) / src_file.name
        content = src_file.read_text(encoding="utf-8")
        
        # Fix any problematic imports
        if src_file.name == "dub.py":
            print(f"   Fixing imports in {src_file.name}")
            if "from tkinter import ttk" in content:
                content = content.replace(
                    "from tkinter import ttk, messagebox", 
                    "import tkinter\nimport tkinter.ttk as ttk\nfrom tkinter import messagebox"
                )
            # Fix circular imports with __main__
            if "from . import __main__ as main_module" in content:
                content = content.replace(
                    "from . import __main__ as main_module",
                    "try:\n    from . import __main__ as main_module\nexcept ImportError:\n    main_module = None"
                )
        
        # Also fix any direct imports in __main__.py
        if src_file.name == "__main__.py":
            # More thorough replacement of relative imports
            content = content.replace(
                "from .", 
                "from photodisarm."
            )
            # Also handle any 'import .' cases
            content = content.replace(
                "import .", 
                "import photodisarm."
            )
        
        # Write the modified file
        print(f"   Copying {src_file.name}")
        dest_file.write_text(content, encoding="utf-8")
    
    # Create empty __init__.py
    Path(package_dir, "__init__.py").write_text("# Package initialization")
    
    # Create hook-cv2.py to ensure OpenCV is correctly packaged
    os.makedirs("_temp_build/hooks", exist_ok=True)
    with open("_temp_build/hooks/hook-cv2.py", "w") as f:
        f.write("""
# PyInstaller hook for cv2
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, get_module_file_attribute
import os.path

binaries = collect_dynamic_libs('cv2')
datas = collect_data_files('cv2')

# Add OpenCV config files
cv2_path = os.path.dirname(get_module_file_attribute('cv2'))
config_file = os.path.join(cv2_path, 'config.py')
config_template = os.path.join(cv2_path, 'config-3.py')

if os.path.exists(config_file):
    datas.append((config_file, 'cv2'))
elif os.path.exists(config_template):
    datas.append((config_template, 'cv2'))
""")
        
    # Create spec file for better control over the build process
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

# Get path to the cv2 module
import cv2
cv2_path = os.path.dirname(cv2.__file__)

# Define paths for adding module hooks
module_collection_paths = ['./_temp_build/hooks']

datas = [
    ('_temp_build/photodisarm', 'photodisarm'),
    ('_temp_build/cv2', 'cv2'),
    ('pics', 'pics')
]

# Add OpenCV config files explicitly
config_file = os.path.join(cv2_path, 'config.py')
config_template = os.path.join(cv2_path, 'config-3.py')
if os.path.exists(config_file):
    datas.append((config_file, 'cv2'))
elif os.path.exists(config_template):
    datas.append((config_template, 'cv2'))

a = Analysis(
    ['_temp_build/launcher.py'],
    pathex=['_temp_build', '.'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'tkinter', 
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'cv2',
        'rawpy',
        'numpy',
        'PIL',
        'PIL.Image',
        'PIL.ExifTags',
        'asyncio',
        'PIL._tkinter_finder',
        'glob',
        'multiprocessing',
        'collections.deque',
    ],
    hookspath=module_collection_paths,
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PhotoDisarm',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True for debugging
    icon=None,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    # Write the spec file
    with open("PhotoDisarm.spec", "w") as f:
        f.write(spec_content)
    
    # Run PyInstaller with the spec file in the current environment
    print("\n🚀 Running PyInstaller...")
    build_cmd = ["poetry", "run", "pyinstaller", "PhotoDisarm.spec"]
    print(f"   Command: {' '.join(build_cmd)}")
    
    build_result = subprocess.run(build_cmd)
    
    if build_result.returncode == 0:
        print("\n✅ Build successful! Executable is in the 'dist' folder.")
        print(f"   Full path: {os.path.abspath('dist/PhotoDisarm.exe')}")
        
        # Optional: Create a production version without console window
        print("\n🚀 Creating production version without console...")
        # Modify spec to disable console for production version
        with open("PhotoDisarm.spec", "r") as f:
            prod_spec = f.read().replace("console=True,  # Set to True for debugging", "console=False,")
        with open("PhotoDisarm_prod.spec", "w") as f:
            f.write(prod_spec.replace("name='PhotoDisarm'", "name='PhotoDisarm_prod'"))
        
        prod_cmd = ["poetry", "run", "pyinstaller", "PhotoDisarm_prod.spec"]
        subprocess.run(prod_cmd)
        print(f"   Production executable: {os.path.abspath('dist/PhotoDisarm_prod.exe')}")
        
        return True
    else:
        print("\n❌ Build failed with error code:", build_result.returncode)
        return False

if __name__ == "__main__":
    success = build_exe()
    if success:
        print("\n🎉 Build process completed successfully!")
    else:
        print("\n❗ Build process failed. Check the errors above.")
    
    # Keep console window open on error for debugging
    if not success and sys.platform == 'win32' and not sys.stdout.isatty():
        input("\nPress Enter to close...")