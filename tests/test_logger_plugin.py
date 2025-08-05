#!/usr/bin/env python3
"""
Test cases for logger plugin functionality

This module contains tests for the non-invasive extension of vllm.envs module.
"""

import os
import pytest
from vllm_kubernetes_plugin.common.logger_plugin import (
    add_logger_env_vars,
)


def test_non_invasive_envs_extension():
    """
    Test non-invasive extension of vllm.envs module

    This test demonstrates how to dynamically add new environment variables
    to vllm.envs module without modifying vllm source code.
    """
    # Set up some environment variables for testing
    original_env = {}
    test_env_vars = {
        "APP_NAME": "my-vllm-app",
        "VLLM_LOG_FILENAME": "custom-server.log",
        "VLLM_LOG_FILE_MAX_BYTES": "16777216",  # 16MB
        "VLLM_LOG_FILE_BACKUP_COUNT": "10",
    }

    # Store original values and set test values
    for key, value in test_env_vars.items():
        if key in os.environ:
            original_env[key] = os.environ[key]
        os.environ[key] = value

    try:
        # Test before extension - should fail
        import vllm.envs as envs

        # Verify that new environment variables don't exist initially
        with pytest.raises(AttributeError):
            _ = envs.APP_NAME

        # Perform non-invasive extension
        add_logger_env_vars()

        # Test after extension - should succeed
        assert envs.APP_NAME == "my-vllm-app"
        assert envs.LOG_ROOT_MODULES == "vllm"  # Default value (string, not list)
        assert envs.VLLM_LOG_FILENAME == "custom-server.log"
        assert envs.VLLM_LOG_FILE_MAX_BYTES == 16777216  # Should be converted to int
        assert envs.VLLM_LOG_FILE_BACKUP_COUNT == 10  # Should be converted to int

        # Test default values by clearing environment variables
        for key in test_env_vars.keys():
            if key in os.environ:
                del os.environ[key]

        # Since these are lambda functions, they will re-read environment variables
        assert envs.APP_NAME == "standalone"  # Default value
        assert envs.VLLM_LOG_FILENAME == "server.log"  # Default value
        assert envs.VLLM_LOG_FILE_MAX_BYTES == 8388608  # Default 8MB
        assert envs.VLLM_LOG_FILE_BACKUP_COUNT == 5  # Default value

        # Verify the new variables are added to module's __dir__ method
        all_vars = dir(envs)
        new_vars = [
            "APP_NAME",
            "LOG_ROOT_MODULES",
            "VLLM_LOG_FILENAME",
            "VLLM_LOG_FILE_MAX_BYTES",
            "VLLM_LOG_FILE_BACKUP_COUNT",
        ]

        for var in new_vars:
            assert var in all_vars, (
                f"{var} should be successfully added to vllm.envs module"
            )

    finally:
        # Restore original environment variables
        for key in test_env_vars.keys():
            if key in os.environ:
                del os.environ[key]
            if key in original_env:
                os.environ[key] = original_env[key]


def test_environment_variable_types():
    """
    Test that environment variables are properly converted to correct types
    """
    # Set environment variables as strings
    os.environ["VLLM_LOG_FILE_MAX_BYTES"] = "33554432"  # 32MB
    os.environ["VLLM_LOG_FILE_BACKUP_COUNT"] = "3"

    try:
        # Import and extend
        import vllm.envs as envs

        add_logger_env_vars()

        # Verify types are correct
        assert isinstance(envs.VLLM_LOG_FILE_MAX_BYTES, int)
        assert envs.VLLM_LOG_FILE_MAX_BYTES == 33554432

        assert isinstance(envs.VLLM_LOG_FILE_BACKUP_COUNT, int)
        assert envs.VLLM_LOG_FILE_BACKUP_COUNT == 3

    finally:
        # Clean up
        for key in ["VLLM_LOG_FILE_MAX_BYTES", "VLLM_LOG_FILE_BACKUP_COUNT"]:
            if key in os.environ:
                del os.environ[key]


def test_log_root_modules_parsing():
    """
    Test that LOG_ROOT_MODULES environment variable is properly handled
    """
    # Test with custom modules
    os.environ["LOG_ROOT_MODULES"] = "vllm,transformers,torch"

    try:
        import vllm.envs as envs

        add_logger_env_vars()

        assert isinstance(envs.LOG_ROOT_MODULES, str)
        assert envs.LOG_ROOT_MODULES == "vllm,transformers,torch"

    finally:
        if "LOG_ROOT_MODULES" in os.environ:
            del os.environ["LOG_ROOT_MODULES"]
