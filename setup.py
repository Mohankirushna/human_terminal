from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="hcmd",
    version="0.1.0",
    author="Arvind Nandigam and Mohan Krishna",
    author_email="nandigamarvind@gmail.com",
    description="Convert natural language to terminal commands",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/hcmd",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'hcmd=hcmd.cli:run',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Utilities",
        "Topic :: System :: Shells",
    ],
    python_requires='>=3.7',
    install_requires=[
        # No external dependencies for now
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.7b0',
            'isort>=5.9.0',
            'mypy>=0.910',
            'flake8>=3.9.0',
        ],
    },
)
