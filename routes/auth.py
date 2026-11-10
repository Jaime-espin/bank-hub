from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import user_exists, obtener_usuario, crear_usuario, get_session_bank, guardar_sesion_banco
from services.enable_banking import authenticate, bank_session

auth = Blueprint('auth', __name__)   # creas el Blueprint

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #autenticar al usuario
        input_username = request.form['username']
        input_password = request.form['password']
        if not user_exists(): # Crea un nuevo usuario si no existe ninguno
            crear_usuario(input_username, generate_password_hash(input_password))  
            return "Usuario creado con éxito"
        else: #si ya existe un usuario, verifica las credenciales
            usuario = obtener_usuario(input_username)
            if usuario == None:
                return "Usuario no encontrado"
            elif check_password_hash(usuario[2], input_password):  # Verifica la contraseña
                session['usuario_id'] = usuario[0]
                print("Autenticando usuario...")
                if get_session_bank(session['usuario_id']) is None:
                    auth_url = authenticate()  # Llama a la función authenticate
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
    code = request.args.get('code')
    session_data = bank_session(code)  # Llama a la función bank_session
    guardar_sesion_banco(session['usuario_id'], 
                        "Sandbox", 
                        session_data['session_id'], 
                        (datetime.now(timezone.utc) + timedelta(days=10)).isoformat())  # Guarda la sesión bancaria en la base de datos
    return redirect(url_for('dashboard.sincronizar'))  # Redirige al dashboard
        