from setuptools import setup, find_packages

setup(
    name="lunuz-tools",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "lunuz=lunuz.cli:main",
        ],
    },
    description="lunuz tools - A collection of Linux-like command line utilities",
    python_requires=">=3.8",
)