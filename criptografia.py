import os
import base64
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import cryptography.exceptions 
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

class Cripto: 
############### GENERACIÓN Y VERIFICACIÓN DE LA CONTRASEÑA ###################
    @staticmethod
    def generar_contraseña(contraseña: str):
        """Generamos la contraseña que se guardará en la base de datos"""
        #A continuación generamos un salt aleatorio para cada contraseña
        salt = os.urandom(16)
        kdf = Scrypt(
            salt = salt,
            length = 256,
            n = 2**15,
            r = 8,
            p=1 )
        return base64.encodebytes(salt).decode('utf8'), \
                base64.encodebytes(kdf.derive(bytes(contraseña,encoding='utf8'))).decode('utf8')

    @staticmethod
    def validar_contraseña(contraseña:str, salt:str, hash:str) -> bool:
        """Verificamos mediante la clave y el salt que la contraseña es la correcta"""
        contraseña = bytes(contraseña, encodint='utf8')
        hash = base64.decodebytes(bytes(hash, encoding = 'utf8'))
        salt = base64.decodebytes(bytes(salt, encoding = 'utf8'))
        kdf = Scrypt(
            salt = salt,
            legnth = 256,
            n = 2**15,
            r = 8,
            p=1 )
        #A continuación comprobamos que la clave coincide con la contraseña
        try:
            kdf.verify(contraseña, hash)
        except cryptography.exceptions.InvalidKey:
            return False
        return True


############### DERIVACIONES DE CLAVE ###################

    @staticmethod
    def prim_deriv_clave_contraseña(contraseña:str):
        """Derivamos la clave de la contraseña por pimera vez"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm = hashes.SHA256(),
            length = 32,
            salt = salt,
            iterations = 480000
        )
        #Derivamos la clave de la contraseña
        clave = kdf.derive(bytes(contraseña, encoding="utf8"))
        return base64.encodebytes(salt).decode("utf8"), base64.encodebytes(clave).decode("utf8")

    
    @staticmethod
    def deriv_clave_contraseña(salt:str, contraseña:str):
        """ Derivamos una clave dados una contraseña y un salt"""
        salt = base64.decodebytes(bytes(salt, encoding="utf8"))
        kdf = PBKDF2HMAC(
            algoritmo = hashes.SHA256(),
            longitud = 32,
            salt = salt,
            iterations = 480000
        )
        #Derivamos la clave con la contraseña y el salt
        clave = kdf.derive(bytes(contraseña, encoding="utf8"))
        return base64.encodebytes(clave).decode("utf8")


############### ENCRIPTACIÓN Y DESENCRIPTACIÓN DE DATOS USANDO CHACHA20 ###################
    @staticmethod
    def encrypt_mis_datos(clave:str, datos:str):
        """ Enciptamos mis datos dada una clave y devolvemos nonce """
        clave = base64.decodebytes(bytes(clave, encoding="utf8"))
        datos = bytes(datos, encoding="utf8")
        chacha = ChaCha20Poly1305(clave)
        nonce = os.urandom(12)
        ct = chacha.encrypt(nonce, datos, None)
        return base64.encodebytes(nonce).decode("utf8"), base64.encodebytes(ct).decode("utf8")


    @staticmethod
    def decrypt_mis_datos(clave, nonce, datos):
        """Autenticamos y Desencriptamos los datos dados un nonce y una clave"""
        clave = base64.decodebytes(bytes(clave, encoding ="utf8"))
        nonce = base64.decodebytes(bytes(nonce, encoding = "utf8"))
        datos = base64.decodebytes(bytes(datos, encoding ="utf8"))
        #Procedemos a la desencriptación:
        chacha = ChaCha20Poly1305(clave)
        res = chacha.decrypt(nonce, datos, None)
        return res.decode("utf8")
