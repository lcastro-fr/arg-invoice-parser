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
COPY main.py __init__.py core.py run-batch.py ./
COPY parsers/ ./parsers/
COPY dtos/ ./dtos/
COPY tests/ ./tests/

# Install uv package manager
RUN uv sync

# Create directory for input PDFs
RUN mkdir -p /app/invoices

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden in docker-compose or at runtime)
ENTRYPOINT ["uv","run"]
CMD ["main.py", "--help"]
