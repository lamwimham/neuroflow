from setuptools import setup, find_packages

setup(
    name="neuroflow-sdk",
    version="0.3.0",
    description="NeuroFlow SDK for building AI agents",
    author="NeuroFlow Team",
    author_email="team@neuroflow.ai",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0",
        "asyncio",
        "pydantic>=2.0.0",
        "grpcio>=1.50.0",
        "protobuf>=4.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        # HTTP client for external calls
        "aiohttp>=3.8.0",
        # OpenAI and Anthropic for LLM support
        "openai>=1.0.0",
        "anthropic>=0.18.0",
        # OpenTelemetry dependencies
        "opentelemetry-api>=1.18.0",
        "opentelemetry-sdk>=1.18.0",
        "opentelemetry-exporter-otlp-proto-http>=1.18.0",
        "opentelemetry-instrumentation-requests>=0.39b0",
        "opentelemetry-instrumentation-logging>=0.39b0",
    ],
    entry_points={
        "console_scripts": [
            "neuroflow=neuroflow.cli.main:main",
        ],
    },
    zip_safe=False,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "click-completion>=0.5.0",
        ],
        "cli": [
            "click>=8.0.0",
            "click-completion>=0.5.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
