from setuptools import setup, find_packages

setup(
    name="ai-kustomize-agent",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'ai-kustomize=src.main:main',
        ],
    },
    install_requires=[
        "kubernetes>=28.1.0",
        "google-generativeai>=0.3.0",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0",
    ],
)
