FROM python:3.11-slim

WORKDIR /app/tests

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements-test.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements-test.txt

# Copiar código de tests
COPY tests/conftest.py .
COPY tests/test_e2e.py .
COPY tests/config.py .
COPY tests/__init__.py .
COPY tests/pytest.ini .

# Marcar que estamos en Docker
ENV DOCKER_ENV=true

# Health check para verificar que pytest está listo
HEALTHCHECK --interval=5s --timeout=3s --start-period=2s --retries=3 \
    CMD python -c "import pytest; print('ready')" || exit 1

# Comando por defecto: ejecutar pytest
ENTRYPOINT ["pytest"]
CMD ["test_e2e.py", "-v", "--tb=short"]
