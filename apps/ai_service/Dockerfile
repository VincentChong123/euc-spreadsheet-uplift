
# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create the working directory
WORKDIR /app

# Copy dependency metadata first so dependency install stays cacheable
COPY pyproject.toml uv.lock ./

# Install Python dependencies into an in-image virtualenv managed by uv
RUN pip install --no-cache-dir uv
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application code
COPY . .

ENV PATH="/app/.venv/bin:${PATH}"

# Port must be explicitly passed by the orchestrator (Cloud Run or Docker Compose)
EXPOSE $PORT

# Run Uvicorn pointing to main.py
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
