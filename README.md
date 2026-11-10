# Bank Hub

Agregador personal de cuentas bancarias construido con Python/Flask y la API de [Enable Banking](https://enablebanking.com). Muestra saldos y movimientos de tus cuentas en un único dashboard.

> **Estado:** MVP funcional. Uso personal en red local, banco sandbox Nordea Finlandia.

---

## Requisitos previos

- Python 3.10+
- Una cuenta en Enable Banking con:
  - `applicationId` (UUID de tu aplicación)
  - Clave privada RSA en un archivo `.pem`
  - Redirect URL registrada como `http://localhost:8080/auth_redirect`

---

## Instalación

```bash
# 1. Clona el repositorio
git clone <repo-url>
cd bank-hub

# 2. Crea y activa un entorno virtual
python -m venv venv
source venv/bin/activate       # Linux/Mac
# venv\Scripts\activate        # Windows

# 3. Instala dependencias
pip install flask werkzeug pyjwt requests cryptography
```

---

## Configuración

Crea el archivo `config.json` en la raíz del proyecto:

```json
{
  "applicationId": "tu-application-id-uuid",
  "keyPath": "private.pem",
  "redirectUrl": "http://localhost:8080/auth_redirect"
}
```

Coloca tu clave privada RSA en `private.pem` (o la ruta que hayas indicado en `keyPath`).

---

## Ejecución

```bash
python app.py
```

La app arranca en `http://localhost:8080`.

> **Importante:** Usar `localhost` (no `127.0.0.1`) para que la cookie de sesión funcione correctamente con el redirect de Enable Banking.

---

## Flujo de uso

### Primera vez

```
Usuario abre /login
  → Introduce usuario y contraseña
  → Se crea el usuario en la BD (hash de contraseña)
  → No hay sesión bancaria → redirige a Enable Banking
  → Usuario autoriza en el banco (sandbox Nordea)
  → Enable Banking redirige a /auth_redirect?code=XXX
  → Se crea la sesión bancaria y se guarda en la BD
  → Redirige a /sincronizar → descarga cuentas y movimientos
  → Dashboard con datos
```

### Siguientes accesos

```
Usuario abre /login
  → Introduce credenciales → verificación con hash
  → Ya hay sesión bancaria → redirige directamente al dashboard
  → Dashboard carga datos desde SQLite (sin llamadas a la API)
```

### Sincronizar

Pulsa el botón **"Actualizar datos del banco"** en el dashboard:
```
/sincronizar
  → Llama a Enable Banking API
  → Actualiza saldos de cada cuenta
  → Descarga movimientos (últimos 90 días, paginados)
  → Guarda sólo los movimientos nuevos (deduplicación)
  → Redirige al dashboard actualizado
```

---

## Arquitectura

El proyecto sigue una separación en 3 capas:

```
┌─────────────────────────────────────────────┐
│  Routes (routes/)                           │  ← HTTP: recibe peticiones, devuelve respuestas
│  auth.py · dashboard.py                     │
└───────────────┬─────────────────────────────┘
                │ llama a
       ┌────────┴──────────────┐
       │                       │
┌──────▼──────┐       ┌────────▼────────┐
│  Models     │       │  Services       │
│ database.py │       │ enable_banking  │
│             │       │ .py             │
│ SQLite CRUD │       │ API calls       │
└─────────────┘       └─────────────────┘
```

| Capa | Responsabilidad | No sabe nada de... |
|------|-----------------|--------------------|
| **Routes** | Leer request, llamar a models/services, devolver response | SQLite, Enable Banking API |
| **Models** | Leer y escribir en SQLite | Flask, Enable Banking |
| **Services** | Llamar a la API de Enable Banking | Flask, SQLite |

---

## Esquema de base de datos

```
usuario
  id · nombre · password_hash

sesiones_banco                       (FK → usuario)
  id · usuario_id · banco · sesion_id · expira_en

cuentas                              (FK → sesiones_banco)
  id · sesiones_banco_id · uid_enablebanking · nombre · saldo · moneda

detalles_movimientos                 (FK → cuentas)
  id · cuenta_id · fecha · importe · direccion · descripcion · contraparte · moneda
```

**`direccion`** vale `"ingreso"` (CRDT) o `"gasto"` (DBIT).

---

## Estructura de archivos

```
bank-hub/
├── app.py                      # Punto de entrada Flask, registra blueprints
├── config.json                 # Credenciales Enable Banking (no subir a git)
├── private.pem                 # Clave privada RSA (no subir a git)
├── database.db                 # SQLite (generado automáticamente)
├── routes/
│   ├── auth.py                 # /login  /auth_redirect
│   └── dashboard.py            # /dashboard  /sincronizar
├── models/
│   └── database.py             # Todas las funciones SQLite
├── services/
│   └── enable_banking.py       # JWT + llamadas a la API
└── templates/
    ├── login.html
    └── dashboard.html
```

---

## Autenticación con Enable Banking

Cada llamada a la API incluye un JWT firmado con tu clave RSA privada:

```
Header:  { "alg": "RS256", "kid": "<applicationId>" }
Payload: { "iss": "enablebanking.com",
           "aud": "api.enablebanking.com",
           "iat": <ahora>,
           "exp": <ahora + 1h> }
```

El token se genera en cada petición (`jwt()` en `services/enable_banking.py`).

---

## Dos tipos de sesión

| Sesión | Dónde vive | Qué representa |
|--------|-----------|----------------|
| **Flask session** | Cookie del navegador | Usuario autenticado localmente (`session['usuario_id']`) |
| **Enable Banking session** | Tabla `sesiones_banco` en SQLite | Autorización del usuario en su banco (válida 10 días) |

Son independientes: puedes cerrar y abrir el navegador y la sesión bancaria sigue activa.

---

## Deduplicación de movimientos

Al sincronizar, antes de insertar cada movimiento se comprueba si ya existe:

```sql
SELECT id FROM detalles_movimientos
WHERE cuenta_id = ? AND fecha = ? AND importe = ? AND descripcion = ?
```

Si ya existe, se omite. Así `/sincronizar` es idempotente: puedes llamarlo N veces sin duplicar datos.

---

## Limitaciones conocidas

- **Un solo usuario:** `user_exists()` sólo comprueba si hay algún usuario, no admite múltiples cuentas.
- **Sin logout:** No hay ruta `/logout` para destruir la sesión Flask.
- **Sesión bancaria fija 10 días:** Al expirar hay que re-autenticar manualmente (eliminar la fila de `sesiones_banco` y volver a hacer login).
- **Sandbox únicamente:** Configurado para Nordea Finlandia en entorno de pruebas de Enable Banking.
- **Sin CSS:** El dashboard muestra HTML plano sin estilos.
- **`SECRET_KEY` hardcodeada:** Para producción real habría que moverla a variable de entorno.

---

## Añadir a `.gitignore`

```
config.json
private.pem
database.db
venv/
__pycache__/
*.pyc
```
