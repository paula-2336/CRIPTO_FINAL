from flask import Flask, request, redirect, render_template, url_for, g, flash, session
from Base_de_Datos import BaseDatos
from criptografia import Cripto
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'
bd = BaseDatos()

#////////RUTA REDENRIZAR INDEX.HTML////////
@app.route('/')
@app.route('/index.html')
def home_page():
    return render_template('index.html')

# Conexión a la base de datos
# def get_db_connection():
#    conn = sqlite3.connect('test.db')
 #   conn.row_factory = sqlite3.Row
  #  return conn

#/////////////////////////INICIAR SESION///////////////////////
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dni = request.form['dni']
        password = request.form['password']

        if bd.validar_usuario(dni, password):
            # Inicia la sesión si las credenciales son correctas
            # TODO guradar la clave para desencriptar los datos
            session['logged_in'] = True
            session['dni'] = dni  # Guardamos el DNI en la sesión
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('historial_transferencias'))  
        else:
            flash('DNI o contraseña incorrectos', 'error')

    return render_template('login.html')

# Función para validar credenciales
# def valid_credentials(dni, password):
#     if bd.validar_usuario(dni, password):
#         stored_password_hash = user['password_hash']
#         return check_password_hash(stored_password_hash, password)  # Comparar el hash
#     return False

#////////////////////////REGISTRO DE USUARIO////////////////////////
@app.route('/register.html', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        dni = request.form['dni']
        contacto = request.form['contacto']
        email = request.form['email']
        password = request.form['password']

        # Registrar el nuevo usuario en la base de datos
        clave = bd.nuevo_usuario(dni, password, contacto, email, nombre, apellidos)
        # TODO guardar la clave para desencriptar los datos
        return redirect(url_for('registro_exitoso'))  
        
    return render_template('register.html')

@app.route('/registro_exitoso')
def registro_exitoso():
    return render_template('registro_exitoso.html')

#////////////////////////HACER TRANSFERENCIA////////////////////////
@app.route('/transferencia.html', methods=['GET', 'POST'])
def transferencia():
    if request.method == 'POST':
        cuenta_origen = request.form['cuenta_origen']
        cuenta_destino = request.form['cuenta_destino']
        cantidad = float(request.form['cantidad'])
        concepto = request.form['concepto']
        
        if not cuenta_origen or not cuenta_destino or cantidad <= 0:
            flash('Todos los campos son obligatorios y la cantidad debe ser mayor a 0.')
            return redirect(url_for('transferencia'))

        try:
            bd.nueva_transferencia(cuenta_origen, cuenta_destino, cantidad, concepto)
            flash('¡Transferencia realizada con éxito!')
        except Exception as e:
            print(f"Error al realizar la transferencia: {e}")
            flash('Hubo un error al procesar la transferencia. Inténtalo de nuevo.')
            return redirect(url_for('transferencia'))
    
    return render_template('transferencia.html')

@app.route('/exito')
def exito():
    return "¡Transferencia realizada con éxito!"

#/////HISTORIAL DE TRANSFERENCIAS/////
@app.route('/historial_trans.html')
def historial_transferencias():
    if not session.get('logged_in'):
        return render_template('historial_trans.html', session_iniciada=False)

    dni = session['dni']
    # TODO Usar la clase db que ya tiene las funciones
    conn = get_db_connection()
    transferencias_enviadas = conn.execute("SELECT fecha, id_cuenta_destino AS cuenta_destino, cantidad, concepto FROM transferencias WHERE id_cuenta_origen = ?", (dni,)).fetchall()
    transferencias_recibidas = conn.execute("SELECT fecha, id_cuenta_origen AS cuenta_origen, cantidad, concepto FROM transferencias WHERE id_cuenta_destino = ?", (dni,)).fetchall()
    conn.close()
    
    return render_template(
        'historial_trans.html',
        transferencias_enviadas=transferencias_enviadas,
        transferencias_recibidas=transferencias_recibidas,
        session_iniciada=True
    )

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('dni', None)  # Eliminar el DNI de la sesión
    # TODO eliminar la clave de la sesión
    return redirect("/login.html")

if __name__ == '__main__':
    app.run(debug=True)
