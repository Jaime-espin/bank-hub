from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import user_exists, obtener_usuario, crear_usuario, get_session_bank, guardar_sesion_banco
from services.enable_banking import authenticate, bank_session, get_config

auth = Blueprint('auth', __name__)   # creas el Blueprint

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #autenticar al usuario
        input_username = request.form['username']
        input_password = request.form['password']
        if not user_exists(): # Crea un nuevo usuario si no existe ninguno
            crear_usuario(input_username, generate_password_hash(input_password))  
            usuario = obtener_usuario(input_username)
            session['usuario_id'] = usuario[0]
            auth_url = authenticate()
            if not auth_url:
                return "Usuario creado, pero hubo un error al conectar con el banco. Revisa la terminal.", 500
            return redirect(auth_url)
        else: #si ya existe un usuario, verifica las credenciales
            usuario = obtener_usuario(input_username)
            if usuario == None:
                return "Usuario no encontrado"
            elif check_password_hash(usuario[2], input_password):  # Verifica la contraseña
                session['usuario_id'] = usuario[0]
                print("Autenticando usuario...")
                if get_session_bank(session['usuario_id']) is None:
                    auth_url = authenticate()  # Llama a la función authenticate
                    if not auth_url:
                        return "Error al conectar con el banco. Revisa la terminal.", 500
                    return redirect(auth_url)  # Redirige a la función authenticate
                    
                return redirect(url_for('dashboard.mostrar_dashboard'))  # Redirige al dashboard
            else:
                return "Credenciales inválidas"
    else:
        return render_template('login.html')

@auth.route('/auth_redirect')
def auth_redirect():
    if session.get('usuario_id') is None:
        return redirect(url_for('auth.login'))

    error = request.args.get('error')
    if error:
        error_desc = request.args.get('error_description', error)
        return f"El banco devolvió un error de autorización: {error_desc}. Inténtalo de nuevo.", 400

    code = request.args.get('code')
    if not code:
        return "No se recibió código de autorización del banco.", 400

    session_data = bank_session(code)
    if not session_data or 'session_id' not in session_data:
        return "Error al crear la sesión con el banco en Enable Banking.", 500

    config = get_config()
    banco_nombre = config.get("aspspName", "Banco")
    guardar_sesion_banco(session['usuario_id'], 
                        banco_nombre, 
                        session_data['session_id'], 
                        (datetime.now(timezone.utc) + timedelta(days=90)).isoformat())  # Guarda la sesión bancaria en la base de datos
    return redirect(url_for('dashboard.sincronizar'))  # Redirige al dashboard
        