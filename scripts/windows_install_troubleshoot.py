#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows Installation Troubleshooting Script for SimTradeLab

This script helps diagnose and resolve common installation issues on Windows.
Run this script if you encounter problems installing SimTradeLab with pip.
"""

import importlib.util
import platform
import subprocess
import sys


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version < (3, 10):
        print("❌ Python 3.10+ is required for SimTradeLab")
        return False
    else:
        print("✅ Python version is compatible")
        return True


def check_platform():
    """Check platform information."""
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")

    if platform.system() == "Windows":
        print("✅ Running on Windows")
        return True
    else:
        print("ℹ️ This script is designed for Windows, but may work on other platforms")
        return True


def check_pip():
    """Check pip installation and version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"], capture_output=True, text=True
        )
        print(f"pip version: {result.stdout.strip()}")
        print("✅ pip is available")
        return True
    except Exception as e:
        print(f"❌ pip not available: {e}")
        return False


def check_build_tools():
    """Check for build tools on Windows."""
    print("\nChecking for build tools...")

    # Check for Visual Studio Build Tools
    try:
        result = subprocess.run(["where", "cl"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Microsoft C++ Build Tools found")
            return True
    except:
        pass

    print("❌ Microsoft C++ Build Tools not found")
    print("💡 Install Visual Studio Build Tools or Visual Studio Community")
    print("   Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    return False


def check_dependencies():
    """Check if key dependencies can be installed."""
    dependencies = ["setuptools", "wheel", "numpy", "pandas"]

    print("\nChecking dependencies...")
    for dep in dependencies:
        try:
            spec = importlib.util.find_spec(dep)
            if spec is not None:
                print(f"✅ {dep} is available")
            else:
                print(f"❌ {dep} not found")
        except ImportError:
            print(f"❌ {dep} not found")


def suggest_solutions():
    """Suggest solutions for common problems."""
    print("\n" + "=" * 50)
    print("SUGGESTED SOLUTIONS")
    print("=" * 50)

    print("\n1. Upgrade pip and build tools:")
    print("   python -m pip install --upgrade pip setuptools wheel")

    print("\n2. Install Visual Studio Build Tools (Windows only):")
    print("   Download and install from:")
    print("   https://visualstudio.microsoft.com/visual-cpp-build-tools/")

    print("\n3. Try installing with pre-compiled wheels:")
    print("   pip install --only-binary=all numpy pandas matplotlib")
    print("   pip install simtradelab")

    print("\n4. Use conda environment (recommended for Windows):")
    print("   conda create -n simtradelab python=3.12")
    print("   conda activate simtradelab")
    print("   conda install numpy pandas matplotlib pyyaml")
    print("   pip install simtradelab")

    print("\n5. Install from source with Poetry:")
    print("   git clone https://github.com/kay-ou/SimTradeLab.git")
    print("   cd SimTradeLab")
    print("   pip install poetry")
    print("   poetry install")

    print("\n6. Try installing without build isolation:")
    print("   pip install --no-build-isolation simtradelab")

    print("\n7. Clear pip cache and retry:")
    print("   pip cache purge")
    print("   pip install simtradelab")


def test_installation():
    """Test if SimTradeLab can be installed and imported."""
    print("\n" + "=" * 50)
    print("TESTING INSTALLATION")
    print("=" * 50)

    try:
        print("Attempting to install SimTradeLab...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "simtradelab", "--user"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Installation successful")

            # Test import
            try:
                import simtradelab

                print(f"✅ Import successful - version {simtradelab.__version__}")
                return True
            except ImportError as e:
                print(f"❌ Import failed: {e}")
                return False
        else:
            print("❌ Installation failed:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False


def main():
    """Main troubleshooting function."""
    print("SimTradeLab Windows Installation Troubleshooter")
    print("=" * 50)

    # System checks
    python_ok = check_python_version()
    platform_ok = check_platform()
    pip_ok = check_pip()
    build_tools_ok = check_build_tools()

    check_dependencies()

    if not python_ok:
        print("\n❌ Please upgrade Python to 3.10+ and try again")
        return

    if not pip_ok:
        print("\n❌ Please install pip and try again")
        return

    # Suggest solutions
    suggest_solutions()

    # Ask user if they want to test installation
    try:
        response = input("\nWould you like to test installation now? (y/n): ")
        if response.lower().startswith("y"):
            test_installation()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")


if __name__ == "__main__":
    main()
