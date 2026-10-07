FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first so this layer is cached until requirements.txt changes
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Install the package itself (pyproject uses the uv_build backend)
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .

# One-off scripts used by CronJobs / init jobs (data/ is not in git, mount it at runtime)
COPY schema.sql load_to_postgres.py ./

# Run as a non-root user
RUN useradd --create-home app && chown -R app /app
USER app

# Override the command per workload, e.g.:
#   onsen-scrawler <seed-url> --max-pages 10
#   python load_to_postgres.py
#   onsen-scrawler-mcp
CMD ["onsen-scrawler", "--help"]
