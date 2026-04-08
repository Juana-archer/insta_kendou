from setuptools import setup, find_packages

setup(
    name="insta_kendou",
    version="1.0.0",
    author="Juana-archer",
    description="Instagram automation tool",
    packages=find_packages(),
    py_modules=[
        "__init__",
        "client",
        "client1", 
        "client2",
        "client_bonne"
    ],
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
