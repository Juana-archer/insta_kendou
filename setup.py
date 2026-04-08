from setuptools import setup, find_packages

setup(
    name="insta_kendou",
    version="1.0.0",
    author="juana_archer",
    description="Instagram automation tool",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
    ],
    python_requires=">=3.6",
)
