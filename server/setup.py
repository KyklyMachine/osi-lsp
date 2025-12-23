from setuptools import setup, find_packages

setup(
    name="osi-language-server",
    version="1.0.0",
    description="Language Server for OSI Protocol Language",
    packages=find_packages(),
    install_requires=[
        "pygls>=1.2.0",
        "lsprotocol>=2023.0.0",
        "dataclasses-json>=0.6.0",
        "typing-extensions>=4.8.0"
    ],
    entry_points={
        "console_scripts": [
            "osi-ls=osi_lsp.server:main",
        ],
    },
    python_requires=">=3.10",
)