"""
Setup script for todo-cli
"""
from setuptools import setup, find_packages

setup(
    name="todo-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "todo=todo_cli.main:app",
        ],
    },
    python_requires=">=3.9",
)
