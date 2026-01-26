FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # For pyzbar (QR/barcode scanning)
    libzbar0 \
    # For pdf2image
    poppler-utils \
    # For PyMuPDF
    libmupdf-dev \
    mupdf-tools \
    # For building Python packages with C extensions
    build-essential \
    # General utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY api/ ./api/
COPY parsers/ ./parsers/
COPY dtos/ ./dtos/
COPY cli/ ./cli/
COPY services/ ./services/
COPY use_cases/ ./use_cases/
COPY utils/ ./utils/

# Sync dependencies and install
RUN uv sync

# Build the project
RUN uv build

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1
