"""Configuración centralizada para tests E2E"""

import os
from typing import Dict


# Detectar si está en Docker o local
IS_DOCKER = os.getenv("DOCKER_ENV", "false").lower() == "true" or os.path.exists(
    "/.dockerenv"
)


class Settings:
    """Configuración de servicios y credenciales"""

    if IS_DOCKER:
        # URLs dentro de Docker (usando nombres de servicios)
        GATEWAY_URL: str = "http://api-gateway:8000"
        AUTH_URL: str = "http://auth-service:8000"
        INVENTORY_URL: str = "http://inventory-service:8000"
        WRITER_URL: str = "http://writer-service:8000"
    else:
        # URLs locales
        GATEWAY_URL: str = "http://localhost:8000"
        AUTH_URL: str = "http://localhost:8003"
        INVENTORY_URL: str = "http://localhost:8002"
        WRITER_URL: str = "http://localhost:8001"

    # Credenciales de prueba
    TEST_EMAIL: str = "test@example.com"
    TEST_PASSWORD: str = "SecurePass123!"

    # Timeouts
    REQUEST_TIMEOUT: int = 30
    HEALTH_CHECK_TIMEOUT: int = 60

    @classmethod
    def get_service_urls(cls) -> Dict[str, str]:
        """Obtener URLs de servicios como diccionario"""
        return {
            "gateway": cls.GATEWAY_URL,
            "auth": cls.AUTH_URL,
            "inventory": cls.INVENTORY_URL,
            "writer": cls.WRITER_URL,
        }

    @classmethod
    def get_test_credentials(cls) -> Dict[str, str]:
        """Obtener credenciales de prueba"""
        return {
            "email": cls.TEST_EMAIL,
            "password": cls.TEST_PASSWORD,
        }


# Instancia global de configuración
settings = Settings()
