# ============================================
# Stage 1: base - Common base for all stages
# ============================================
FROM python:3.11-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && rm -rf /root/.cache

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false
RUN poetry lock


# ============================================
# Stage 2: development - Development environment
# ============================================
FROM base AS development

RUN poetry install --no-root

COPY . .

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]


# ============================================
# Stage 3: production - Production environment
# ============================================
FROM base AS production

RUN poetry install --only main --no-root

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN useradd -m -u 1000 appuser

USER appuser

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
