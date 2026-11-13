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
            tipo_cuenta TEXT CHECK(tipo_cuenta IN ('corriente', 'ahorros', 'inversion')) DEFAULT 'corriente',
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
            categoria TEXT DEFAULT 'Otros',
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

def actualizar_cuenta(sesion_banco_id, uid, nombre, saldo, moneda, tipo_cuenta='corriente'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM cuentas WHERE uid_enablebanking = ?', (uid,))
    cuenta_id = cursor.fetchone()
    if not cuenta_id:
        cursor.execute(
            'INSERT INTO cuentas (sesiones_banco_id, uid_enablebanking, nombre, saldo, moneda, tipo_cuenta) VALUES (?, ?, ?, ?, ?, ?)',
            (sesion_banco_id, uid, nombre, saldo, moneda, tipo_cuenta)
        )
        id_final = cursor.lastrowid
    else:
        cursor.execute(
            'UPDATE cuentas SET saldo = ?, moneda = ? WHERE id = ?',
            (saldo, moneda, cuenta_id[0])
        )
        id_final = cuenta_id[0]
    conn.commit()
    conn.close()

    return id_final

def get_cuentas_usuario(usuario_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.uid_enablebanking, c.nombre, c.saldo, c.moneda, c.tipo_cuenta
        FROM cuentas c
        JOIN sesiones_banco s ON c.sesiones_banco_id = s.id
        WHERE s.usuario_id = ?
    ''', (usuario_id,))
    cuentas = cursor.fetchall()
    conn.close()
    return cuentas

def guardar_movimiento(cuenta_id, fecha, importe, direccion, descripcion, contraparte, moneda, categoria='Otros'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id FROM detalles_movimientos 
        WHERE cuenta_id = ? AND fecha = ? AND importe = ? AND descripcion = ?
    ''', (cuenta_id, fecha, importe, descripcion))

    movimiento_existente = cursor.fetchone()
    if not movimiento_existente:
        cursor.execute(
            'INSERT INTO detalles_movimientos (cuenta_id, fecha, importe, direccion, descripcion, contraparte, moneda, categoria) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (cuenta_id, fecha, importe, direccion, descripcion, contraparte, moneda, categoria)
        )
    else:
        # Si ya existía de antes (cuando era 'gasto') y ahora lo hemos detectado como transferencia:
        if direccion == 'transferencia_interna':
            cursor.execute(
                'UPDATE detalles_movimientos SET direccion = ? WHERE id = ?',
                (direccion, movimiento_existente[0])
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

def conciliar_movimiento_espejo(id_cuenta, fecha, importe, descripcion):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Busca si existe en OTRA cuenta un movimiento con la misma fecha e importe
    cursor.execute('''
        SELECT id FROM detalles_movimientos 
        WHERE cuenta_id != ? AND fecha = ? AND importe = ? AND descripcion = ?
    ''', (id_cuenta, fecha, importe, descripcion))
    espejo = cursor.fetchone()

    if espejo:
        id_espejo = espejo[0]
        # 2. Si lo encuentra, actualiza ese movimiento previo a 'transferencia_interna'
        cursor.execute('''
            UPDATE detalles_movimientos 
            SET direccion = 'transferencia_interna' 
            WHERE id = ?
        ''', (id_espejo,))
        conn.commit()
        conn.close()
        return True  # Indica que hubo coincidencia
        
    conn.close()
    return False

def get_resumen_saldos(usuario_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.tipo_cuenta, SUM(c.saldo)
        FROM cuentas c
        JOIN sesiones_banco s ON c.sesiones_banco_id = s.id
        WHERE s.usuario_id = ?
        GROUP BY c.tipo_cuenta
    ''', (usuario_id,))
    resumen = cursor.fetchall()
    conn.close()

    # Lo convertimos a diccionario con valores por defecto en 0.0:
    totales = {'corriente': 0.0, 'ahorros': 0.0, 'inversion': 0.0}
    for tipo, saldo in resumen:
        totales[tipo] = round(saldo or 0.0, 2)
        
    totales['total'] = round(sum(totales.values()), 2)
    return totales

def get_movimientos_filtrados(usuario_id, busqueda=None, cuenta_id=None, tipo=None, categoria=None, fecha_inicio=None, fecha_fin=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = '''
        SELECT m.fecha, m.importe, m.direccion, m.descripcion, m.contraparte, m.moneda, m.categoria
        FROM detalles_movimientos m
        JOIN cuentas c ON m.cuenta_id = c.id
        JOIN sesiones_banco s ON c.sesiones_banco_id = s.id
        WHERE s.usuario_id = ?
    '''
    params = [usuario_id]

    if busqueda:
        query += ' AND (m.descripcion LIKE ? OR m.contraparte LIKE ?)'
        params.extend([f'%{busqueda}%', f'%{busqueda}%'])
    if cuenta_id:
        query += ' AND c.id = ?'
        params.append(cuenta_id)
    if tipo:
        query += ' AND m.direccion = ?'
        params.append(tipo)
    if categoria:
        query += ' AND m.categoria = ?'
        params.append(categoria)
    if fecha_inicio:
        query += ' AND m.fecha >= ?'
        params.append(fecha_inicio)
    if fecha_fin:
        query += ' AND m.fecha <= ?'
        params.append(fecha_fin)

    query += ' ORDER BY m.fecha DESC, m.id DESC'

    cursor.execute(query, params)
    movimientos = cursor.fetchall()
    conn.close()
    return movimientos

def get_gasto_categoria(usuario_id, categoria):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT SUM(m.importe)
        FROM detalles_movimientos m
        JOIN cuentas c ON m.cuenta_id = c.id
        JOIN sesiones_banco s ON c.sesiones_banco_id = s.id
        WHERE s.usuario_id = ? AND m.categoria = ? AND m.direccion = 'gasto'
    ''', (usuario_id, categoria))
    total = cursor.fetchone()[0]
    conn.close()
    return round(total or 0.0, 2)

if __name__ == "__main__":
    crear_tablas()