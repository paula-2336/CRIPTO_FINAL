from flask import Flask, request, redirect, render_template, url_for, g, flash, session
from Base_de_Datos import BaseDatos
from criptografia import Cripto
import sqlite3
import smtplib
import random
from dotenv import load_dotenv
import ssl

app = Flask(__name__)
## SOLO PARA DESARROLLO
app.secret_key = 'supersecretkey'
bd = BaseDatos()
cripto = Cripto()

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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dni = request.form['dni']
        password = request.form['password']
        try: 
            clave = bd.validar_usuario(dni, password)
                
            if clave:
                # Inicia la sesión si las credenciales son correctas
                # TODO guradar la clave para desencriptar los datos
                session['logged_in'] = True
                session['dni'] = dni  # Guardamos el DNI en la sesión
                session['clave'] = clave # Guardamos la clave
                session['contrasena'] = password # Guardamos la contraseña para desencriptar la clave privada
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('menu'))
            raise Exception('Credenciales incorrectas')  
        except Exception as e:
            flash('DNI o contraseña incorrectos', 'error')

    return render_template('login.html')

# Función para validar credenciales
# def valid_credentials(dni, password):
#     if bd.validar_usuario(dni, password):
#         stored_password_hash = user['password_hash']
#         return check_password_hash(stored_password_hash, password)  # Comparar el hash
#     return False

#////////////////////////ENVIAR MAIL CON CODIGO VERIFICACION////////////////////////
def send_mail(username):
    try:
        load_dotenv()
        email_reciver = to
        password = os.getenv("PASSWORD")
        email_sender = "100472336@alumnos.uc3m.es"
        email_subject = "Confirmacion de correo"
        # Creamos el mensaje
        mensaje = EmailMessage()
        mensaje['Subject'] = email_subject
        mensaje['From'] = email_sender
        mensaje['To'] = email_reciver
        #Generamos un codigo de 6 digitos que utilizaremos como codigo de verificacion
        codigo_v = random.randint(100000, 999999)
        mensaje_codigo = str("Codigo de verificacion: " + str(codigo_v) + "\n")
        mensaje.set_content(mensaje_codigo)
        context = ssl.create_default_context()
        # Enviamos el mensaje
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(email_sender, password)
            smtp.sendmail(email_sender, email_reciver, mensaje.as_string())
        # Retornamos el codigo de verificacion, para su posterior comprobacion
        return codigo_v
    
     #en caso de error al enviar el correo:
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


#////////////////////////REGISTRO DE USUARIO////////////////////////
@app.route('/register', methods=['GET','POST'])
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
        session['logged_in'] = True
        session['dni'] = dni  # Guardamos el DNI en la sesión
        session['clave'] = clave # Clave para desencriptar los datos
        session['contrasena'] = password # Guardamos la contraseña para desencriptar la clave privada
        return redirect(url_for('registro_exitoso'))  
    if dni in bd.get_usuarios():
        flash('El DNI ya está registrado. Por favor, inicia sesión.', 'error')
        return redirect("\login.html")
    else:
        # Registrar el nuevo usuario en la base de datos
        clave = bd.nuevo_usuario(dni, password, contacto, email, nombre, apellidos)
        session['logged_in'] = True
        session['dni'] = dni  # Guardamos el DNI en la sesión
        session['clave'] = clave
        # TODO guardar la clave para desencriptar los datos
        # Enviar correo de verificación
        flash('Para terminar de verificar su identidad, se le enviara un codigo de verificacion a su correo')
        codigo = send_mail(str(email)) # Enviamos el correo
        codigo_v = flash(input("Ingrese el codigo de verificacion: "))
        if codigo_v != codigo:
            flash('Codigo incorrecto')
            return redirect("\register.html")
        else:
                flash('Usuario registrado con éxito')
                return redirect('\registro_exitoso')
            
@app.route('/registro_exitoso')
def registro_exitoso():
    return render_template('registro_exitoso.html')

#////////////////////////ACCESO A MENU////////////////////////
@app.route('/menu.html', methods=['GET','POST'])
def menu():
    if not session.get('logged_in'):
        return render_template('menu.html', session_iniciada=False)

    dni = session['dni']
    clave = session['clave']
    print(clave)
    consulta_mis_datos = bd.vista_usuario(dni, clave)
    return render_template(
        'menu.html',
        nombre_usuario = consulta_mis_datos[1],
        session_iniciada=True
    )


#////////////////////////HACER TRANSFERENCIA////////////////////////
@app.route('/transferencia.html', methods=['GET', 'POST'])
def transferencia():
    if request.method == 'POST':
        cuenta_origen = request.form['cuenta_origen']
        cuenta_destino = request.form['cuenta_destino']
        cantidad = float(request.form['cantidad'])
        concepto = request.form['concepto']
        contrasena = request.form['contrasena']
        
        if not cuenta_origen or not cuenta_destino or cantidad <= 0:
            flash('Todos los campos son obligatorios y la cantidad debe ser mayor a 0.')
            return redirect(url_for('transferencia'))

        try:
            bd.nueva_transferencia(cuenta_origen, cuenta_destino, cantidad, concepto, contrasena)
            flash('¡Transferencia realizada con éxito!')
        except Exception as e:
            print(f"Error al realizar la transferencia: {e}")
            flash('Hubo un error al procesar la transferencia. Inténtalo de nuevo.')
            return redirect(url_for('fracaso'))
    
    return render_template('transferencia.html', cuentas=bd.obtener_cuentas(session['dni']))

@app.route('/ingreso.html', methods=['GET', 'POST'])
def ingreso():
    if request.method == "POST":
        cuenta = request.form['cuenta']
        cantidad = float(request.form['cantidad'])
        concepto = request.form['concepto']
        bd.realizar_ingreso(cuenta, cantidad, concepto)
        flash('¡Ingreso realizado con éxito!')
        return redirect(url_for('ingreso'))
    return render_template('ingreso.html', cuentas=bd.obtener_cuentas(session['dni']))



@app.route('/fracaso')
def fracaso():
    return "Transferencia fallida"


@app.route('/cuentas.html')
def cuentas():
    if not session.get('logged_in'):
        return render_template('cuentas.html', session_iniciada=False)

    dni = session['dni']
    cuentas = bd.obtener_cuentas(dni)
    return render_template(
        'cuentas.html',
        cuentas=cuentas,
        nombre_usuario=bd.vista_usuario(dni, session['clave'])[1],
        session_iniciada=True
    )

@app.route('/crear_cuenta', methods=['GET', 'POST'])
def crear_cuenta():
    if not session.get('logged_in'):
        return render_template('crear_cuenta.html', session_iniciada=False)
    if request.method == 'GET':
        return render_template('crear_cuenta.html', session_iniciada=True)
    
    nombre = request.form['cuenta']
    dni = session['dni']
    bd.nueva_cuenta(dni, nombre)
    return redirect(url_for('cuentas'))

#/////HISTORIAL DE TRANSFERENCIAS/////
@app.route('/cuentas/<cuenta_id>')
def historial_transferencias(cuenta_id):
    if not session.get('logged_in'):
        return render_template('historial_trans.html', session_iniciada=False)
    try: 
        dni = session['dni']
        contraseña = session['contrasena']
        transferencias_enviadas = bd.transferencias_enviadas(dni, cuenta_id, contraseña)
        transferencias_recibidas = bd.transferencias_recibidas(dni, cuenta_id, contraseña)
        ingresos = bd.ingresos(cuenta_id)
        saldo = bd.calcular_saldo(cuenta_id)
    except Exception as e:
        print(f"Error al obtener el historial de transferencias: {e}")
        return redirect(url_for('menu'))

    return render_template(
        'historial_trans.html',
        transferencias_enviadas=transferencias_enviadas,
        transferencias_recibidas=transferencias_recibidas,
        ingresos=ingresos,
        saldo=saldo,
        session_iniciada=True
    )

#/////CONSULTAR MIS DATOS/////
@app.route('/mis_datos.html')
def mis_datos():
    if not session.get('logged_in'):
        return render_template('mis_datos.html', session_iniciada=False)

    dni = session['dni']
    clave = session['clave']
    print(clave)
    consulta_mis_datos = bd.vista_usuario(dni, clave)
   
    return render_template(
        'mis_datos.html',
        mis_datos = consulta_mis_datos,
        session_iniciada=True
    )

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('dni', None)  # Eliminar el DNI de la sesión
    session.pop('clave', None)
    return redirect("/index.html")

if __name__ == '__main__':
    app.run(debug=True)
