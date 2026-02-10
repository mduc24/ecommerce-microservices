# ============================================
# Stage 1: builder - Build dependencies
# ============================================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry via official installer
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /root/.cache

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to create virtualenv in project
RUN poetry config virtualenvs.in-project true

# Install dependencies (no dev dependencies, no root package)
RUN poetry install --only main --no-root


# ============================================
# Stage 2: runtime - Production runtime
# ============================================
FROM python:3.11-slim AS runtime

# Set working directory
WORKDIR /app

# Install wget for health check (not curl)
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app ./app

# Set ownership to app user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Add virtualenv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 3000

# Health check using wget
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Run uvicorn as non-root user
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]


# ============================================
# Stage 3: development - Development environment
# ============================================
FROM python:3.11-slim AS development

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry via official installer
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /root/.cache

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not create virtualenvs (install globally)
RUN poetry config virtualenvs.create false

# Install ALL dependencies (including dev)
RUN poetry install --no-root

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check using wget
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Run with hot reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]
