import os 
import sqlite3
import shutil

def borrar_archivo_de_directorio(directorio):
    for archivo in os.listdir(directorio):
        if os.path.isfile(f"{directorio}/{archivo}"):
            os.remove(f"{directorio}/{archivo}")
        else:
            shutil.rmtree(f"{directorio}/{archivo}")
    


# Borramos todos los datos del base de datos
def borrar_archivo(archivo):
    try:
        os.remove(archivo)
    except FileNotFoundError:
        pass


def borrar_datos_base_de_datos():
    # Borramos el contenido de la base de datos test.db
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM transferencias")
    cursor.execute("DELETE FROM ingresos")
    cursor.execute("DELETE FROM cuentas")
    cursor.execute("DELETE FROM usuarios")

    conn.commit()
    conn.close()


def main():
    # Reseteamos la base de datos
    borrar_datos_base_de_datos()
    # Borramos los directorios con las claves de los usuarios
    borrar_archivo_de_directorio("./Certificados/Usuarios/")
    borrar_archivo_de_directorio("./Certificados/VanguardTrustBank/nuevoscerts/")
    borrar_archivo_de_directorio("./Certificados/VanguardTrustBank/solicitudes/")
    borrar_archivo("./Certificados/VanguardTrustBank/index.txt.attr")
    borrar_archivo("./Certificados/VanguardTrustBank/index.txt.attr.old")
    borrar_archivo("./Certificados/VanguardTrustBank/index.txt.old")
    borrar_archivo("./Certificados/VanguardTrustBank/serial.old")
    borrar_archivo("./Certificados/VanguardTrustBank/serial")
    borrar_archivo("./Certificados/VanguardTrustBank/index.txt")
    borrar_archivo("./Certificados/VanguardTrustBank/VanguardTrustBank.pem")

    os.chdir(f"./Certificados/VanguardTrustBank/")
    os.system(f"echo '01' > serial")
    os.system(f"touch index.txt")
    os.system(f"openssl req -x509 -newkey rsa:2048 -days 360 -out VanguardTrustBank.pem -outform PEM -config openssl-VanguardTrustBank.conf")
    os.chdir(f"../..")

if __name__ == "__main__":
    main()