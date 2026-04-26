FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv sync --no-dev

COPY src/ src/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
