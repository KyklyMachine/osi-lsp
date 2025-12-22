from setuptools import setup, find_packages

setup(
    name="protocol-language-server",
    version="0.1.0",
    description="Language Server for Protocol Language",
    packages=find_packages(),
    install_requires=[
        "pygls>=1.3.0",
        "lsprotocol>=2023.0.0",
    ],
    entry_points={
        "console_scripts": [
            "protocol-ls=protocol_ls.server:main",
        ],
    },
    python_requires=">=3.8",
)
