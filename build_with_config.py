#!/usr/bin/env python3
"""
Automatically generate configuration and build vLLM Kubernetes Plugin
Supports multiple build methods and custom parameters
"""

import argparse
import glob
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command, description, continue_on_error=False):
    """Run command and handle errors"""
    print(f"\n{'=' * 50}")
    print(f"Executing: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'=' * 50}")

    try:
        subprocess.run(command, check=True, cwd=Path(__file__).parent)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if continue_on_error:
            print("⚠️  Continue with subsequent steps")
            return False
        else:
            sys.exit(1)


def clean_previous_builds():
    """Clean previous build files"""
    print("🧹 Clean previous build files...")
    
    project_root = Path(__file__).parent
    directories_to_clean = ["build", "dist"]
    patterns_to_clean = ["*.egg-info"]
    
    # Delete directories
    for dir_name in directories_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  🗑️  Delete directory: {dir_name}/")
    
    # Delete files and directories matching patterns
    for pattern in patterns_to_clean:
        for path in glob.glob(str(project_root / pattern)):
            path_obj = Path(path)
            if path_obj.is_dir():
                shutil.rmtree(path_obj)
                print(f"  🗑️  Delete directory: {path_obj.name}")
            elif path_obj.is_file():
                path_obj.unlink()
                print(f"  🗑️  Delete file: {path_obj.name}")
    
    print("✅ Clean completed")


def test_build():
    """Test build results"""
    print("\n🧪 Start build validation tests...")
    
    project_root = Path(__file__).parent
    success = True
    
    # Test 1: Check if configuration file is generated
    print("  📋 Checking configuration file...")
    config_file = project_root / "src" / "vllm_kubernetes_plugin" / "config" / "vllm_scanned_info.py"
    if config_file.exists():
        print("    ✅ Configuration file exists")
    else:
        print("    ❌ Configuration file missing")
        success = False
    
    # Test 2: Check build artifacts
    print("  📦 Checking build artifacts...")
    dist_dir = project_root / "dist"
    if dist_dir.exists():
        wheel_files = list(dist_dir.glob("*.whl"))
        tar_files = list(dist_dir.glob("*.tar.gz"))
        
        if wheel_files:
            print(f"    ✅ Wheel file: {wheel_files[0].name}")
        else:
            print("    ❌ Missing Wheel file")
            success = False
            
        if tar_files:
            print(f"    ✅ Source code package: {tar_files[0].name}")
        else:
            print("    ❌ Missing source code package")
            success = False
    else:
        print("    ❌ dist directory does not exist")
        success = False
    
    # Test 3: Verify package importability
    print("  🔍 Testing package import...")
    try:
        # 简单的导入测试
        import sys
        sys.path.insert(0, str(project_root / "src"))
        import vllm_kubernetes_plugin
        print("    ✅ Package can be imported")
    except ImportError as e:
        print(f"    ❌ Package import failed: {e}")
        success = False
    
    if success:
        print("  🎉 All tests passed!")
    else:
        print("  ❌ Some tests failed")
        
    return success


def parse_args():
    parser = argparse.ArgumentParser(
        description="vLLM Kubernetes Plugin build script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Build method examples:
  python build_with_config.py                   # Default using uv build
  python build_with_config.py --use-setuptools  # Use setup.py build
  python build_with_config.py --skip-config     # Skip vLLM configuration generation step
  python build_with_config.py --no-clean        # Do not clean previous build files
  python build_with_config.py --test            # Run tests after build (including configuration generation and package building)
        """
    )
    
    parser.add_argument(
        "--use-setuptools", 
        action="store_true",
        help="Use setup.py instead of uv for building"
    )
    
    parser.add_argument(
        "--skip-config", 
        action="store_true",
        help="Skip vLLM configuration generation step"
    )
    
    parser.add_argument(
        "--no-clean", 
        action="store_true",
        help="Do not clean previous build files"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Run tests after build (including configuration generation and package building)"
    )
    
    parser.add_argument(
        "extra_args", 
        nargs="*",
        help="Extra arguments to pass to the build command"
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("🚀 Start vLLM Kubernetes Plugin automatic build process")
    print(f"Build method: {'setup.py' if args.use_setuptools else 'uv'}")
    
    # Step 1: Clean previous builds
    if not args.no_clean:
        clean_previous_builds()
    else:
        print("⏭️  Skip cleanup step")
    
    # Step 2: Generate vLLM configuration
    if not args.skip_config:
        run_command(
            [sys.executable, "scripts/generate_config.py"], 
            "Generate vLLM configuration",
            continue_on_error=True  # Configuration generation failure does not abort build
        )
    else:
        print("⏭️  Skip configuration generation step")
    
    # Step 3: Build project
    if args.use_setuptools:
        # Use setup.py to build
        build_cmd = [sys.executable, "setup.py", "build"]
        if args.extra_args:
            build_cmd.extend(args.extra_args)
        run_command(build_cmd, "Build project using setup.py")
    else:
        # Use uv to build
        build_cmd = ["uv", "build"]
        if args.extra_args:
            build_cmd.extend(args.extra_args)
        run_command(build_cmd, "Build project using uv")

    print(f"\n{'=' * 50}")
    print("🎉 Build completed!")
    print("Files generated:")

    dist_dir = Path(__file__).parent / "dist"
    if dist_dir.exists():
        for file in dist_dir.iterdir():
            if file.is_file():
                file_size = file.stat().st_size
                size_str = f"({file_size:,} bytes)" if file_size > 0 else ""
                print(f"  📦 {file.name} {size_str}")
    else:
        print("  ⚠️  No dist/ directory found")

    print(f"{'=' * 50}")

    if args.test:
        if not test_build():
            print("❌ Build validation tests did not pass!")
            sys.exit(1)


if __name__ == "__main__":
    main()
