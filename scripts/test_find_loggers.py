#!/usr/bin/env python3
"""
Test script for find_logger_modules function
Validates the function output against the generated JSON configuration
"""

import json
import sys
from pathlib import Path
from typing import List

# Add the project root to sys.path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils import find_logger_modules, normalized_package_full_name


def load_expected_logger_modules(package_name: str, package_version: str) -> List[str]:
    """Load expected logger modules from the generated JSON configuration file"""
    package_full_name = normalized_package_full_name(package_name, package_version)
    json_file = project_root / "scripts" / "test_output" / f"{package_full_name}.json"

    if not json_file.exists():
        print(f"Warning: JSON configuration file not found at {json_file}")
        print("Please run generate_config.py first to create the reference file")
        return []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        return config.get("modules_with_logger", [])
    except Exception as e:
        print(f"Error reading JSON configuration: {e}")
        return []


def compare_logger_lists(expected: List[str], actual: List[str]) -> None:
    """Compare expected and actual logger module lists and report differences"""
    expected_set = set(expected)
    actual_set = set(actual)

    print(f"Expected logger modules count: {len(expected_set)}")
    print(f"Actual logger modules count: {len(actual_set)}")

    # Find differences
    missing_modules = expected_set - actual_set
    extra_modules = actual_set - expected_set
    common_modules = expected_set & actual_set

    print(f"Common modules: {len(common_modules)}")

    if missing_modules:
        print(f"\nMissing logger modules ({len(missing_modules)}):")
        for module in sorted(missing_modules):
            print(f"  - {module}")

    if extra_modules:
        print(f"\nExtra logger modules ({len(extra_modules)}):")
        for module in sorted(extra_modules):
            print(f"  + {module}")

    if not missing_modules and not extra_modules:
        print(
            "\n✅ Perfect match! All logger modules match the expected configuration."
        )
    else:
        print(f"\n⚠️  Found differences:")
        print(f"   Missing: {len(missing_modules)}")
        print(f"   Extra: {len(extra_modules)}")


def test_find_logger_modules():
    """Test the find_logger_modules function"""
    print("=== Testing find_logger_modules function ===")

    print("\nStep 1: Loading expected logger modules from JSON configuration...")
    expected_modules = load_expected_logger_modules("vllm", "0.10.0")

    if not expected_modules:
        print("Cannot proceed with test - no expected modules loaded")
        return False

    print("\nStep 2: Scanning vLLM modules for logger instances...")
    actual_modules = find_logger_modules("vllm")

    print("\nStep 3: Comparing results...")
    compare_logger_lists(expected_modules, actual_modules)

    return set(expected_modules) == set(actual_modules)


def main():
    """Main function"""
    print("vLLM Logger Modules Validation Test")
    print("=" * 50)

    try:
        success = test_find_logger_modules()

        if success:
            print("\n🎉 Test PASSED: Function output matches expected configuration")
            sys.exit(0)
        else:
            print(
                "\n❌ Test FAILED: Function output differs from expected configuration"
            )
            print("\nThis could indicate:")
            print("- vLLM version differences")
            print("- Changes in vLLM logging structure")
            print("- Issues with the scanning logic")
            print("\nPlease review the differences above and update accordingly.")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Test ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
