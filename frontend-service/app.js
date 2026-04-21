const express = require('express');
const axios = require('axios');
const session = require('express-session');
const cookieParser = require('cookie-parser');
const methodOverride = require('method-override');

const app = express();
const PORT = process.env.PORT || 3000;

// Configuración
app.set('view engine', 'ejs');
app.set('views', './views');
app.use(express.static('public'));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(cookieParser());
app.use(methodOverride('_method'));

// Configuración de sesión
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-session-secret',
  resave: false,
  saveUninitialized: false,
  cookie: { secure: false } // Cambiar a true en producción con HTTPS
}));

// URLs de servicios
const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';
const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://localhost:8003';

// Middleware para verificar autenticación
const requireAuth = (req, res, next) => {
  if (!req.session.token) {
    return res.redirect('/login');
  }
  next();
};

// Rutas
app.get('/', (req, res) => {
  if (req.session.token) {
    return res.redirect('/dashboard');
  }
  res.redirect('/login');
});

// Login
app.get('/login', (req, res) => {
  res.render('login', { error: null });
});

app.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    const response = await axios.post(`${API_GATEWAY_URL}/auth/login`, {
      email,
      password
    });

    req.session.token = response.data.access_token;
    req.session.user = response.data.user;

    res.redirect('/dashboard');
  } catch (error) {
    const errorMessage = error.response?.data?.detail || 'Error al iniciar sesión';
    res.render('login', { error: errorMessage });
  }
});

// Registro
app.get('/register', (req, res) => {
  res.render('register', { error: null });
});

app.post('/register', async (req, res) => {
  try {
    const { email, password } = req.body;

    await axios.post(`${API_GATEWAY_URL}/auth/register`, {
      email,
      password
    });

    res.redirect('/login?message=Usuario registrado exitosamente');
  } catch (error) {
    const errorMessage = error.response?.data?.detail || 'Error al registrar usuario';
    res.render('register', { error: errorMessage });
  }
});

// Dashboard
app.get('/dashboard', requireAuth, async (req, res) => {
  try {
    // Obtener órdenes
    const ordersResponse = await axios.get(`${API_GATEWAY_URL}/orders`, {
      headers: { Authorization: `Bearer ${req.session.token}` }
    });

    // Obtener inventario
    const inventoryResponse = await axios.get(`${API_GATEWAY_URL}/inventory`, {
      headers: { Authorization: `Bearer ${req.session.token}` }
    });

    res.render('dashboard', {
      user: req.session.user,
      orders: ordersResponse.data || [],
      inventory: inventoryResponse.data || []
    });
  } catch (error) {
    console.error('Error loading dashboard:', error.message);
    res.render('dashboard', {
      user: req.session.user,
      orders: [],
      inventory: [],
      error: 'Error al cargar los datos'
    });
  }
});

// Crear orden
app.post('/orders', requireAuth, async (req, res) => {
  try {
    const { product_id, quantity } = req.body;

    await axios.post(`${API_GATEWAY_URL}/orders`, {
      product_id: parseInt(product_id),
      quantity: parseInt(quantity)
    }, {
      headers: { Authorization: `Bearer ${req.session.token}` }
    });

    res.redirect('/dashboard?message=Orden creada exitosamente');
  } catch (error) {
    const errorMessage = error.response?.data?.detail || 'Error al crear orden';
    res.redirect(`/dashboard?error=${encodeURIComponent(errorMessage)}`);
  }
});

// Logout
app.post('/logout', (req, res) => {
  req.session.destroy();
  res.redirect('/login');
});

// Health check
app.get('/health', (req, res) => {
  res.json({ service: 'frontend-service', status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Frontend service running on port ${PORT}`);
});