# Bank-hub

Proyecto personal para conectar diferentes cuentas bancarias personales en un mismo lugar. Facilitando la visualización de liquidez y movimientos en un mismo lugar. Usaré **enable banking**

## MVP
Primero haré el mvp que unicamente mostrará la información como los movimientos y el saldo extraido de un banco simulado de enable banking
App web, red local, login propio, saldos + movimientos, cuentas sandbox de Enable Banking.
Flujo 1: TÚ → tu app  (login con usuario/contraseña)
Flujo 2: TÚ → tu banco (permiso a Enable Banking para leer tus cuentas)

Backend: Python + Flask
Base de datos: SQLite
Frontend: HTML/CSS (Flask tiene un sistema de plantillas llamado Jinja2 que te permite mezclar HTML con datos de Python, lo veremos cuando llegue el momento)
Alojamiento MVP: Tu portátil, red local
Cuentas: Sandbox de Enable Banking

Usuario abre la app
        ↓
¿Está logueado en la app?
        NO → /login → introduce contraseña → login correcto
        ↓
¿Hay sesión activa con Enable Banking?
        NO → inicia flujo con el banco → usuario da permiso → /auth_redirect → sesión creada
        ↓
/dashboard → muestra saldos y movimientos