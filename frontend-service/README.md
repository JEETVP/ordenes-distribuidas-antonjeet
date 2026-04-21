# Frontend Service

Servicio frontend web para el sistema distribuido de órdenes.

## Características

- **Interfaz web moderna** con Bootstrap 5
- **Autenticación JWT** integrada
- **Dashboard completo** con órdenes e inventario
- **Responsive design** para móviles y desktop
- **Sesiones seguras** con express-session

## URLs

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Auth Service**: http://localhost:8003

## Funcionalidades

### Páginas disponibles:
- `/login` - Iniciar sesión
- `/register` - Registro de usuarios
- `/dashboard` - Panel principal (requiere autenticación)
- `/logout` - Cerrar sesión

### Dashboard incluye:
- **Crear órdenes** nuevas
- **Ver órdenes recientes**
- **Consultar inventario** disponible
- **Gestión de sesión** de usuario

## Uso

1. **Levantar todos los servicios:**
```bash
docker compose up --build
```

2. **Acceder al frontend:**
   - Abre http://localhost:3000 en tu navegador

3. **Flujo de uso:**
   - Regístrate con email y contraseña
   - Inicia sesión
   - Crea órdenes desde el dashboard
   - Ve el inventario y órdenes recientes

## Variables de entorno

```yaml
API_GATEWAY_URL: URL del API Gateway (default: http://api-gateway:8000)
AUTH_SERVICE_URL: URL del Auth Service (default: http://auth-service:8003)
SESSION_SECRET: Clave secreta para sesiones (default: your-frontend-session-secret)
PORT: Puerto del frontend (default: 3000)
```

## Tecnologías

- **Express.js** - Framework web
- **EJS** - Motor de templates
- **Bootstrap 5** - Framework CSS
- **Axios** - Cliente HTTP
- **express-session** - Gestión de sesiones