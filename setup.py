from setuptools import find_packages, setup
import os

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

setup(
    name="vllm-kubernetes-plugin",
    # Follow:
    # https://packaging.python.org/en/latest/specifications/version-specifiers
    version=VERSION,
    author="bairong-inc AI infra team",
    license="Apache 2.0",
    description=("vLLM Kubernetes plugin"),
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="http://git.100credit.cn/kai.liu/vllm-kubernetes-plugin",
    project_urls={
        "Homepage": "http://git.100credit.cn/kai.liu/vllm-kubernetes-plugin",
    },
    # TODO: Add 3.12 back when torch-npu support 3.12
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    packages=find_packages(exclude=("docs", "examples", "tests*", "csrc")),
    package_dir={"vllm_kubernetes_plugin": "src"},
    python_requires=">=3.9",
    install_requires=["vllm>=0.5.5", "pynvml>=12.0.0"],
    extras_require={},
    entry_points={
        "vllm.general_plugins":
        ["vllm_kubernetes_plugin = vllm_kubernetes_plugin:register"],
    },
)
