# Bank-Hub — Documento de planificación

Referencia interna de diseño para consultar mientras construyo el proyecto.

---

## ¿Qué es esto?

Una herramienta personal alojada en mi portátil, accesible desde cualquier dispositivo de mi red doméstica, que muestra en un mismo lugar la información de todas mis cuentas bancarias con mis claves, sin depender de terceros.

---

## MVP — Lo que se construye primero

El objetivo del MVP es hacer algo que funcione y se pueda ver, sin complicar demasiado para no acabar abandonando el proyecto.

**Qué incluye el MVP:**
- Login con usuario y contraseña
- Conexión a cuentas **simuladas** de Enable Banking (sandbox), no cuentas reales todavía
- Pantalla con el resumen de saldos de todas las cuentas
- Pantalla con los últimos movimientos
- Accesible solo desde la red doméstica

**Qué NO incluye el MVP (para más adelante):**
- Cuentas bancarias reales
- Acceso desde fuera de casa (internet)
- Otros analiticas con la información de las cuentas

---

## Tecnologías elegidas

| Qué | Herramienta | Por qué |
|-----|-------------|---------|
| Lenguaje | Python | Conocido y el ejemplo de Enable Banking está en Python |
| Backend / servidor | Flask | Sencillo, hace poco "por magia", bueno para aprender |
| Base de datos | SQLite | No necesita servidor separado, es un fichero, ya la he usado |
| Frontend | HTML/CSS + Jinja2 | Jinja2 es el sistema de plantillas de Flask: mezcla HTML con datos de Python |
| API bancaria | Enable Banking | Agregador que habla con muchos bancos con una sola API |

---

## ¿Qué es Enable Banking?

Una capa intermedia que permite hablar con muchos bancos distintos usando una sola API. En lugar de integrarse con Santander, luego BBVA, luego Nordea... se habla solo con Enable Banking y ellos se encargan del resto.

Los bancos en su jerga se llaman **ASPSPs**.

### Cómo funciona la autenticación con el banco (flujo OAuth)

Hay **dos flujos de autenticación distintos** que no hay que confundir:

```
Flujo 1: YO → mi app     (login con usuario/contraseña)
Flujo 2: YO → mi banco   (doy permiso a Enable Banking para leer mis cuentas)
```

El Flujo 2 pasa por el banco — la app redirige al usuario a la web del banco, el usuario da permiso, y el banco redirige de vuelta a la app con un código. Ese código se intercambia por una **sesión bancaria** (un `session_id`) que permite hacer llamadas a la API.

Esa sesión tiene fecha de caducidad. Para el proyecto real, se renovará cada ~30 días.

---

## Pantallas y rutas

| Ruta | Qué hace | ¿El usuario la ve? |
|------|----------|-------------------|
| `/login` | Formulario de login | ✅ Sí |
| `/dashboard` | Saldos y movimientos de todas las cuentas | ✅ Sí |
| `/auth_redirect` | Recibe el código del banco tras el Flujo 2 | ❌ Solo de paso |

---

## Flujo de usuario completo

```
Usuario abre la app
        ↓
¿Está logueado en la app?
    NO → /login → introduce contraseña → login correcto
        ↓
¿Hay sesión activa con Enable Banking?
    NO → inicia Flujo 2 con el banco → usuario da permiso → /auth_redirect → sesión creada
        ↓
/dashboard → muestra saldos y movimientos
```

Si ya está logueado Y ya tiene sesión bancaria activa → va directo al dashboard.
La sesión con el banco se inicia automáticamente al hacer login si no existe.

---

## Estructura de ficheros prevista

```
bank-hub/
├── app.py                  ← punto de entrada, arranca Flask
├── config.json             ← claves de Enable Banking (no subir a git)
├── database.db             ← fichero SQLite (no subir a git)
│
├── routes/                 ← "recepción": reciben peticiones del navegador
│   ├── auth.py             ← rutas de login/logout
│   └── dashboard.py        ← rutas de la pantalla principal
│
├── services/               ← "departamentos": hacen el trabajo real
│   └── enable_banking.py   ← toda la lógica de comunicación con Enable Banking
│
├── models/                 ← estructura y acceso a la base de datos
│   └── database.py
│
├── templates/              ← ficheros HTML (Jinja2)
│   ├── login.html
│   └── dashboard.html
│
└── static/                 ← CSS, imágenes, etc.
    └── style.css
```

> Las rutas reciben la petición y llaman a los servicios.  
> Los servicios hacen el trabajo y no saben nada del navegador.  
> Los modelos gestionan la base de datos y no saben nada de la API.

---

## Base de datos — Esquema

Las relaciones son **uno a muchos** encadenadas:

```
usuario → tiene muchas → sesiones_banco
sesión_banco → tiene muchas → cuentas
cuenta → tiene muchos → movimientos
```

### Tabla `usuario`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| nombre | TEXT | Nombre de usuario |
| password_hash | TEXT | Contraseña hasheada (nunca en texto plano) |

### Tabla `sesiones_banco`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| usuario_id | INTEGER | → apunta a `usuario` |
| banco | TEXT | Nombre del banco (ej: "Nordea", "Santander") |
| session_id | TEXT | ID de sesión que devuelve Enable Banking |
| expira_en | TEXT | Fecha de caducidad de la sesión |

### Tabla `cuentas`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| sesion_banco_id | INTEGER | → apunta a `sesiones_banco` |
| uid_enablebanking | TEXT | UID que Enable Banking asigna a la cuenta (necesario para llamar a la API) |
| nombre | TEXT | Nombre o alias de la cuenta |
| saldo | REAL | Saldo actual |
| moneda | TEXT | Ej: "EUR" |

### Tabla `movimientos`
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | INTEGER | Clave primaria |
| cuenta_id | INTEGER | → apunta a `cuentas` |
| fecha | TEXT | Fecha del movimiento |
| importe | REAL | Cantidad (siempre positiva) |
| direccion | TEXT | "entrada" o "salida" |
| descripcion | TEXT | Asunto / concepto del movimiento |
| contraparte | TEXT | Nombre del remitente o receptor |
| moneda | TEXT | Ej: "EUR" |

---

## Módulos — Separación de responsabilidades

Cada módulo tiene una sola razón para existir:

- **`routes/auth.py`** — gestiona el login y logout del usuario en la app
- **`routes/dashboard.py`** — gestiona qué se muestra en pantalla
- **`services/enable_banking.py`** — toda la comunicación con Enable Banking (autenticación con el banco, obtener cuentas, saldos y movimientos)
- **`models/database.py`** — leer y escribir en SQLite

Las rutas llaman a los servicios. Los servicios llaman a los modelos. Cada capa ignora los detalles de las demás.

