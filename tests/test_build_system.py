#!/usr/bin/env python3
"""
Build system tests for vLLM Kubernetes Plugin

Tests the configuration generation and package building functionality.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestBuildSystem:
    """Test cases for the build system"""

    @pytest.fixture
    def project_root(self):
        """Fixture to get project root directory"""
        return Path(__file__).parent.parent

    def test_config_generation(self, project_root):
        """Test that configuration files can be generated"""
        generate_script = project_root / "scripts" / "generate_config.py"

        assert generate_script.exists(), "Configuration generation script not found"

        # Run configuration generation
        result = subprocess.run(
            [sys.executable, str(generate_script)],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Config generation failed: {result.stderr}"

        # Check if config file was created
        config_file = (
            project_root
            / "src"
            / "vllm_kubernetes_plugin"
            / "config"
            / "vllm_scanned_info.py"
        )
        assert config_file.exists(), "Configuration file was not created"

    def test_package_building(self, project_root):
        """Test that the package can be built successfully"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with uv build if available
            try:
                cmd = ["uv", "build", "--out-dir", temp_dir]
                result = subprocess.run(
                    cmd,
                    cwd=project_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to setup.py if uv is not available
                cmd = [
                    sys.executable,
                    "setup.py",
                    "bdist_wheel",
                    "--dist-dir",
                    temp_dir,
                ]
                result = subprocess.run(
                    cmd,
                    cwd=project_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            # Check if wheel file was created
            wheel_files = list(Path(temp_dir).glob("*.whl"))
            assert len(wheel_files) > 0, "No wheel file was created"

            wheel_file = wheel_files[0]
            assert wheel_file.stat().st_size > 0, "Wheel file is empty"

    def test_package_import(self, project_root):
        """Test that the package can be imported after building"""
        # Add src directory to Python path
        src_dir = project_root / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))

        try:
            # Test basic import
            import vllm_kubernetes_plugin

            # Test that main modules can be imported
            from vllm_kubernetes_plugin.common import logger_plugin
            from vllm_kubernetes_plugin.common import trace_plugin

            # Test that config exists
            from vllm_kubernetes_plugin.config import vllm_scanned_info

            assert hasattr(vllm_scanned_info, "SCANNED_INFO"), (
                "SCANNED_INFO not found in config"
            )

        except ImportError as e:
            pytest.fail(f"Package import failed: {e}")

    def test_build_with_config_script(self, project_root):
        """Test the build_with_config.py script with --test option"""
        build_script = project_root / "build_with_config.py"

        assert build_script.exists(), "build_with_config.py script not found"

        # Test the build script with test option
        result = subprocess.run(
            [sys.executable, str(build_script), "--test", "--no-clean"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Build script failed: {result.stderr}"
        assert "🎉 All tests passed!" in result.stdout, (
            "Build validation tests did not pass"
        )


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__])
