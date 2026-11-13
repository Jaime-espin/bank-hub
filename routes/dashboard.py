from flask import Blueprint, redirect, url_for, session, render_template, request
from models.database import actualizar_cuenta, get_cuentas_usuario, get_resumen_saldos, get_session_bank, guardar_movimiento, get_movimientos, conciliar_movimiento_espejo, get_movimientos_filtrados, get_gasto_categoria
from services.categorizacion import obtener_categoria
from services.enable_banking import get_balances, get_transactions, get_session_details

dashboard = Blueprint('dashboard', __name__)   # creas el Blueprint

@dashboard.route('/dashboard')                # asocias rutas a él
def mostrar_dashboard():
    if session.get('usuario_id') is None:
        return redirect(url_for('auth.login'))
    cuentas = get_cuentas_usuario(session['usuario_id'])
    ultimos_movimientos = get_movimientos(session['usuario_id'], limite=15)
    resumen = get_resumen_saldos(session['usuario_id'])
    gasto_gasolina = get_gasto_categoria(session['usuario_id'], 'Gasolina')
    return render_template('dashboard.html', cuentas=cuentas, movimientos=ultimos_movimientos, resumen=resumen, gasto_gasolina=gasto_gasolina)

@dashboard.route('/sincronizar')
def sincronizar():
    if session.get('usuario_id') is None:
        return redirect(url_for('auth.login'))
    sesion_banco = get_session_bank(session['usuario_id'])
    if not sesion_banco:
        return redirect(url_for('dashboard.mostrar_dashboard'))
    session_id = sesion_banco[3]    #el id de enable banking
    sesion_banco_id = sesion_banco[0]   #el id local
    session_details = get_session_details(session_id)
    if session_details and 'accounts' in session_details:
        cuentas_propias = get_cuentas_usuario(session['usuario_id']) # Lista con los identificadores/nombres de tus cuentas y tu propio nombre de usuario
        # Sacamos el nombre (posición 2 de cada tupla) de todas las cuentas:
        nombres_cuentas = [c[2] for c in cuentas_propias]
        for uid in session_details['accounts']:
            # 1. Actualizar saldo
            datos_saldo = get_balances(uid)
            if datos_saldo and 'balances' in datos_saldo:
                balance = datos_saldo['balances'][0]['balance_amount']
                id_cuenta = actualizar_cuenta(
                    sesion_banco_id, uid, "Cuenta Sandbox", 
                    balance['amount'], balance['currency']
                )
                # 2. Descargar y guardar movimientos
                movimientos = get_transactions(uid)
                if movimientos:
                    for m in movimientos:
                        fecha = m.get('booking_date')
                        importe = float(m['transaction_amount']['amount'])
                        moneda = m['transaction_amount']['currency']
                        
                        remittance = m.get('remittance_information', [])
                        descripcion = remittance[1] if len(remittance) > 1 else (remittance[0] if len(remittance) > 0 else "")
                        
                        contraparte = ""
                        if m.get('creditor') and m['creditor'].get('name'):
                            contraparte = m['creditor']['name']
                        elif m.get('debtor') and m['debtor'].get('name'):
                            contraparte = m['debtor']['name']

                        direccion = "ingreso" if m.get('credit_debit_indicator') == 'CRDT' else "gasto"
                        
                        # Si la contraparte es el propio titular o la descripción indica traspaso propio:
                        if conciliar_movimiento_espejo(id_cuenta, fecha, importe, descripcion):
                            direccion = "transferencia_interna"

                        categoria = obtener_categoria(descripcion, contraparte)

                        guardar_movimiento(id_cuenta, fecha, importe, direccion, descripcion, contraparte, moneda, categoria)

    
    # Una vez terminada la sincronización, volvemos al dashboard
    return redirect(url_for('dashboard.mostrar_dashboard'))

@dashboard.route('/movimientos')
def movimientos():
    if session.get('usuario_id') is None:
        return redirect(url_for('auth.login'))
        
    busqueda = request.args.get('busqueda')
    cuenta_id = request.args.get('cuenta_id')
    tipo = request.args.get('tipo')
    categoria = request.args.get('categoria')
    
    todos_movimientos = get_movimientos_filtrados(session['usuario_id'], busqueda=busqueda, tipo=tipo, cuenta_id=cuenta_id, categoria=categoria)
    cuentas = get_cuentas_usuario(session['usuario_id'])
    
    return render_template('movimientos.html', 
                           movimientos=todos_movimientos, 
                           cuentas=cuentas,
                           busqueda=busqueda,
                           tipo_actual=tipo,
                           cuenta_actual=cuenta_id,
                           categoria_actual=categoria)