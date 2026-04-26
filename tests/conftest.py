"""Configuración compartida y fixtures para tests E2E"""
import pytest
import requests
import uuid
from datetime import datetime
from config import settings


@pytest.fixture(scope="session")
def service_urls():
    """URLs de los servicios"""
    return settings.get_service_urls()


@pytest.fixture(scope="session")
def test_credentials():
    """Credenciales de prueba"""
    email = f"test-{datetime.now().timestamp()}@example.com"
    password = settings.get_test_credentials()["password"]
    return {
        "email": email,
        "password": password,
    }


@pytest.fixture
def client():
    """Cliente HTTP con sesión persistente"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


@pytest.fixture
def registered_user(client, service_urls, test_credentials):
    """
    Fixture que registra un usuario y retorna:
    {
        "email": str,
        "password": str,
        "user_id": str (si está disponible)
    }
    """
    email = test_credentials["email"]
    password = test_credentials["password"]
    
    response = client.post(
        f"{service_urls['gateway']}/auth/register",
        json={"email": email, "password": password},
    )
    
    assert response.status_code == 201, f"Registro fallido: {response.text}"
    
    return {
        "email": email,
        "password": password,
    }


@pytest.fixture
def authenticated_user(client, service_urls, registered_user):
    """
    Fixture que hace login y retorna token y claims:
    {
        "token": str (JWT),
        "email": str,
        "password": str,
    }
    """
    email = registered_user["email"]
    password = registered_user["password"]
    
    response = client.post(
        f"{service_urls['gateway']}/auth/login",
        json={"email": email, "password": password},
    )
    
    assert response.status_code == 200, f"Login fallido: {response.text}"
    
    data = response.json()
    token = data.get("access_token")
    assert token, "No se obtuvo token"
    
    return {
        "token": token,
        "email": email,
        "password": password,
    }


@pytest.fixture
def auth_headers(authenticated_user):
    """Headers con token de autenticación"""
    return {
        "Authorization": f"Bearer {authenticated_user['token']}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_skus():
    """SKUs de prueba únicos"""
    timestamp = str(uuid.uuid4())[:8]
    return {
        "sku1": f"SKU-{timestamp}-001",
        "sku2": f"SKU-{timestamp}-002",
        "sku3": f"SKU-{timestamp}-003",
    }
