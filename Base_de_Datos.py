import sqlite3
from criptografia import Cripto

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

         #Creamos la base de datos de las transferencias:
        #Decisiones respecto al diseño: varchar(34) por si estamos trabajando con cuentas bancarias internacionales (IBAN)
        #Maximo monto permitido en españa sin declarar
        self.cursor.execute("""
                                CREATE TABLE transferencias(
                                id INTEGER PRIMARY KEY AUTOINCREMENT, -- ID único de la transacción
                                id_cuenta_origen INTEGER, -- Id de la cuenta que envía el dinero
                                id_cuenta_destino INTEGER, -- Id de la cuenta que recibe el dinero
                                fecha_transfer DATETIME DEFAULT CURRENT_TIMESTAMP, -- Fecha y Hora en la que se registra la transferencia
                                monto DECIMAL(5,2) NOT NULL, -- Cantidad de dinero enviado
                                concepto TEXT, -- Concepto de la transferencia
                                estado VARCHAR(20) DEFAULT 'PENDIENTE', -- Estado de la transferencia
                                FOREIGN KEY(id_cuenta_origen) REFERENCES usuarios(dni_usuario),
                                FOREIGN KEY(id_cuenta_destino) REFERENCES usuarios(dni_usuario)
                                );""")

    ############### GENERACIÓN DE UN NUEVO USUARIO ###################                     
    def nuevo_usuario(self, dni, contraseña, telefono, email, nombre, apellido):
        """Añadimos un nuevo usuario a la base de datos siempre y cuando proporcione los requisitos necesarios"""
        salt_contraseña, hash_contraseña = self.__criptografia.generar_contraseña(contraseña)
        salt_clave, clave = self.__criptografia.prim_deriv_clave_contraseña(contraseña)
        nonce_telefono, telefono = self.__criptografia.encrypt_mis_datos(clave, telefono)
        nonce_email, email = self.__criptografia.encrypt_mis_datos(clave, email)
        nonce_nombre, nombre = self.__criptografia.encrypt_mis_datos(clave, nombre)
        nonce_apellido, apellido = self.__criptografia.encrypt_mis_datos(clave, apellido)
        self.cursor.execute("INSERT INTO usuarios VALUES (?,?,?,?,?,?,?,?,?,?,?,?);",
                            (dni, hash_contraseña, salt_contraseña, salt_clave, telefono, nonce_telefono, email,
                            nonce_email, nombre, nonce_nombre, apellido, nonce_apellido))
        self.conexion.commit()
        return clave


    ############### VALIDACIÓN DE UN USUARIO ###################
    def validar_usuario(self, dni, contraseña):
        """ Validamos la infromación proporcionada por un usuario en el log-in"""
        #Primero hacemos una vista de los dadtos de autenticación del usuario y los convertimos en una lista
        vista = list(self.cursor.execute("SELECT dni_usuario, hash_contraseña, salt_contraseña, salt_clave FROM usuarios WHERE dni_usuario = ?;", (dni,)))
        #A continuación comprobamos que dichos datos son correctos (requerimos el salt de la contraseña y la clave)
        if self.__criptografia.validar_contraseña(contraseña, vista[0][2], vista[0][1]):
            return self.__criptografia.deriv_clave_contraseña(vista[0][2], contraseña)
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

    def nueva_transferencia(self, remitente, beneficiario, cantidad, concepto):
        """Función que añade una nueva transferencia a la bd de transferencias"""
        self.cursor.execute("INSERT INTO transferencias(id_cuenta_origen, id_cuenta_destino, monto, concepto) VALUES(?,?,?,?);", (remitente, beneficiario, cantidad, concepto))
        self.conexion.commit()

    def transferencias_enviadas(self, dni, clave):
        """Esta funcion crea una vista de todas las transferencias registradas donde el remitente es el usuario seleccionado"""
        vista = list(self.cursor.execute("SELECT fecha_transfer, id_cuenta_destino, monto, concepto FROM transferencias WHERE id_cuenta_origen = ?;", (dni,)))
        datos_desencriptados = []
        for dato in vista[0]:
            dato_desencriptado = self.__criptografia.decrypt_mis_datos(clave, nonce, dato)
            datos_desencriptados.append(dato_desencriptado)
        return datos_desencriptados

    def transferencias_recibidas(self, dni, clave):
        """Esta función crea una vista de todas las transferencias registradas donde el beneficiario es el usuario seleccionado."""
        vista = list(self.cursor.execute("SELECT fecha_transfer, id_cuenta_origen, monto, concepto FROM transferencias WHERE id_cuenta_destino = ?;", (dni,)))
        datos_desencriptados = []
        for dato in vista[0]:
            dato_desencriptado = self.__criptografia.decrypt_mis_datos(clave, nonce, dato)
            datos_desencriptados.append(dato_desencriptado)
        return datos_desencriptados




