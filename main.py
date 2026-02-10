import os
import subprocess
import time
import socket
import fcntl
import struct
import psutil
from psutil import Process, STATUS_RUNNING
import threading
import signal
import time
import mariadb
import requests
import schedule
from functools import partial

#from ClaseTimer import Temporizador_offDelay
from datetime import timedelta, datetime

import setproctitle

setproctitle.setproctitle("ServerDomo-InternetChecker")

# Dirección a verificar (puede ser un servidor confiable como Google/Bing)
CHECK_HOST = "bing.com"
# Interfaces de red Wifi
WIFI_INTERFACE = "wlan0"
# Interfaces de red cable
CABLE_INTERFACE = "eth0"
# Interfaces de red via USB desde el celular (Dongle 4g)
USB_INTERFACE = "eth1"
# Interfaces de red a traves de Bluetooh usando Celular estandar
BLUETOOH_INTERFACE = "bnep0"
# Interfaces de red a traves auxiliares de Bluetooh y necesarias para el uso en determinadas funciones
BLUETOOH_INTERFACE_aux = "C0\:17\:4D\:2C\:8E\:C6" #"60\:72\:0B\:44\:E3\:3D"
BLUETOOH_INTERFACE_aux2 = "C0:17:4D:2C:8E:C6"
#Nombre Conexión Fibra
Fibra = "RedWifi6_Mesh"
#Nombre Conexión Celular Dash
Celular_USB = "ConexCelularDash"
#Modem USB
Modem_USB = "ModemUsb"
#Nombre Conexión Galaxy
Celular_Bluetooh = "RedGalaxyJ2Prime"

# Abrir el archivo de texto en modo lectura para obatener datos de usuario.
with open("/home/villafapd/Documents/ConfigEspeciales/BotTelegram.txt", "r") as archivo:
	# Leer las líneas del archivo
	lineas = archivo.readlines()
# Inicializar las variables
USER = ""
PASSWORD = ""
idBot = ""
idGrupo = ""
idmio = ""

# Procesar las lineas del archivo
for linea in lineas:
	if linea.startswith("idBot_CasaDanielBot"):
		idBot = linea.split("=")[1].strip().strip("'")
	elif linea.startswith("idGrupo"):
		idGrupo = linea.split("=")[1].strip().strip("'")
	elif linea.startswith("idmio"):
		idmio = linea.split("=")[1].strip().strip("'") 
	elif linea.startswith("USER"):
		USER = linea.split("=")[1].strip().strip("'")
	elif linea.startswith("PASSWORD"):
		PASSWORD = linea.split("=")[1].strip().strip("'")

#........................................................................................#Aqui se debe configurar que interface se usará y que tipo de conexion a internet se usará
#........................................................................................
INTERFACE_01 = WIFI_INTERFACE
INTERFACE_02 = USB_INTERFACE
TIPO_CONEXION_01 = Fibra
TIPO_CONEXION_02 = Modem_USB 
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------

#@profile
def watchDog () :
	Consulta ="UPDATE Configserver SET WatchDog = %s WHERE ID_Servidor = %s"
	Parametros = ("WatchDog_OK", "3")
	SQLCMD_To_MariaDB(Consulta, Parametros)	
	del Consulta, Parametros
	
#@profile	
def PID_Proceso(): 
	# Obtén el PID de tu proceso
	pid = os.getpid()
	#Crea un objeto Process
	p = psutil.Process(pid)
	# Obtén la información de la CPU
	
	#print_terminal("PID: " + str(p.pid))
	#print_terminal("Estado Proceso: " + str(p.status))
	if p.status() == STATUS_RUNNING:
		#print("DomoServer está corriendo y disponible como servidor")
		ST_IntChecker = "Corriendo"
	else:
		#print_terminal ("DomoServer no está disponible")
		ST_IntChecker = "Parado"
	
	Consulta ="UPDATE Configserver SET PID_Asignado = %s, EstadoServer = %s WHERE NombreServer = %s" 
	Parametros = (str(p.pid), ST_IntChecker, "InternetChecker")
	SQLCMD_To_MariaDB(Consulta, Parametros)
	del Consulta, Parametros

def get_default_route_ip(interface):
	try:
		result = subprocess.run(
			['nmcli', '-t', '-f', 'IP4.GATEWAY', 'device', 'show', interface],
			stdout=subprocess.PIPE,
			text=True
		)
		ip_address = result.stdout.strip().split(':')[-1]  # Extrae solo la IP
		return ip_address if ip_address else None
	except Exception as e:
		return None

#Reestablecer el valor de ipv4.route-metric ""
def reset_route_metric(connection_name):
	command = f"nmcli connection modify {connection_name} ipv4.route-metric \"\""
	subprocess.run(command, shell=True)
	print(f"El valor de 'ipv4.route-metric' para '{connection_name}' se ha restablecido.")

#Borrar la conexión de red e internet completa y no la solo la conexion de internet
def delete_connection(connection_name):
	command = f"nmcli connection delete {connection_name}"
	subprocess.run(command, shell=True)
	print(f"La conexión '{connection_name}' ha sido eliminada.")

def enviarMensaje(mensaje):
	url = f'https://api.telegram.org/bot{idBot}/sendMessage'
	requests.post(url, data={'chat_id': idGrupo, 'text': mensaje, 'parse_mode': 'HTML'})
	print("Mensaje de Respuesta Telegram vía url api")

def enviarMensaje_a_mi(mensaje):
	url = f'https://api.telegram.org/bot{idBot}/sendMessage'
	requests.post(url, data={'chat_id': idmio, 'text': mensaje, 'parse_mode': 'HTML'})
	print("Mensaje de Respuesta Telegram vía url api")

#Consulta a DB
def SQLCMD_To_MariaDB(Consulta, Parametros):
	conn = mariadb.connect(user=USER, password=PASSWORD, database="homeserver")  #, host="127.0.0.1", port=3306, 
	cur = conn.cursor()
	cur.execute (Consulta, Parametros) 
	#Para confirmar los cambios
	conn.commit()
	#Cerrar la conexión
	cur.close()
	conn.close()
 
#Hora y Fecha del sistema
def HoraFecha():
	ahora = datetime.now()#.time()
	date = datetime.now().today()
	hora_actual = ahora.strftime("%H:%M:%S")
	hora = ahora.hour
	hora = f"{hora:02d}"
	minutos = ahora.minute
	minutos = f"{minutos:02d}"
	segundos = ahora.second
	segundos = f"{segundos:02d}"
	dia = date.day
	dia = f"{dia:02d}"
	mes = date.month
	mes = f"{mes:02d}"
	ano = str(date.year)
	return hora, minutos, segundos, dia, mes, ano

#Activar conexion de red e internet
def activate_connection(connection_name):
	command = f"nmcli connection up {connection_name}"
	result = subprocess.run(command, shell=True, capture_output=True, text=True)

	if result.returncode == 0:
		print(f"La conexión '{connection_name}' se activó correctamente.")
		return True
	else:
		print(f"Error al activar la conexión '{connection_name}':\n{result.stderr}")
		return False

#desactivar conexion de red e internet
def deactivate_connection(connection_name):
	command = f"nmcli connection down {connection_name}"
	result = subprocess.run(command, shell=True, capture_output=True, text=True)

	if result.returncode == 0:
		print(f"La conexión '{connection_name}' se desactivó correctamente.")
		return True
	else:
		print(f"Error al desactivar la conexión '{connection_name}':\n{result.stderr}")
		return False     

#Modificacion del valor de la metrica en la tabla route y no es temporal
def set_route_metric(connection_name, metric_value):
	command = f"sudo nmcli connection modify {connection_name} ipv4.route-metric {metric_value}"
	subprocess.run(command, shell=True)
	print(f"Se ha establecido 'ipv4.route-metric' en {metric_value} para '{connection_name}'.")
 
#Modificacion Valor de la metrica en la tabla route y es temporal. Se borra al reiniciar la pc
def set_route_metric_temporal(interface, gateway, metric):
	"""Configura la ruta predeterminada para una interfaz."""
	try:
		# Agrega la ruta predeterminada
		subprocess.check_output(
			f"ip route add default via {gateway} dev {interface} metric {metric}",
			shell=True,
			stderr=subprocess.DEVNULL,
		)
	except subprocess.CalledProcessError:
		pass  # Maneja el error si el comando falla

	try:
		# Elimina rutas predeterminadas conflictivas
		subprocess.check_output(
			f"ip route del default dev {interface}",
			shell=True,
			stderr=subprocess.DEVNULL,
		)
	except subprocess.CalledProcessError:
		pass  # Maneja el error si el comando falla

#Modificacion del valor de la prioridad de conexion automatica de la interface de red
def set_connection_priority(connection_name, priority):
	command = f"nmcli connection modify {connection_name} connection.autoconnect-priority {priority}"
	subprocess.run(command, shell=True)
	print(f"Prioridad de conexión de '{connection_name}' establecida en {priority}")

#Chequeo de interface de red este habilitada 
def check_interface_status(interface):
	try:
		active_interfaces = psutil.net_if_stats()
		is_up = active_interfaces[interface].isup
		return is_up
	except Exception as e:
		return None
 
#Obtener el nombre de la conexion de red local
"""
def nombre_conexion(interface):
	result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE,CONNECTION', 'device'], stdout=subprocess.PIPE, text=True)

	for line in result.stdout.split('\n'):
		if line:
			device, connection = line.split(':')
			if device == interface:
				nombre_conex = connection if connection != "--" else None
				return nombre_conex
"""

# Obtener el nombre de la conexi�n de red local para una interfaz espec�fica
def nombre_conexion(interface):
	comando = f"nmcli -t -f DEVICE,CONNECTION device | grep '^{interface}:' | cut -d: -f2"
	result = subprocess.run(comando, shell=True, stdout=subprocess.PIPE, text=True)
	nombre = result.stdout.strip()
	return nombre

#Obtener el nombre de la conexion de red local
def nombre_conexion_cel(interface):
	result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE,CONNECTION', 'device'], stdout=subprocess.PIPE, text=True)

	for line in result.stdout.split('\n'):
		if line:
			partes = line.split(':')
			device = ":".join(partes[:-1])  # Une las partes para preservar los ":"
			if device == interface:
				# El último elemento es el nombre de la conexión
				nombre_conex = partes[-1]
				return nombre_conex

#Procesamiento para obtener la IP de la interface de red
def get_ip_address(ifname):
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		return socket.inet_ntoa(fcntl.ioctl(
			sock.fileno(),
			0x8915,  # SIOCGIFADDR
			struct.pack('256s', ifname[:15].encode('utf-8'))
		)[20:24])
	except OSError:
		return None

#Obtener la IP de la interface de red
def ip_interface(iface):
	try: 
		ip = get_ip_address(iface)
		return ip
	except Exception as e:
		print(e)
		return "0.0.0.0"  

#Funcion que realizar el chequeo de todo
def check_connectivity(interface): #, con_prio, val_metric
	"""Verifica la conectividad a Internet usando ping."""
	try:
		subprocess.check_output(
			["ping", "-c", "4", "-I", interface, CHECK_HOST],
			stderr=subprocess.STDOUT
		)
		St = "Conectado"
		return St #, ip, connections, is_up

	except subprocess.CalledProcessError:
		St = "Desconectado" 
		return St #, ip, connections,is_up

#Modificacion de las rutas y es temporal. Se borra al reiniciar la pc
def add_route(interface, gateway):
	try:
		# Agrega la ruta predeterminada
		#Ej:  sudo ip route add default via 192.168.42.129 dev eth1
		subprocess.check_output(
			f"sudo ip route add default via {gateway} dev {interface} metric 10",
			shell=True,
			stderr=subprocess.DEVNULL,
		)
		print(f"Se agregó la Ruta correctamente para la interface {interface} y gateway {gateway}")
	except subprocess.CalledProcessError:
		print(f"NO se pudo agregar la Ruta correctamente para la interface {interface} y gateway {gateway}")
		pass  # Maneja el error si el comando falla

def del_route(interface):
	try:
		# Elimina rutas predeterminadas 
		#Ej:  sudo ip route del default dev wlan0
		# sudo ip route del default
		subprocess.check_output(
			f"sudo ip route del default", #dev {interface}
			shell=True,
			stderr=subprocess.DEVNULL,
		)
		print(f"Ruta borrada correctamente para la interface {interface}")
	except subprocess.CalledProcessError:
		print(f"NO se pudo borrar la Ruta correctamente para la interface {interface}")
		pass  # Maneja el error si el comando falla

def check_estado_conex_internet():
	#Verifico si la placa de red esta habilitada, conectada a la red local, con IP asignada y con conexion a internet
	try:
		if check_interface_status(INTERFACE_02) and check_connectivity(INTERFACE_02) == "Conectado" and ip_interface(INTERFACE_02) != "0.0.0.0":
			hora, minutos, segundos, dia, mes, ano = HoraFecha()
			print(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> La interface de red {INTERFACE_02} con mombre asignado {nombre_conexion(INTERFACE_02)} está habilitada y está {check_connectivity(INTERFACE_02)} a internet y con dirección ip: {ip_interface(INTERFACE_02)}")	
		
			Aux_Conex_Celular = "True"
			Consulta ="UPDATE Configserver SET Aux_Conex_Celular = %s WHERE NombreServer = %s" 
			Parametros = (Aux_Conex_Celular, "InternetChecker")
			SQLCMD_To_MariaDB(Consulta, Parametros)	
			if check_connectivity(INTERFACE_01) == "Conectado":   
				enviarMensaje_a_mi(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> Conexión desde Fibra óptica y celular en estado normal y conectados a internet")
			else:
				enviarMensaje_a_mi(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> Conexión desde Fibra óptica DESCONECTADA a internet y conexion desde celular CONECTADA a internet")
		else:
			Aux_Conex_Celular = "False"
			Consulta ="UPDATE Configserver SET Aux_Conex_Celular = %s WHERE NombreServer = %s" 
			Parametros = (Aux_Conex_Celular, "InternetChecker")
			SQLCMD_To_MariaDB(Consulta, Parametros)	    
			if check_connectivity(INTERFACE_01) == "Conectado":
				enviarMensaje_a_mi("Conexión desde Fibra óptica en estado normal y CONECTADA a internet y conexion a internet desde celular DESCONECTADA")
			else:
				enviarMensaje_a_mi("Conexión desde Fibra óptica DESCONECTADA a internet y conexion desde celular a internet CONECTADA")    

	except Exception as e:
		print (f" {str(e)}, Función Chequeo de estado conexion a internet")
      

def ConexCelular():
	if check_interface_status(INTERFACE_02) and check_connectivity(INTERFACE_02) == "Conectado" and ip_interface(INTERFACE_02) != "0.0.0.0":
		hora, minutos, segundos, dia, mes, ano = HoraFecha()
		print(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> La interface de red {INTERFACE_02} con mombre asignado {nombre_conexion_cel(INTERFACE_02)} está habilitada y está {check_connectivity(INTERFACE_02)} a internet y con dirección ip: {ip_interface(INTERFACE_02)}")  
		#Envio Estado de conexion a la base de datos
		Consulta ="UPDATE Configserver SET ST_Conex_Celular = %s WHERE NombreServer = %s" 
		Parametros = ("Conectado", "InternetChecker")
		SQLCMD_To_MariaDB(Consulta, Parametros)   
	else:
		hora, minutos, segundos, dia, mes, ano = HoraFecha()
		print(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> La interface de red {INTERFACE_02} con mombre asignado {nombre_conexion_cel(INTERFACE_02)} no está habilitada")   
		#Envio Estado de conexion a la base de datos
		Consulta ="UPDATE Configserver SET ST_Conex_Celular = %s WHERE NombreServer = %s" 
		Parametros = ("Desconectado", "InternetChecker")
		SQLCMD_To_MariaDB(Consulta, Parametros) 

def ConexFibra():
	
	#Verifico si la placa de red esta habilitada, conectada a la red local, con IP asignada y con conexion a internet
	if check_interface_status(INTERFACE_01) and ip_interface(INTERFACE_01) == "192.168.68.100" and check_connectivity(INTERFACE_01) == "Conectado" and ip_interface(INTERFACE_01) != "0.0.0.0":
		hora, minutos, segundos, dia, mes, ano = HoraFecha()
		print(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> La interface de red {INTERFACE_01} con mombre asignado {nombre_conexion(INTERFACE_01)} está habilitada y está {check_connectivity(INTERFACE_01)} a internet y con dirección ip: {ip_interface(INTERFACE_01)}")	
		#Envio Estado de conexion a la base de datos
		Consulta ="UPDATE Configserver SET ST_Conex_Fibra = %s WHERE NombreServer = %s" 
		Parametros = ("Conectado", "InternetChecker")
		SQLCMD_To_MariaDB(Consulta, Parametros)		
		#Consulto a la DB el estado de la variable Aux_Conex_Celular
		query = "SELECT Aux_Conex_Celular FROM {} WHERE {} = {}".format('Configserver', 'ID_Servidor', str(3))
		with mariadb.connect(user=USER, password=PASSWORD, database="homeserver") as conn:
			with conn.cursor() as cur:
				cur.execute(query)
				while True:
					row = cur.fetchone()
					if row is None:
						break
					Aux_Conex_Celular = row[0]
			conn.commit()
		del conn, cur
		if Aux_Conex_Celular == "True":
			Ruta_Predeterminada = get_default_route_ip(INTERFACE_01)
			#Ruta_Predeterminada_USB = get_default_route_ip(INTERFACE_02)
			del_route(INTERFACE_02) #Borra la ruta por defecto de la Bluetooh/USB
			add_route(INTERFACE_01,Ruta_Predeterminada) #Se agrega ruta fibra por defecto 
			#add_route(INTERFACE_02,Ruta_Predeterminada_USB)   
			Aux_Conex_Celular = "False"
			Consulta ="UPDATE Configserver SET Aux_Conex_Celular = %s WHERE NombreServer = %s" 
			Parametros = (Aux_Conex_Celular, "InternetChecker")
			SQLCMD_To_MariaDB(Consulta, Parametros)	
			
	else:
		hora, minutos, segundos, dia, mes, ano = HoraFecha()
		print(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> La interface de red {INTERFACE_01} con mombre asignado {nombre_conexion(INTERFACE_01)} no está habilitada") 
		#Envio Estado de conexion a la base de datos
		Consulta ="UPDATE Configserver SET ST_Conex_Fibra = %s WHERE NombreServer = %s" 
		Parametros = ("Desconectado", "InternetChecker")
		SQLCMD_To_MariaDB(Consulta, Parametros)	   
		#Consulto a la DB el estado de la variable Aux_Conex_Celular
		query = "SELECT Aux_Conex_Celular FROM {} WHERE {} = {}".format('Configserver', 'ID_Servidor', str(3))
		with mariadb.connect(user=USER, password=PASSWORD, database="homeserver") as conn:
			with conn.cursor() as cur:
				cur.execute(query)
				while True:
					row = cur.fetchone()
					if row is None:
						break
					Aux_Conex_Celular = row[0]
			conn.commit()
		del conn, cur
  
		#Envio de mensaje de aviso de corte de conexion
		#enviarMensaje_a_mi("Conexión a internet desde Fibra óptica DESCONECTADA")
		if Aux_Conex_Celular == "False" and activate_connection(TIPO_CONEXION_02)== True:
			Ruta_Predeterminada = get_default_route_ip(INTERFACE_02)
			del_route(INTERFACE_01) #Borra la ruta por defecto de la wifi
			add_route(INTERFACE_02,Ruta_Predeterminada) #Se agrega ruta celular por defecto 
			Aux_Conex_Celular = "True" #Var Auxiliar para guardar en base datos
			Consulta ="UPDATE Configserver SET Aux_Conex_Celular = %s WHERE NombreServer = %s" 
			Parametros = (Aux_Conex_Celular, "InternetChecker")
			SQLCMD_To_MariaDB(Consulta, Parametros)		
			hora, minutos, segundos, dia, mes, ano = HoraFecha() 
			enviarMensaje_a_mi(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> Conexión a internet conmutada a Celular por fallo en conexión de fibra óptica")
			#Envio TRUE a la variable Aux_Conex_Celular a la base de datos		
			
		elif Aux_Conex_Celular == "False" and activate_connection(TIPO_CONEXION_02)== False:
			#enviarMensaje_a_mi("Fallo en la conmutación de la conexión a internet a través de Celular_Bluetooh. \n Próximo intento de conmutación a celular en 3 segundos. ")
			print("Espera de 3 seg. para nuevo reintentoo")
			time.sleep(3)
			if activate_connection(TIPO_CONEXION_02):
				Ruta_Predeterminada = get_default_route_ip(INTERFACE_02)
				del_route(INTERFACE_01) #Borra la ruta por defecto de la wifi
				add_route(INTERFACE_02,Ruta_Predeterminada) #Se agrega ruta celular por defecto        
				#enviarMensaje_a_mi("Luego del reintento en la conmutación de la conexión a internet a través de Celular_Bluetooh, se ha conectado exitosamente.")
				enviarMensaje_a_mi("Conexión a internet conmutada a Celular y CONECTADA")
				#Envio TRUE a la variable Aux_Conex_Celular a la base de datos
				Aux_Conex_Celular = "True"
				Consulta ="UPDATE Configserver SET Aux_Conex_Celular = %s WHERE NombreServer = %s" 
				Parametros = (Aux_Conex_Celular, "InternetChecker")
				SQLCMD_To_MariaDB(Consulta, Parametros)				
	
			else:
				print("Fallo de reintento en la conmutación a la red celular. Espera de 30 seg. para reinicio de secuencia de conexión")		
			
def cerrar_programa(signal, frame):
	print("\nPrograma interrumpido por el usuario. Cerrando...")
	print("Cerrando Hilos y Chauuuu")   
	exit(0)




if __name__ == "__main__":
	#Envio de estado de PID proceso a la DB
	PID_Proceso()
	#Envio de estado de Watchdog a la DB
	schedule.every(5).seconds.do(partial(watchDog))
   
	#Se establece la prioridad de conexion de cada interface de red
	set_connection_priority(TIPO_CONEXION_01,200) #Conexion de fibra
	set_connection_priority(TIPO_CONEXION_02,100) #Conexion celular
	set_connection_priority("ConexFibraMesh",50) #conexion de fibra a traves de cable red usando la red mesh
	#chequeo del estado de conexion a internet desde celular 
	check_estado_conex_internet()			
	# Se ejecuta la función una vez antes al inicio del programa antes del periodo de 10 seg. 
	ConexFibra()      
	ConexCelular() 	
	# Se ejecutan cada 20 y 40 segundos
	schedule.every(20).seconds.do(partial(ConexFibra))
	schedule.every(40).seconds.do(partial(ConexCelular))		
	while True:
			# Manejar el cierre del terminal
			signal.signal(signal.SIGTERM, cerrar_programa)
			#Manejar el cierre del programa con interrupcion de teclado ctrl+c
			signal.signal(signal.SIGINT, cerrar_programa) 
			schedule.run_pending()
			time.sleep(3)   


