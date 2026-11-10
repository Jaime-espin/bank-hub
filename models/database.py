import sqlite3
import os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'database.db')

def crear_tablas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Crear tabla de usuario
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Crear tabla de sesiones de banco
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesiones_banco (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            banco TEXT NOT NULL,
            sesion_id TEXT NOT NULL,
            expira_en TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuario(id)
        )
    ''')

    # Crear tabla de cuentas bancarias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sesiones_banco_id INTEGER NOT NULL,
            uid_enablebanking TEXT NOT NULL,
            nombre TEXT NOT NULL,
            saldo REAL NOT NULL,
            moneda TEXT NOT NULL,
            FOREIGN KEY (sesiones_banco_id) REFERENCES sesiones_banco(id)
        )
    ''')

    # Crear tabla de detalles de movimientos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalles_movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            importe REAL NOT NULL,
            direccion TEXT NOT NULL,
            descripcion TEXT,
            contraparte TEXT,
            moneda TEXT NOT NULL,
            FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)
        )
    ''')

    conn.commit()
    conn.close()

def crear_usuario(nombre, password_hash):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO usuario (nombre, password_hash) VALUES (?, ?)', (nombre, password_hash))
    conn.commit()
    conn.close()

def obtener_usuario(nombre):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuario WHERE nombre = ?', (nombre,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario

def user_exists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuario')
    usuario = cursor.fetchone()
    conn.close()
    return True if usuario else False

def get_session_bank(usuario_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sesiones_banco WHERE usuario_id = ?', (usuario_id,))
    sesion = cursor.fetchone()
    conn.close()
    return sesion

def guardar_sesion_banco(usuario_id, banco, session_id, expira_en):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO sesiones_banco (usuario_id, banco, sesion_id, expira_en) VALUES (?, ?, ?, ?)',
        (usuario_id, banco, session_id, expira_en)
    )
    conn.commit()
    conn.close()

def actualizar_cuenta(sesion_banco_id, uid, nombre, saldo, moneda):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM cuentas WHERE uid_enablebanking = ?', (uid,))
    cuenta_id = cursor.fetchone()
    if not cuenta_id:
        cursor.execute(
            'INSERT INTO cuentas (sesiones_banco_id, uid_enablebanking, nombre, saldo, moneda) VALUES (?, ?, ?, ?, ?)',
            (sesion_banco_id, uid, nombre, saldo, moneda)
        )
        id_final = cursor.lastrowid
    else:
        cursor.execute(
            'UPDATE cuentas SET nombre = ?, saldo = ?, moneda = ? WHERE sesiones_banco_id = ? AND uid_enablebanking = ?',
            (nombre, saldo, moneda, sesion_banco_id, uid)
        )
        id_final = cuenta_id[0]
    conn.commit()
    conn.close()

    return id_final

def get_cuentas_usuario(usuario_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.uid_enablebanking, c.nombre, c.saldo, c.moneda
        FROM cuentas c
        JOIN sesiones_banco s ON c.sesiones_banco_id = s.id
        WHERE s.usuario_id = ?
    ''', (usuario_id,))
    cuentas = cursor.fetchall()
    conn.close()
    return cuentas

def guardar_movimiento(cuenta_id, fecha, importe, direccion, descripcion, contraparte, moneda):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id FROM detalles_movimientos 
        WHERE cuenta_id = ? AND fecha = ? AND importe = ? AND descripcion = ?
    ''', (cuenta_id, fecha, importe, descripcion))
    if not cursor.fetchone():
        cursor.execute(
            'INSERT INTO detalles_movimientos (cuenta_id, fecha, importe, direccion, descripcion, contraparte, moneda) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (cuenta_id, fecha, importe, direccion, descripcion, contraparte, moneda)
        )
    conn.commit()
    conn.close()

def get_movimientos(usuario_id, limite=15):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT m.fecha, m.importe, m.direccion, m.descripcion, m.contraparte, m.moneda
        FROM detalles_movimientos m
        JOIN cuentas c ON m.cuenta_id = c.id
        JOIN sesiones_banco s ON c.sesiones_banco_id = s.id
        WHERE s.usuario_id = ?
        ORDER BY m.fecha DESC, m.id DESC
        LIMIT ?''', (usuario_id, limite))
    movimientos = cursor.fetchall()
    conn.close()
    return movimientos

if __name__ == "__main__":
    crear_tablas()