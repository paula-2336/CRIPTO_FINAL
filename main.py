from meswap import MeSwap
import json
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import ssl
import smtplib
import random
from caag import consultar_saldo
from json_func import load_users, save_users, register_user, login_user, send_mail, desencriptar,verificarfirma, registrar_usuario_con_certificado

print("Bienvenido a Vanguard Trust Bank")
x = input("Pulse 1 si ya tiene una cuenta, 2 si quiere registrarse: ")

if "2" == x:
    opcion = input("¿Desea registrar un usuario? (S/N): ")
    if opcion.lower() == 's':
        username = input("Ingrese su nombre de usuario: ")
        password = input("Ingrese su contraseña: ")
        registrar_usuario_con_certificado(username, password)

    if register_user(_usuario, _contrasena):
        opcion = input("Una vez logueado, puede realizar las siguientes operaciones: \n 1. Consultar saldo \n 2. Transferir dinero \n 3. Ver el historial de transacciones \n 4. Salir\n")
        
        if opcion == "1":
            # Opción para consultar saldo
            mensaje, firma = consultar_saldo(_usuario)
            password = input("Ingrese su contraseña de nuevo para realizar la operación: ")
            verificarfirma(mensaje, firma, _usuario)
            desencriptar(password)

        elif opcion == "2":
            # Opción para transferir dinero
            cuenta_destino = input("Ingrese el número de cuenta de destino: ")
            monto = input("Ingrese el monto a transferir: ")
            mensaje, firma = transferir_dinero(_usuario, cuenta_destino, monto)
            password = input("Ingrese su contraseña de nuevo para confirmar la transferencia: ")
            verificarfirma(mensaje, firma, _usuario)
            desencriptar(password)
            print(f"Transferencia de {monto} a la cuenta {cuenta_destino} realizada con éxito.")

        elif opcion == "3":
            # Opción para ver historial de transacciones
            historial, firma = ver_historial(_usuario)
            password = input("Ingrese su contraseña de nuevo para acceder al historial: ")
            verificarfirma(historial, firma, _usuario)
            desencriptar(password)
            print("Historial de transacciones: ")
            print(historial)

        elif opcion == "4":
            print("Gracias por usar Vanguard Trust Bank, hasta pronto")
            exit()

elif "1" == x:
    print("Para ingresar introduzca usuario y contraseña")
    _usuario = input("Usuario: ")
    _contrasena = input("Contraseña: ")
    if login_user(_usuario, _contrasena):
        opcion= input("Una vez logeado, puede realizar las siguientes operaciones: \n 1. Consultar saldo \n 2.Salir")
        if opcion == "1":
            mensaje, firma=consultar_saldo(_usuario)
            password = input("Ingrese su contraseña de nuevo para relaizar la operacion: ")
            verificarfirma(mensaje,firma, _usuario)
            desencriptar(password)
        elif opcion == "2":
            print("Gracias por usar Vanguard Trust Bank, hasta pronto")
            exit()

else:
    print("Opcion no valida")
