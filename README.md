# Bank Hub

Agregador personal de finanzas y patrimonio construido con Python/Flask y la API de [Enable Banking](https://enablebanking.com). Combina sincronización automática de cuentas bancarias mediante Open Banking (PSD2) con soporte para importación y registro de productos de inversión y depósitos.

> [!NOTE]
> **Enfoque del proyecto:** El objetivo principal de este desarrollo es el aprendizaje y profundización en **backend** (Python, Flask, SQLite, integración de APIs bancarias con OAuth/PSD2, seguridad de datos, algoritmos de conciliación contable y gestión híbrida de datos bancarios/inversión). La interfaz visual y los estilos de frontend (HTML/CSS) han sido delegados a agentes de IA, ya que el diseño frontend no es una prioridad para mí en este proyecto.

> **Estado:** Arquitectura híbrida en desarrollo (sincronización automática de banca del día a día en producción, conciliación de transferencias internas, categorización de gastos y soporte de importación/registro para inversiones).

---

## Requisitos previos

- Python 3.10+
- Certificado SSL local (`cert.pem` + `key.pem`) para HTTPS — necesario para el redirect de banca real española (Redsys)
- Una cuenta en [Enable Banking](https://enablebanking.com) con:
  - `applicationId` (UUID de tu aplicación)
  - Clave privada RSA en un archivo `.pem`
  - Redirect URL registrada como `https://localhost:8080/auth_redirect`

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
  "keyPath": "tu-clave-privada.pem",
  "redirectUrl": "https://localhost:8080/auth_redirect",
  "aspspName": "Nombre del Banco en Enable Banking",
  "aspspCountry": "ES",
  "secretKey": "cadena-larga-y-aleatoria-para-firmar-cookies"
}
```

Coloca tu clave privada RSA en el archivo indicado en `keyPath`.

> [!IMPORTANT]
> `config.json` y los archivos `.pem` están en `.gitignore`. Nunca los subas al repositorio.

---

## Ejecución

```bash
python app.py
```

La app arranca en `https://localhost:8080` (HTTPS con certificado autofirmado).

> [!NOTE]
> Al usar un certificado autofirmado, el navegador mostrará un aviso de seguridad la primera vez. Pulsa **"Avanzado → Continuar de todos modos"** para acceder. Esto es normal en entorno local.

> **Importante:** Usar `localhost` (no `127.0.0.1`) para que la cookie de sesión funcione correctamente con el redirect de Enable Banking.

---

## Flujo de uso

### Primera vez

```
Usuario abre /login
  → Introduce usuario y contraseña
  → Se crea el usuario en la BD (hash de contraseña)
  → No hay sesión bancaria → redirige a Enable Banking
  → Usuario autoriza en el banco (banca real española vía PSD2)
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
  → Descarga movimientos (últimos 89 días, límite PSD2 Redsys)
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
  id · sesiones_banco_id · uid_enablebanking · nombre · saldo · moneda · tipo_cuenta

detalles_movimientos                 (FK → cuentas)
  id · cuenta_id · fecha · importe · direccion · descripcion · contraparte · moneda · categoria
```

**`tipo_cuenta`** vale `"corriente"`, `"ahorros"` o `"inversion"`.

**`direccion`** vale `"ingreso"` (CRDT), `"gasto"` (DBIT) o `"transferencia_interna"` (traspaso entre cuentas propias).

**`categoria`** vale `"Gasolina"`, `"Otros"` u otras categorías definidas en `services/categorizacion.py`.

---

## Estructura de archivos

```
bank-hub/
├── app.py                      # Punto de entrada Flask, registra blueprints
├── config.json                 # Credenciales Enable Banking + SECRET_KEY (no subir a git)
├── tu-clave-privada.pem        # Clave privada RSA Enable Banking (no subir a git)
├── cert.pem / key.pem          # Certificado SSL local autofirmado (no subir a git)
├── database.db                 # SQLite (generado automáticamente, no subir a git)
├── routes/
│   ├── auth.py                 # /login  /auth_redirect
│   └── dashboard.py            # /dashboard  /sincronizar  /movimientos
├── models/
│   └── database.py             # Todas las funciones SQLite
├── services/
│   ├── enable_banking.py       # JWT + llamadas a la API de Enable Banking
│   └── categorizacion.py       # Motor de categorización de gastos por palabras clave
└── templates/
    ├── login.html
    ├── dashboard.html
    └── movimientos.html
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
| **Enable Banking session** | Tabla `sesiones_banco` en SQLite | Autorización del usuario en su banco (válida ~90 días, según normativa PSD2) |

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

- **Alcance de Open Banking (PSD2) en inversiones:** La normativa europea PSD2 solo cubre cuentas de pago y efectivo. Para brokers o entidades de inversión, la API solo entrega la cuenta corriente de efectivo, no fondos ni carteras. Para solventar esto, Bank-Hub adopta un enfoque híbrido combinando sincronización automática de cuentas corrientes con importación/registro manual de depósitos y carteras (ver detalles en `ROADMAP.md`).
- **Límite de consultas diarias (Rate Limit PSD2):** Redsys/bancos españoles aplican un máximo de 4 consultas automáticas cada 24 horas por consentimiento (error 429 `HUB046` si se sincroniza repetidamente en poco tiempo).
- **Límite de histórico PSD2:** Los bancos españoles en Redsys solo permiten consultar los últimos 89 días de movimientos por llamada. Los datos históricos anteriores se acumulan en SQLite y no se borran; solo el primer sync tiene este límite.
- **Un solo usuario:** `user_exists()` comprueba si hay un usuario principal en la base de datos local. No está diseñado para múltiples usuarios.
- **Sesión bancaria renovable:** Las autorizaciones bancarias tienen una vigencia estándar de 90 días según normativa PSD2. Al expirar, hay que reconectar el banco desde `/login`.

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
