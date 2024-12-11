import sqlite3
from criptografia import Cripto
import random

class BaseDatos:

    def __init__(self):
        """Creamos las conexiones con las bases de datos"""
        #Conectamos con la base de datos de los usuarios utilizando sqlite3. 
        self.__criptografia = Cripto()
        self.conexion = sqlite3.connect("test.db", check_same_thread=False)
        self.cursor = self.conexion.cursor()
        self.cursor.execute("PRAGMA foreign_keys = 1")
    
    ############### GENERACIÓN DE LAS BASES DE DATOS ###################
    def crear_base_datos(self):
        """Creamos ambas tablas de la base de datos del proyecto. """
        #En primer lugar creamos la tabla de los usuarios: 
        #Decisiones respecto al diseño; varchar2(100) para los apellidos para abrcar aquellos compuestos o largos, 
        #varchar2(254) para email ya que es el maximo permitido por los estándares de internet. 
        self.cursor.execute("""
                                CREATE TABLE usuarios (
                                dni_usuario CHAR(20) PRIMARY KEY, -- Número de teléfono del usuario
                                hash_contraseña CHAR(256) NOT NULL, -- Token de uso único contraseña
                                salt_contraseña CHAR(64) NOT NULL, -- Salt aleatorio de la contraeña
                                salt_clave CHAR(64) NOT NULL, -- Salt aleatorio de la clave
                                telefono VARCHAR2(15) NOT NULL UNIQUE, -- Telefono del usuario
                                nonce_telefono CHAR(24), -- Valor uso único del teléfono
                                email VARCHAR(254) NOT NULL UNIQUE, -- Email del usuario
                                nonce_email CHAR(24), -- Valor uso único del email
                                nombre VARCHAR2(50), -- Nombre del usuario
                                nonce_nombre CHAR(24), -- Valor uso único del nombre
                                apellido VARCHAR2(100), -- Apellido del usuario
                                nonce_apellido CHAR(24) -- Valor uso único del apellido
                                );""")


        #Creamos la base de datos de las cuentas bamcarias:
        self.cursor.execute("""
                                CREATE TABLE cuentas (
                                numero_cuenta CHAR(24) PRIMARY KEY, -- Número de cuenta del usuario
                                dni_usuario CHAR(20), -- Dni del usuario que tiene la cuenta
                                nombre_cuenta VARCHAR2(50), -- Nombre de la cuenta
                                FOREIGN KEY (dni_usuario) REFERENCES usuarios(dni_usuario)
                                );""")

   
        #Creamos la base de datos de las transferencias:
        #Decisiones respecto al diseño: varchar(34) por si estamos trabajando con cuentas bancarias internacionales (IBAN)
        #Maximo monto permitido en españa sin declarar
        self.cursor.execute("""
                                CREATE TABLE transferencias(
                                id_transferencia INTEGER PRIMARY KEY AUTOINCREMENT, -- Id de la transferencia
                                cuenta_origen CHAR(24) NOT NULL, -- Número de cuenta origen
                                cuenta_destino CHAR(24) NOT NULL, -- Número de cuenta destino
                                fecha_transfer DATETIME DEFAULT CURRENT_TIMESTAMP, -- Fecha y Hora en la que se registra la transferencia
                                monto DECIMAL(5,2) NOT NULL, -- Cantidad de dinero enviado
                                concepto_origen TEXT, -- Concepto de la transferencia encriptado para el remitente
                                concepto_destino TEXT,  -- Concepto de la transferencia encriptado para el destinatario
                                firma TEXT, -- Firma de la transferencia
                                FOREIGN KEY(cuenta_origen) REFERENCES cuentas(numero_cuenta),
                                FOREIGN KEY(cuenta_destino) REFERENCES cuentas(numero_cuenta)
                                );""")
        
        self.cursos.execute("""
                                CREATE TABLE ingresos(
                                    id_ingreso INTEGER PRIMARY KEY AUTOINCREMENT, -- Id del ingreso
                                    cuenta CHAR(24) NOT NULL, -- Número de cuenta origen
                                    fecha_ingreso DATETIME DEFAULT CURRENT_TIMESTAMP, -- Fecha y Hora en la que se registra el ingreso
                                    monto DECIMAL(5,2) NOT NULL, -- Cantidad de dinero ingresada
                                    concepto TEXT, -- Concepto del ingreso
                                    FOREIGN KEY(cuenta) REFERENCES cuentas(numero_cuenta)
                                );""")
                            

    ############### GENERACIÓN DE UN NUEVO USUARIO ###################                     
    def nuevo_usuario(self, dni, contraseña, telefono, email, nombre, apellido):
        """Añadimos un nuevo usuario a la base de datos siempre y cuando proporcione los requisitos necesarios"""
        # Creamos un certificado para el usuario
        self.__criptografia.generar_clave_privado_y_publica(contraseña, dni)
        salt_contraseña, hash_contraseña = self.__criptografia.generar_contraseña(contraseña)
        salt_clave, clave = self.__criptografia.prim_deriv_clave_contraseña(contraseña)
        nonce_telefono, telefono_encriptado = self.__criptografia.encrypt_mis_datos(clave, telefono)
        nonce_email, email_encriptado = self.__criptografia.encrypt_mis_datos(clave, email)
        nonce_nombre, nombre_encriptado = self.__criptografia.encrypt_mis_datos(clave, nombre)
        nonce_apellido, apellido_encriptado = self.__criptografia.encrypt_mis_datos(clave, apellido)
        self.cursor.execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?,?,?,?,?,?);",
                            (dni, hash_contraseña, salt_contraseña, salt_clave, telefono_encriptado, nonce_telefono, email_encriptado,
                            nonce_email, nombre_encriptado, nonce_nombre, apellido_encriptado, nonce_apellido))
        self.conexion.commit()
        self.nueva_cuenta(dni, "Personal")
        return clave

    def nueva_cuenta(self, dni, nombre):
        """Función que añade una nueva cuenta a la base de datos de cuentas"""
        self.cursor.execute("INSERT INTO cuentas(dni_usuario, numero_cuenta, nombre_cuenta) VALUES(?,?,?);", (dni, self.generar_cuenta(), nombre))
        self.conexion.commit()

    def obtener_cuentas(self, dni):
        """Función que devuelve todas las cuentas de un usuario"""
        cuentas = list(self.cursor.execute("SELECT numero_cuenta, nombre_cuenta FROM cuentas WHERE dni_usuario = ?;", (dni,)))
        return cuentas

    def generar_cuenta(self):
        """Generamos un número de cuenta aleatorio"""
        cuenta = "ES"
        for _ in range(22):
            cuenta += str(random.randint(0,9))
        return cuenta

    ############### VALIDACIÓN DE UN USUARIO ###################
    def validar_usuario(self, dni, contraseña):
        """ Validamos la infromación proporcionada por un usuario en el log-in"""
        #Primero hacemos una vista de los dadtos de autenticación del usuario y los convertimos en una lista
        vista = list(self.cursor.execute("SELECT dni_usuario, hash_contraseña, salt_contraseña, salt_clave FROM usuarios WHERE dni_usuario = ?;", (dni,)))
        #A continuación comprobamos que dichos datos son correctos (requerimos el salt de la contraseña y la clave)
        if self.__criptografia.validar_contraseña(contraseña, vista[0][2], vista[0][1]):
            return self.__criptografia.deriv_clave_contraseña(vista[0][3], contraseña)
        return False


    ############### POSIBLES CONSULTAS DE UN USUARIO ###################
    def vista_usuario(self, dni, clave):
        """Esta funcion devuelve toda la información pertinente dado un usuario"""
        #Creamos la consulta sql y devolvemos todo lo que recoge la vista del usuario
        vista = list(self.cursor.execute("SELECT nombre, apellido, email, telefono, nonce_nombre, nonce_apellido, nonce_email, nonce_telefono FROM usuarios WHERE dni_usuario = ?;", (dni,)))
        datos_desencriptados = [dni]
        datos, nonces = vista[0][:4], vista[0][4:]
        for i in range(len(datos)):
            dato_desencriptado = self.__criptografia.decrypt_mis_datos(clave, nonces[i], datos[i])
            datos_desencriptados.append(dato_desencriptado)
        return datos_desencriptados

    def nueva_transferencia(self, remitente, beneficiario, cantidad, concepto, contraseña_clave_privada):
        """Función que añade una nueva transferencia a la bd de transferencias"""
        # TODO Firmar la cantidad de la transferencia
        dni_beneficiario = self.obtener_dueño_cuenta(beneficiario)
        dni_remitente = self.obtener_dueño_cuenta(remitente)
        concepto_origen, concepto_destino = self.__criptografia.encriptar_asunto(dni_remitente, dni_beneficiario, concepto)
        firma = self.__criptografia.firmar_cantidad(dni_remitente, contraseña_clave_privada, cantidad)
        print(concepto_origen, concepto_destino)
        self.cursor.execute("INSERT INTO transferencias(cuenta_origen, cuenta_destino, monto, concepto_origen, concepto_destino, firma) VALUES(?,?,?,?,?,?);", 
                            (remitente, beneficiario, cantidad, concepto_origen, concepto_destino, firma))
        print(remitente, beneficiario, cantidad, concepto_origen, concepto_destino)
        self.conexion.commit()

    def transferencias_enviadas(self, dni, cuenta, contraseña):
        # TODO añadir comprobación de la firma de la cantidad
        """Esta funcion crea una vista de todas las transferencias registradas donde el remitente es el usuario seleccionado"""
        vista = []
        vista = list(self.cursor.execute("SELECT fecha_transfer, cuenta_destino, monto, concepto_origen, firma, cuenta_origen FROM transferencias WHERE cuenta_origen = ?;", (cuenta,)))

        vista_final = []
        for i in range(len(vista)):
            asunto_descifrado = self.__criptografia.desencriptar_asunto(dni, contraseña, vista[i][3])
            usuario_origen = self.obtener_dueño_cuenta(vista[i][5])
            # Comprobamos que el cirtaficado haya sido firamdo por el banco
            if not self.__criptografia.verificar_cadena_certificado(usuario_origen):
                continue
            if self.__criptografia.comprobar_firma_cantidad(usuario_origen, vista[i][2], vista[i][4]):
                print("La firma es incorrecta")
                vista.pop(i)
                continue
            vista_final.append([vista[i][0], vista[i][1], vista[i][2], asunto_descifrado])
            print("La firma es correcta")
        return vista_final

    def transferencias_recibidas(self, dni, cuenta, contraseña):
        """Esta función crea una vista de todas las transferencias registradas donde el beneficiario es el usuario seleccionado."""
        # Realizamos la consulta de las trasnferencias que tiene como cuenta destino la cuenta seleccionada
        vista = [] 
        vista = list(self.cursor.execute("SELECT fecha_transfer, cuenta_origen, monto, concepto_destino, firma FROM transferencias WHERE cuenta_destino = ?;", (cuenta,)))
        # Comprobamos la firma de la cantidad y desenccriptamos el asunto
        vista_final = []
        for i in range(len(vista)):
            asunto_descifrado = self.__criptografia.desencriptar_asunto(dni, contraseña, vista[i][3])
            usuario_origen = self.obtener_dueño_cuenta(vista[i][1])
            # Comprobamos que el cirtaficado haya sido firamdo por el banco
            if not self.__criptografia.verificar_cadena_certificado(usuario_origen):
                continue
            if self.__criptografia.comprobar_firma_cantidad(usuario_origen, vista[i][2], vista[i][4]):
                print("La firma es incorrecta")
                vista.pop(i) # No se cuenta la transferencia si la firma es incorrecta
                continue
            vista_final.append([vista[i][0], vista[i][1], vista[i][2], asunto_descifrado])
            print("La firma es correcta")
        return vista_final
    
    def realizar_ingreso(self, cuenta, cantidad, concepto):
        """Función que añade un ingreso a la base de datos de ingresos"""
        self.cursor.execute("INSERT INTO ingresos(cuenta, monto, concepto) VALUES(?,?,?);", (cuenta, cantidad, concepto))
        self.conexion.commit()

    def ingresos(self, cuenta):
        """Función que crea una vista de todos los ingresos registrados en una cuenta"""
        vista = []
        vista = list(self.cursor.execute("SELECT fecha_ingreso, monto, concepto FROM ingresos WHERE cuenta = ?;", (cuenta,)))
        return vista
    
    def calcular_saldo(self, cuenta):
        """Función que calcula el saldo de una cuenta"""
        ingresos = list(self.cursor.execute("SELECT SUM(monto) FROM ingresos WHERE cuenta = ?;", (cuenta,)))
        transferencias_enviadas = list(self.cursor.execute("SELECT SUM(monto) FROM transferencias WHERE cuenta_origen = ?;", (cuenta,)))
        transferencias_recibidas = list(self.cursor.execute("SELECT SUM(monto) FROM transferencias WHERE cuenta_destino = ?;", (cuenta,)))
        if not ingresos[0][0]:
            ingresos[0] = (0,)
        if not transferencias_enviadas[0][0]:
            transferencias_enviadas[0] = (0,)
        if not transferencias_recibidas[0][0]:
            transferencias_recibidas[0] = (0,)
        saldo = int(ingresos[0][0]) - int(transferencias_enviadas[0][0]) + int(transferencias_recibidas[0][0])
        return saldo
    
    def obtener_dueño_cuenta(self, cuenta):
        """Función que devuelve el dueño de una cuenta"""
        dueño = list(self.cursor.execute("SELECT dni_usuario FROM cuentas WHERE numero_cuenta = ?;", (cuenta,)))
        return dueño[0][0]




