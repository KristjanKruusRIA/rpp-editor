"""
Setup script for RPP Editor package
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="rpp-editor",
    version="3",
    author="RPP Editor Contributors",
    description="A GUI application for editing and comparing REAPER project files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KristjanKruusRIA/rpp-editor",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0", "flake8>=6.0.0"],
    },
    entry_points={
        "console_scripts": [
            "rpp-editor=rpp_editor.gui:main",
        ],
    },
)