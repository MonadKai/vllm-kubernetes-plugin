#!/usr/bin/env python3
"""
Test script for find_methods_with_request_id function
Validates the function output against the generated JSON configuration
"""

import json
import sys
from pathlib import Path
from typing import List

# Add the project root to sys.path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils import find_methods_with_request_id


def load_expected_methods() -> List[str]:
    """Load expected methods from the generated JSON configuration file"""
    json_file = project_root / "scripts" / "test_output" / "vllm_scanned_info.json"

    if not json_file.exists():
        print(f"Warning: JSON configuration file not found at {json_file}")
        print("Please run generate_config.py first to create the reference file")
        return []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        return config.get("methods_with_request_id", [])
    except Exception as e:
        print(f"Error reading JSON configuration: {e}")
        return []


def compare_method_lists(expected: List[str], actual: List[str]) -> None:
    """Compare expected and actual method lists and report differences"""
    expected_set = set(expected)
    actual_set = set(actual)

    print(f"Expected methods count: {len(expected_set)}")
    print(f"Actual methods count: {len(actual_set)}")

    # Find differences
    missing_methods = expected_set - actual_set
    extra_methods = actual_set - expected_set
    common_methods = expected_set & actual_set

    print(f"Common methods: {len(common_methods)}")

    if missing_methods:
        print(f"\nMissing methods ({len(missing_methods)}):")
        for method in sorted(missing_methods):
            print(f"  - {method}")

    if extra_methods:
        print(f"\nExtra methods ({len(extra_methods)}):")
        for method in sorted(extra_methods):
            print(f"  + {method}")

    if not missing_methods and not extra_methods:
        print("\n✅ Perfect match! All methods match the expected configuration.")
    else:
        print(f"\n⚠️  Found differences:")
        print(f"   Missing: {len(missing_methods)}")
        print(f"   Extra: {len(extra_methods)}")


def test_find_methods_with_request_id():
    """Test the find_methods_with_request_id function"""
    print("=== Testing find_methods_with_request_id function ===")

    print("\nStep 1: Loading expected methods from JSON configuration...")
    expected_methods = load_expected_methods()

    if not expected_methods:
        print("Cannot proceed with test - no expected methods loaded")
        return False

    print("\nStep 2: Scanning vLLM modules for methods with request_id parameters...")
    actual_methods = find_methods_with_request_id("vllm", ignore_init=True)

    print("\nStep 3: Comparing results...")
    compare_method_lists(expected_methods, actual_methods)

    return set(expected_methods) == set(actual_methods)


def main():
    """Main function"""
    print("vLLM Request ID Methods Validation Test")
    print("=" * 50)

    try:
        success = test_find_methods_with_request_id()

        if success:
            print("\n🎉 Test PASSED: Function output matches expected configuration")
            sys.exit(0)
        else:
            print(
                "\n❌ Test FAILED: Function output differs from expected configuration"
            )
            print("\nThis could indicate:")
            print("- vLLM version differences")
            print("- Changes in vLLM API structure")
            print("- Issues with the scanning logic")
            print("\nPlease review the differences above and update accordingly.")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Test ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
