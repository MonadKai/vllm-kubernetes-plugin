from setuptools import find_packages, setup
from setuptools.command.build_py import build_py
from distutils.command.clean import clean
import os
import subprocess
import sys
import shutil

ROOT_DIR = os.path.dirname(__file__)
VERSION = "0.1.0"


def get_path(*filepath) -> str:
    return os.path.join(ROOT_DIR, *filepath)


def read_readme() -> str:
    """Read the README file if present."""
    p = get_path("README.md")
    if os.path.isfile(p):
        with open(get_path("README.md"), encoding="utf-8") as f:
            return f.read()
    else:
        return ""


class CustomBuildPy(build_py):
    """Custom build command that generates configuration files before building"""

    def run(self):
        """Run configuration generation before building"""
        print("Generating vLLM scanned info...")

        # Run configuration generation script
        generate_script = get_path("scripts", "generate_config.py")
        if os.path.exists(generate_script):
            try:
                subprocess.run(
                    [sys.executable, generate_script], check=True, cwd=ROOT_DIR
                )
                print("Configuration files generated successfully")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Configuration file generation failed: {e}")
                print("Continuing build, but runtime configuration may be missing")
        else:
            print(
                "Warning: Configuration generation script not found, skipping config generation"
            )

        # Continue with normal build process
        super().run()


class CustomClean(clean):
    """Custom clean command that removes egg_info and build directories"""

    def run(self):
        """Run clean with additional cleanup"""
        # Call the parent clean command first
        super().run()

        # Remove egg_info directory
        egg_info_dirs = [
            "src/vllm_kubernetes_plugin.egg-info",
            "vllm_kubernetes_plugin.egg-info",
        ]
        for egg_info_dir in egg_info_dirs:
            if os.path.exists(egg_info_dir):
                print(f"Removing {egg_info_dir}")
                shutil.rmtree(egg_info_dir)

        # Remove build directory if it exists
        build_dir = get_path("build")
        if os.path.exists(build_dir):
            print(f"Removing {build_dir}")
            shutil.rmtree(build_dir)

        print("Clean completed")


setup(
    name="vllm-kubernetes-plugin",
    # Follow:
    # https://packaging.python.org/en/latest/specifications/version-specifiers
    version=VERSION,
    author="MonadKai",
    license="Apache 2.0",
    description=("vLLM Kubernetes plugin"),
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/MonadKai/vllm-kubernetes-plugin",
    project_urls={
        "Homepage": "https://github.com/MonadKai/vllm-kubernetes-plugin",
    },
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=["vllm>=0.5.5", "pynvml>=12.0.0", "pydantic>=2.0.0"],
    extras_require={},
    entry_points={
        "vllm.general_plugins": [
            "vllm_kubernetes_plugin = vllm_kubernetes_plugin:register"
        ],
    },
    cmdclass={
        "build_py": CustomBuildPy,
        "clean": CustomClean,
    },
    # Ensure configuration files are included in distribution package
    package_data={
        "vllm_kubernetes_plugin": ["config/*.py"],
    },
    include_package_data=True,
)
