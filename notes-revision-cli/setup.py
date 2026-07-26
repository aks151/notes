from setuptools import setup, find_packages

setup(
    name="notes-revision",
    version="1.0.0",
    description="Automated Daily Notes Revision CLI & Email System",
    author="AGY Pair Programmer",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "notes-revision = notes_revision.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
    ],
)
