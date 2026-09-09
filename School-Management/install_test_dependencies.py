
#!/usr/bin/env python3
"""
Install Test Dependencies
"""

import subprocess
import sys
import os

def install_package(package_name):
    """Install a Python package"""
    try:
        print(f"📦 Installing {package_name}...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', package_name], 
                              capture_output=True, text=True, check=True)
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def main():
    print("🔧 Installing Test Dependencies for School Management System")
    print("=" * 60)
    
    # Required packages for testing
    packages = [
        'requests',      # HTTP testing
        'psutil',        # System monitoring
        'reportlab',     # PDF generation (already in main requirements)
    ]
    
    success_count = 0
    
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Installation Summary: {success_count}/{len(packages)} packages installed")
    
    if success_count == len(packages):
        print("🎉 All test dependencies installed successfully!")
        print("\nYou can now run the tests:")
        print("  python quick_health_check.py      # Quick health check")
        print("  python run_all_tests.py          # Comprehensive testing")
    else:
        print("⚠️  Some packages failed to install. Tests may not work properly.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
