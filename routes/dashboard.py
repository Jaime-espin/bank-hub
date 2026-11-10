from flask import Blueprint, redirect, url_for, session, render_template
from models.database import actualizar_cuenta, get_cuentas_usuario, get_session_bank, guardar_movimiento, get_movimientos
from services.enable_banking import get_balances, get_transactions, get_session_details

dashboard = Blueprint('dashboard', __name__)   # creas el Blueprint

@dashboard.route('/dashboard')                # asocias rutas a él
def mostrar_dashboard():
    if session.get('usuario_id') is None:
        return redirect(url_for('auth.login'))
    cuentas = get_cuentas_usuario(session['usuario_id'])
    ultimos_movimientos = get_movimientos(session['usuario_id'], limite=15)
    return render_template('dashboard.html', cuentas=cuentas, movimientos=ultimos_movimientos)

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
                        direccion = "ingreso" if m.get('credit_debit_indicator') == 'CRDT' else "gasto"
                        
                        remittance = m.get('remittance_information', [])
                        descripcion = remittance[1] if len(remittance) > 1 else (remittance[0] if len(remittance) > 0 else "")
                        
                        contraparte = ""
                        if m.get('creditor') and m['creditor'].get('name'):
                            contraparte = m['creditor']['name']
                        elif m.get('debtor') and m['debtor'].get('name'):
                            contraparte = m['debtor']['name']
                        guardar_movimiento(id_cuenta, fecha, importe, direccion, descripcion, contraparte, moneda)
    
    # Una vez terminada la sincronización, volvemos al dashboard
    return redirect(url_for('dashboard.mostrar_dashboard'))