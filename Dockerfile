FROM python:3.12-slim
WORKDIR /app
RUN useradd --create-home --uid 10001 rag
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
RUN mkdir -p docs db audit && chown -R rag:rag /app
USER rag
CMD ["python", "-m", "src.cli.main"]
