from setuptools import setup, find_packages

setup(
    name="insta_kendou",
    version="1.0.0",
    author="Juana-archer",
    description="Instagram automation tool",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "beautifulsoup4",
        "selenium",
        "cloudscraper",
        "Telethon",
    ],
    python_requires=">=3.6",
)
