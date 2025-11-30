#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cross-platform compatibility verification script for SimTradeLab

This script verifies that SimTradeLab is properly configured for
cross-platform installation via pip.
"""

import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd  # nosec B602
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_project_structure():
    """Check if all required files are present."""
    print("🔍 Checking project structure...")

    required_files = [
        "pyproject.toml",
        "setup.py",
        "MANIFEST.in",
        "src/simtradelab/__init__.py",
        "README.md",
        "LICENSE",
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True


def check_build_config():
    """Check build configuration in pyproject.toml."""
    print("\n🔍 Checking build configuration...")

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            print("❌ Cannot check pyproject.toml - no TOML parser available")
            return False

    try:
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        # Check build system
        build_system = config.get("build-system", {})
        requires = build_system.get("requires", [])

        required_build_deps = ["poetry-core", "setuptools", "wheel", "numpy"]
        missing_deps = []

        for dep in required_build_deps:
            if not any(dep in req for req in requires):
                missing_deps.append(dep)

        if missing_deps:
            print(f"❌ Missing build dependencies: {missing_deps}")
            return False

        # Check classifiers include OS Independent
        classifiers = config.get("tool", {}).get("poetry", {}).get("classifiers", [])
        if "Operating System :: OS Independent" not in classifiers:
            print("⚠️  Consider adding 'Operating System :: OS Independent' classifier")

        print("✅ Build configuration looks good")
        return True

    except Exception as e:
        print(f"❌ Error checking pyproject.toml: {e}")
        return False


def test_poetry_build():
    """Test Poetry build."""
    print("\n🏗️  Testing Poetry build...")

    success, stdout, stderr = run_command("poetry build")

    if success:
        print("✅ Poetry build successful")

        # Check if wheel and sdist were created
        dist_files = list(Path("dist").glob("*"))
        wheel_files = [f for f in dist_files if f.suffix == ".whl"]
        sdist_files = [f for f in dist_files if f.suffix == ".gz"]

        if wheel_files and sdist_files:
            print(f"✅ Created wheel: {wheel_files[0].name}")
            print(f"✅ Created sdist: {sdist_files[0].name}")
            return True
        else:
            print("❌ Build artifacts missing")
            return False
    else:
        print(f"❌ Poetry build failed: {stderr}")
        return False


def test_setuptools_build():
    """Test setuptools build as fallback."""
    print("\n🏗️  Testing setuptools build...")

    success, stdout, stderr = run_command("python -m build --wheel")

    if success:
        print("✅ Setuptools build successful")
        return True
    else:
        print(f"❌ Setuptools build failed: {stderr}")
        return False


def test_wheel_installation():
    """Test wheel installation in a temporary virtual environment."""
    print("\n📦 Testing wheel installation...")

    # Find the wheel file
    wheel_files = list(Path("dist").glob("*.whl"))
    if not wheel_files:
        print("❌ No wheel file found")
        return False

    wheel_file = wheel_files[0]

    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        venv_path = temp_path / "test_venv"

        # Create virtual environment
        success, _, stderr = run_command(f"python -m venv {venv_path}")
        if not success:
            print(f"❌ Failed to create virtual environment: {stderr}")
            return False

        # Determine activation script
        if sys.platform == "win32":
            _ = venv_path / "Scripts" / "activate.bat"  # activate脚本路径，当前未使用
            pip_cmd = f"{venv_path / 'Scripts' / 'pip.exe'}"
        else:
            _ = venv_path / "bin" / "activate"  # activate脚本路径，当前未使用
            pip_cmd = f"{venv_path / 'bin' / 'pip'}"

        # Install wheel
        success, stdout, stderr = run_command(
            f"{pip_cmd} install {wheel_file.absolute()}"
        )
        if not success:
            print(f"❌ Failed to install wheel: {stderr}")
            return False

        # Test import
        if sys.platform == "win32":
            python_cmd = f"{venv_path / 'Scripts' / 'python.exe'}"
        else:
            python_cmd = f"{venv_path / 'bin' / 'python'}"

        success, stdout, stderr = run_command(
            f"{python_cmd} -c \"import simtradelab; print(f'SimTradeLab {{simtradelab.__version__}} imported successfully')\""
        )

        if success:
            print(f"✅ Wheel installation test passed: {stdout.strip()}")
            return True
        else:
            print(f"❌ Import test failed: {stderr}")
            return False


def check_github_actions():
    """Check GitHub Actions configuration."""
    print("\n🔍 Checking GitHub Actions...")

    workflow_files = list(Path(".github/workflows").glob("*.yml"))
    if not workflow_files:
        print("⚠️  No GitHub Actions workflows found")
        return True

    outdated_actions = []
    for workflow_file in workflow_files:
        with open(workflow_file, "r") as f:
            content = f.read()

        # Check for outdated actions
        if "upload-artifact@v3" in content:
            outdated_actions.append(f"{workflow_file.name}: upload-artifact@v3")
        if "download-artifact@v3" in content:
            outdated_actions.append(f"{workflow_file.name}: download-artifact@v3")
        if "setup-python@v4" in content:
            outdated_actions.append(f"{workflow_file.name}: setup-python@v4")

    if outdated_actions:
        print("❌ Found outdated GitHub Actions:")
        for action in outdated_actions:
            print(f"  - {action}")
        return False
    else:
        print("✅ GitHub Actions are up to date")
        return True


def main():
    """Main verification function."""
    print("SimTradeLab Cross-Platform Compatibility Check")
    print("=" * 50)

    # Change to project root if needed
    if not Path("pyproject.toml").exists():
        print("❌ Not in project root directory")
        return False

    checks = [
        check_project_structure,
        check_build_config,
        test_poetry_build,
        test_setuptools_build,
        test_wheel_installation,
        check_github_actions,
    ]

    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("\n🎉 SimTradeLab is ready for cross-platform pip installation!")
        return True
    else:
        print(f"❌ SOME CHECKS FAILED ({passed}/{total})")
        print("\n🔧 Please fix the issues above before releasing.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
