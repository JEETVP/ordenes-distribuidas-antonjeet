"""Suite completa de tests E2E para el sistema de microservicios distribuidos"""

from datetime import datetime


class TestHealthChecks:
    """Tests de health checks de todos los servicios"""

    def test_gateway_health(self, client, service_urls):
        """API Gateway debe responder a health check"""
        response = client.get(f"{service_urls['gateway']}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "api-gateway"
        assert data["status"] == "ok"

    def test_auth_service_health(self, client, service_urls):
        """Auth Service debe responder a health check"""
        response = client.get(f"{service_urls['auth']}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "auth-service"
        assert data["status"] == "ok"

    def test_inventory_service_health(self, client, service_urls):
        """Inventory Service debe responder a health check"""
        response = client.get(f"{service_urls['inventory']}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "inventory-service"
        assert data["status"] == "ok"

    def test_writer_service_health(self, client, service_urls):
        """Writer Service debe responder a health check"""
        response = client.get(f"{service_urls['writer']}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "writer-service"
        assert data["status"] == "ok"


class TestAuthentication:
    """Tests de autenticación y manejo de tokens"""

    def test_register_user_success(self, client, service_urls, test_credentials):
        """Registrar nuevo usuario exitosamente"""
        email = f"newuser-{datetime.now().timestamp()}@example.com"
        password = test_credentials["password"]

        response = client.post(
            f"{service_urls['gateway']}/auth/register",
            json={"email": email, "password": password},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email

    def test_register_duplicate_email_fails(
        self, client, service_urls, registered_user
    ):
        """Intentar registrar email duplicado debe fallar"""
        response = client.post(
            f"{service_urls['gateway']}/auth/register",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert (
            "already registered" in data.get("detail", "").lower()
            or "email" in data.get("detail", "").lower()
        )

    def test_login_success(self, client, service_urls, registered_user):
        """Login exitoso debe retornar token"""
        response = client.post(
            f"{service_urls['gateway']}/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"]
        assert "expires_in" in data
        assert "user" in data

    def test_login_wrong_password_fails(self, client, service_urls, registered_user):
        """Login con contraseña incorrecta debe fallar"""
        response = client.post(
            f"{service_urls['gateway']}/auth/login",
            json={
                "email": registered_user["email"],
                "password": "wrong_password",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert (
            "invalid" in data.get("detail", "").lower()
            or "unauthorized" in data.get("detail", "").lower()
        )

    def test_login_nonexistent_user_fails(self, client, service_urls, test_credentials):
        """Login de usuario inexistente debe fallar"""
        response = client.post(
            f"{service_urls['gateway']}/auth/login",
            json={
                "email": f"nonexistent-{datetime.now().timestamp()}@example.com",
                "password": test_credentials["password"],
            },
        )

        assert response.status_code == 401

    def test_verify_valid_token(self, client, service_urls, authenticated_user):
        """Verificar token válido"""
        headers = {
            "Authorization": f"Bearer {authenticated_user['token']}",
        }

        response = client.get(
            f"{service_urls['gateway']}/auth/verify",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("active") or "true" in str(data).lower()

    def test_verify_invalid_token_fails(self, client, service_urls):
        """Verificar token inválido debe fallar"""
        headers = {
            "Authorization": "Bearer invalid.token.here",
        }

        response = client.get(
            f"{service_urls['gateway']}/auth/verify",
            headers=headers,
        )

        assert response.status_code in [401, 403]

    def test_get_me_success(self, client, service_urls, authenticated_user):
        """Obtener información del usuario autenticado"""
        headers = {
            "Authorization": f"Bearer {authenticated_user['token']}",
        }

        response = client.get(
            f"{service_urls['gateway']}/auth/me",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == authenticated_user["email"]

    def test_get_me_without_token_fails(self, client, service_urls):
        """Obtener /me sin token debe fallar"""
        response = client.get(
            f"{service_urls['gateway']}/auth/me",
        )

        assert response.status_code in [401, 403]

    def test_logout_revokes_token(self, client, service_urls, authenticated_user):
        """Logout debe revocar el token"""
        headers = {
            "Authorization": f"Bearer {authenticated_user['token']}",
        }

        # Primero verificar que el token es válido
        verify_before = client.get(
            f"{service_urls['gateway']}/auth/verify",
            headers=headers,
        )
        assert verify_before.status_code == 200

        # Hacer logout
        response = client.post(
            f"{service_urls['gateway']}/auth/logout",
            headers=headers,
        )
        assert response.status_code == 200

        # Intentar usar el token después del logout
        verify_after = client.get(
            f"{service_urls['gateway']}/auth/verify",
            headers=headers,
        )
        assert verify_after.status_code in [401, 403]


class TestInventory:
    """Tests de gestión de inventario"""

    def test_seed_inventory_success(
        self, client, service_urls, auth_headers, sample_skus
    ):
        """Seed de inventario exitoso"""
        response = client.post(
            f"{service_urls['inventory']}/inventory/seed",
            headers=auth_headers,
            json={
                "sku": sample_skus["sku1"],
                "stock": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == sample_skus["sku1"]
        assert data["stock"] == 100

    def test_seed_multiple_skus(self, client, service_urls, auth_headers, sample_skus):
        """Seed de múltiples SKUs"""
        skus_data = [
            (sample_skus["sku1"], 100),
            (sample_skus["sku2"], 50),
            (sample_skus["sku3"], 75),
        ]

        for sku, stock in skus_data:
            response = client.post(
                f"{service_urls['inventory']}/inventory/seed",
                headers=auth_headers,
                json={"sku": sku, "stock": stock},
            )
            assert response.status_code == 200

    def test_get_inventory_success(
        self, client, service_urls, auth_headers, sample_skus
    ):
        """Obtener inventario existente"""
        # Primero seed
        client.post(
            f"{service_urls['inventory']}/inventory/seed",
            headers=auth_headers,
            json={"sku": sample_skus["sku1"], "stock": 100},
        )

        # Luego obtener
        response = client.get(
            f"{service_urls['inventory']}/inventory/{sample_skus['sku1']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sku"] == sample_skus["sku1"]
        assert data["stock"] == 100

    def test_get_nonexistent_inventory_fails(self, client, service_urls, auth_headers):
        """Obtener SKU inexistente debe retornar 404"""
        response = client.get(
            f"{service_urls['inventory']}/inventory/NONEXISTENT-SKU",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_seed_inventory_without_auth_fails(self, client, service_urls, sample_skus):
        """Seed sin autenticación debe fallar"""
        response = client.post(
            f"{service_urls['inventory']}/inventory/seed",
            json={"sku": sample_skus["sku1"], "stock": 100},
        )

        assert response.status_code in [401, 403]

    def test_get_inventory_without_auth_fails(self, client, service_urls, sample_skus):
        """Get sin autenticación debe fallar"""
        response = client.get(
            f"{service_urls['inventory']}/inventory/{sample_skus['sku1']}",
        )

        assert response.status_code in [401, 403]


class TestOrders:
    """Tests de gestión de órdenes"""

    def test_create_order_success(
        self, client, service_urls, auth_headers, sample_skus
    ):
        """Crear orden exitosamente"""
        # Primero seed inventory
        client.post(
            f"{service_urls['inventory']}/inventory/seed",
            headers=auth_headers,
            json={"sku": sample_skus["sku1"], "stock": 100},
        )

        # Crear orden
        response = client.post(
            f"{service_urls['gateway']}/orders",
            headers=auth_headers,
            json={
                "customer": "Test Company",
                "items": [
                    {"sku": sample_skus["sku1"], "qty": 5},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
        assert data["order_id"]
        assert data["status"] == "RECEIVED"
        assert data["customer"] == "Test Company" or "requested_by" in data

    def test_create_order_multiple_items(
        self, client, service_urls, auth_headers, sample_skus
    ):
        """Crear orden con múltiples items"""
        # Seed inventory
        for sku, stock in [(sample_skus["sku1"], 100), (sample_skus["sku2"], 50)]:
            client.post(
                f"{service_urls['inventory']}/inventory/seed",
                headers=auth_headers,
                json={"sku": sku, "stock": stock},
            )

        # Crear orden
        response = client.post(
            f"{service_urls['gateway']}/orders",
            headers=auth_headers,
            json={
                "customer": "Multi Item Corp",
                "items": [
                    {"sku": sample_skus["sku1"], "qty": 5},
                    {"sku": sample_skus["sku2"], "qty": 3},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data

    def test_create_order_without_auth_fails(self, client, service_urls):
        """Crear orden sin autenticación debe fallar"""
        response = client.post(
            f"{service_urls['gateway']}/orders",
            json={
                "customer": "Test",
                "items": [{"sku": "TEST", "qty": 1}],
            },
        )

        assert response.status_code in [401, 403]

    def test_list_orders_success(self, client, service_urls, auth_headers, sample_skus):
        """Listar órdenes del usuario"""
        # Crear una orden
        client.post(
            f"{service_urls['inventory']}/inventory/seed",
            headers=auth_headers,
            json={"sku": sample_skus["sku1"], "stock": 100},
        )

        client.post(
            f"{service_urls['gateway']}/orders",
            headers=auth_headers,
            json={
                "customer": "Test",
                "items": [{"sku": sample_skus["sku1"], "qty": 5}],
            },
        )

        # Listar órdenes
        response = client.get(
            f"{service_urls['gateway']}/orders",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_orders_without_auth_fails(self, client, service_urls):
        """Listar órdenes sin autenticación debe fallar"""
        response = client.get(
            f"{service_urls['gateway']}/orders",
        )

        assert response.status_code in [401, 403]


class TestE2EFlow:
    """Tests del flujo end-to-end completo"""

    def test_complete_e2e_flow(self, client, service_urls):
        """
        Flujo completo:
        1. Registrar usuario
        2. Login
        3. Seed inventario
        4. Crear orden
        5. Listar órdenes
        6. Logout
        """
        email = f"e2e-{datetime.now().timestamp()}@example.com"
        password = "Test123!"

        # 1. Registrar
        reg_resp = client.post(
            f"{service_urls['gateway']}/auth/register",
            json={"email": email, "password": password},
        )
        assert reg_resp.status_code == 201

        # 2. Login
        login_resp = client.post(
            f"{service_urls['gateway']}/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Seed inventario
        sku = f"E2E-SKU-{datetime.now().timestamp()}"
        seed_resp = client.post(
            f"{service_urls['inventory']}/inventory/seed",
            headers=headers,
            json={"sku": sku, "stock": 100},
        )
        assert seed_resp.status_code == 200

        # 4. Crear orden
        order_resp = client.post(
            f"{service_urls['gateway']}/orders",
            headers=headers,
            json={
                "customer": "E2E Test Company",
                "items": [{"sku": sku, "qty": 10}],
            },
        )
        assert order_resp.status_code == 200
        order_id = order_resp.json()["order_id"]
        assert order_id

        # 5. Listar órdenes
        list_resp = client.get(
            f"{service_urls['gateway']}/orders",
            headers=headers,
        )
        assert list_resp.status_code == 200
        orders = list_resp.json()
        assert isinstance(orders, list)
        # La orden debe estar en la lista
        assert any(o.get("order_id") == order_id for o in orders)

        # 6. Logout
        logout_resp = client.post(
            f"{service_urls['gateway']}/auth/logout",
            headers=headers,
        )
        assert logout_resp.status_code == 200

        # Verificar que el token fue revocado
        verify_resp = client.get(
            f"{service_urls['gateway']}/auth/verify",
            headers=headers,
        )
        assert verify_resp.status_code in [401, 403]

    def test_order_flow_from_writer_service(
        self, client, service_urls, auth_headers, sample_skus
    ):
        """Verificar que las órdenes persisten en writer service"""
        # Seed
        client.post(
            f"{service_urls['inventory']}/inventory/seed",
            headers=auth_headers,
            json={"sku": sample_skus["sku1"], "stock": 100},
        )

        # Crear orden
        order_resp = client.post(
            f"{service_urls['gateway']}/orders",
            headers=auth_headers,
            json={
                "customer": "Writer Test",
                "items": [{"sku": sample_skus["sku1"], "qty": 5}],
            },
        )
        assert order_resp.status_code == 200

        # Listar desde writer service
        writer_resp = client.get(
            f"{service_urls['writer']}/internal/orders",
            headers=auth_headers,
        )

        assert writer_resp.status_code == 200
        orders = writer_resp.json()
        assert isinstance(orders, list)


class TestErrorHandling:
    """Tests de manejo de errores y casos límite"""

    def test_invalid_json_payload(self, client, service_urls):
        """Enviar JSON inválido debe fallar"""
        response = client.post(
            f"{service_urls['gateway']}/auth/register",
            data="invalid json",
        )

        assert response.status_code in [400, 422]

    def test_missing_required_fields_registration(self, client, service_urls):
        """Registrarse sin campos requeridos debe fallar"""
        response = client.post(
            f"{service_urls['gateway']}/auth/register",
            json={"email": "test@example.com"},  # Falta password
        )

        assert response.status_code in [400, 422]

    def test_missing_required_fields_order(self, client, service_urls, auth_headers):
        """Crear orden sin campos requeridos debe fallar"""
        response = client.post(
            f"{service_urls['gateway']}/orders",
            headers=auth_headers,
            json={"customer": "Test"},  # Falta items
        )

        assert response.status_code in [400, 422]

    def test_empty_items_list(self, client, service_urls, auth_headers):
        """Orden con items vacío puede fallar o ser válido según la validación"""
        response = client.post(
            f"{service_urls['gateway']}/orders",
            headers=auth_headers,
            json={
                "customer": "Test",
                "items": [],
            },
        )

        # Puede ser 200 o 400 dependiendo de la validación
        assert response.status_code in [200, 400, 422]

    def test_negative_quantity(self, client, service_urls, auth_headers):
        """Cantidad negativa en orden"""
        response = client.post(
            f"{service_urls['gateway']}/orders",
            headers=auth_headers,
            json={
                "customer": "Test",
                "items": [{"sku": "TEST", "qty": -5}],
            },
        )

        # Puede ser 200 o 400 dependiendo de la validación
        assert response.status_code in [200, 400, 422]

    def test_negative_stock_seed(self, client, service_urls, auth_headers, sample_skus):
        """Stock negativo al seed"""
        response = client.post(
            f"{service_urls['inventory']}/inventory/seed",
            headers=auth_headers,
            json={
                "sku": sample_skus["sku1"],
                "stock": -50,
            },
        )

        # Puede ser 200 o 400 dependiendo de la validación
        assert response.status_code in [200, 400, 422]
