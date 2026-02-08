# ============================================
# Stage 1: base - Common base for all stages
# ============================================
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry via official installer
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /root/.cache

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure Poetry to not create virtualenvs
RUN poetry config virtualenvs.create false


# ============================================
# Stage 2: development - Development environment
# ============================================
FROM base AS development

# Install ALL dependencies (including dev) but skip installing current project
RUN poetry install --no-root

# Copy entire application code
COPY . .

# Expose port
EXPOSE 8000

# Run with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ============================================
# Stage 3: production - Production environment
# ============================================
FROM base AS production

# Install ONLY production dependencies
RUN poetry install --only main --no-root

# Copy only app folder
COPY app ./app

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run without reload (performance)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
