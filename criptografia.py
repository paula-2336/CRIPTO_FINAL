import os
import base64
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import cryptography.exceptions 
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import padding
import getpass


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
        contraseña = bytes(contraseña, encoding='utf8')
        hash = base64.decodebytes(bytes(hash, encoding = 'utf8'))
        salt = base64.decodebytes(bytes(salt, encoding = 'utf8'))
        kdf = Scrypt(
            salt = salt,
            length = 256,
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
            algorithm = hashes.SHA256(),
            length = 32,
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

    ############### IMPLEMENTACIÓN DE RSA ###################
    def generar_clave_privado_y_publica(self, contraseña, dni):
        # Creamos un directorio para guardar los certificados del usuario
        os.mkdir(f"./Certificados/Usuarios/{dni}")
        # generamos la contraseña privada
        contraseña = bytes(contraseña, encoding="utf8")
        # We generate the private key
        clave_privada = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # La guardamos en un archivo encriptado con la contraseña del usuario
        with open(f"./Certificados/Usuarios/{dni}/{dni}-key.pem", "wb") as f:
            f.write(clave_privada.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.BestAvailableEncryption(contraseña),
            ))

        # Generamos la request de firmar el certificado
        self.generate_csr(clave_privada, dni)
        self.generate_pem(dni)
    
    @staticmethod
    def generate_csr(private_key, dni):
        # Generamos la request de firmar el certificado del usuario
        csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "MADRID"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, dni),
            x509.NameAttribute(NameOID.COMMON_NAME, "vanguard_trust_bank.com"),
        ])).sign(private_key, hashes.SHA256())

        # Guardamos la request en el directorio de solicitudes
        with open(f"./Certificados/VanguardTrustBank/solicitudes/{dni}-csr.pem", "wb") as file:
            file.write(csr.public_bytes(serialization.Encoding.PEM))

    
    @staticmethod
    def generate_pem(dni):
        # Función que genera el certificado del usuario a partir de la request
        directorio_actual = os.getcwd()

        # Cambiar el directorio al de los certificados del banco
        os.chdir("./Certificados/VanguardTrustBank/")
        # Obtenemos la contraseña del banco para firmar el certificado del usuario
        contraseña = getpass.getpass("Enter your password: ")

        # Obtenemos el serial del certificado  
        with open("./serial", "rb") as file:
            file_data = file.read().decode("utf-8")

        # Firmamos el certificado del usuario con openssl
        os.system(f"openssl ca -in ./solicitudes/{dni}-csr.pem -notext -config "
                  f"./openssl-VanguardTrustBank.conf --passin pass:{contraseña}")

        # Copiamos el certificado del usuario a su directorio
        os.system(f"cp ./nuevoscerts/{file_data[:-1]}.pem "
                  f"../Usuarios/{dni}/{dni}-cert.pem")

        # Volvemos al directorio original
        os.chdir(directorio_actual)
    
    def obtener_clave_publica(self, dni):
        with open(f"./Certificados/Usuarios/{dni}/{dni}-cert.pem", "rb") as archivo_pem:
            datos_pem = archivo_pem.read()

        cert = x509.load_pem_x509_certificate(datos_pem)

        clave_publica = cert.public_key()

        pem_publica = clave_publica.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return base64.encodebytes(pem_publica).decode("utf8")
    
    def encriptar_asunto(self, remitente, beneficiario, asunto):
        clave_publica_remitente = self.obtener_clave_publica(remitente)
        clave_publica_beneficiario = self.obtener_clave_publica(beneficiario)
        clave_publica_remitente = base64.decodebytes(bytes(clave_publica_remitente, encoding="utf8"))
        clave_publica_beneficiario = base64.decodebytes(bytes(clave_publica_beneficiario, encoding="utf8"))

        clave_publica_remitente = serialization.load_pem_public_key(clave_publica_remitente)
        clave_publica_beneficiario = serialization.load_pem_public_key(clave_publica_beneficiario)

        # Encriptamos el asunto con la clave pública del beneficiario
        datos = bytes(asunto, encoding="utf8")
        datos_beneficiario = clave_publica_beneficiario.encrypt(
            datos,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Encriptamos la clave con la clave pública del remitente
        datos_remitente = clave_publica_remitente.encrypt(
            datos,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return (base64.encodebytes(datos_remitente).decode("utf8"), base64.encodebytes(datos_beneficiario).decode("utf8"))

    # Función que desencripta el asunto de un mensaje
    def desencriptar_asunto(self, dni, contraseña_clave_privada, asunto_ecnriptado):
        with open(f"./Certificados/Usuarios/{dni}/{dni}-key.pem", "rb") as archivo_pem:
            datos_pem = archivo_pem.read()
        
        contraseña_clave_privada = bytes(contraseña_clave_privada, encoding="utf8")
        clave_privada = load_pem_private_key(
            datos_pem,
            contraseña_clave_privada,
        )

        asunto_ecnriptado = base64.decodebytes(bytes(asunto_ecnriptado, encoding="utf8"))
        asunto = clave_privada.decrypt(
            asunto_ecnriptado,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return asunto.decode("utf8")
    
    def firmar_cantidad(self, dni, contraseña_clave_privada, cantidad):
        with open(f"./Certificados/Usuarios/{dni}/{dni}-key.pem", "rb") as archivo_pem:
            datos_pem = archivo_pem.read()
        
        contraseña_clave_privada = bytes(contraseña_clave_privada, encoding="utf8")
        clave_privada = load_pem_private_key(
            datos_pem,
            contraseña_clave_privada,
        )

        cantidad_str = str(cantidad)

        firma = clave_privada.sign(
            bytes(cantidad_str, encoding="utf8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return base64.encodebytes(firma).decode("utf8")
    
    def comprobar_firma_cantidad(self, dni, cantidad, firma):
        # Obtenemos la clave pública del usuario
        clave_publica = self.obtener_clave_publica(dni)
        clave_publica = base64.decodebytes(bytes(clave_publica, encoding="utf8"))
        clave_publica = serialization.load_pem_public_key(clave_publica)

        firma = base64.decodebytes(bytes(firma, encoding="utf8"))

        cantidad_str = str(cantidad)

        try:
            clave_publica.verify(
                firma,
                bytes(cantidad_str, encoding="utf8"),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except cryptography.exceptions.InvalidSignature:
            return False


    def verificar_cadena_certificado(self, dni):
        # Obtenemos el certificado del usuario
        with open(f"./Certificados/Usuarios/{dni}/{dni}-cert.pem", "rb") as archivo_pem:
            datos_pem = archivo_pem.read()

        cert = x509.load_pem_x509_certificate(datos_pem)

        # Obtenemos la cadena de certificados del banco
        with open("./Certificados/VanguardTrustBank/VanguardTrustBank.pem", "rb") as archivo_pem:
            datos_pem = archivo_pem.read()

        cert_banco = x509.load_pem_x509_certificate(datos_pem)

        # Verificamos que el certificado del usuario está firmado por el banco
        try:
            cert_banco.public_key().verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm,
            )
            return True
        except cryptography.exceptions.InvalidSignature:
            return False