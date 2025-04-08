import os
import subprocess
import time
import socket
import fcntl
import struct
import psutil
import threading
import signal
import time
import mariadb
import requests


from ClaseTimer import Temporizador_offDelay
from datetime import timedelta, datetime

# Dirección a verificar (puede ser un servidor confiable como Google)
CHECK_HOST = "bing.com"
# Interfaces de red
WIFI_INTERFACE = "wlan0"
CABLE_INTERFACE = "eth0"
USB_INTERFACE = "eth1"
#Nombre Conexión
Fibra = "RedWifi6_Mesh_IoT"
Celular = "ConexCelularDash"



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
	# Abrir el archivo de texto en modo lectura
	with open("/home/villafapd/Documents/ConfigEspeciales/BotTelegram.txt", "r") as archivo:
		# Leer las líneas del archivo
		lineas = archivo.readlines()

	# Inicializar las variables
	idBot = ""
	idGrupo = ""

	# Procesar las lineas del archivo
	for linea in lineas:
		if linea.startswith("idBot"):
			idBot = linea.split("=")[1].strip().strip("'")
		elif linea.startswith("idGrupo"):
			idGrupo = linea.split("=")[1].strip().strip("'")
		elif linea.startswith("idmio"):
			idmio = linea.split("=")[1].strip().strip("'")

	url = f'https://api.telegram.org/bot{idBot}/sendMessage'
	requests.post(url, data={'chat_id': idGrupo, 'text': mensaje, 'parse_mode': 'HTML'})
	print("Mensaje de Respuesta Telegram vía url api")

def enviarMensaje_a_mi(mensaje):
	# Abrir el archivo de texto en modo lectura
	with open("/home/villafapd/Documents/ConfigEspeciales/BotTelegram.txt", "r") as archivo:
		# Leer las líneas del archivo
		lineas = archivo.readlines()

	# Inicializar las variables
	idBot = ""
	idmio = ""

	# Procesar las lineas del archivo
	for linea in lineas:
		if linea.startswith("idBot"):
			idBot = linea.split("=")[1].strip().strip("'")
		elif linea.startswith("idGrupo"):
			idGrupo = linea.split("=")[1].strip().strip("'")
		elif linea.startswith("idmio"):
			idmio = linea.split("=")[1].strip().strip("'")

	url = f'https://api.telegram.org/bot{idBot}/sendMessage'
	requests.post(url, data={'chat_id': idmio, 'text': mensaje, 'parse_mode': 'HTML'})
	print("Mensaje de Respuesta Telegram vía url api")

#Consulta a DB
def SQLCMD_To_MariaDB(Consulta, Parametros):
	# Abrir el archivo de texto en modo lectura
	with open("/home/villafapd/Documents/ConfigEspeciales/BotTelegram.txt", "r") as archivo:
		# Leer las líneas del archivo
		lineas = archivo.readlines()
	# Inicializar las variables
	USER = ""
	PASSWORD = ""
	# Procesar las lineas del archivo
	for linea in lineas:
		if linea.startswith("USER"):
			USER = linea.split("=")[1].strip().strip("'")
		elif linea.startswith("PASSWORD"):
			PASSWORD = linea.split("=")[1].strip().strip("'")
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
	active_interfaces = psutil.net_if_stats()
	is_up = active_interfaces[interface].isup
	return is_up
 
#Obtener el nombre de la conexion de red local
def nombre_conexion(interface):
	result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE,CONNECTION', 'device'], stdout=subprocess.PIPE, text=True)

	for line in result.stdout.split('\n'):
		if line:
			device, connection = line.split(':')
			if device == interface:
				nombre_conex = connection if connection != "--" else None
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
			["ping", "-c", "3", "-I", interface, CHECK_HOST],
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
			f"sudo ip route add default via {gateway} dev {interface}",
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
		subprocess.check_output(
			f"sudo ip route del default dev {interface}",
			shell=True,
			stderr=subprocess.DEVNULL,
		)
		print(f"Ruta borrada correctamente para la interface {interface}")
	except subprocess.CalledProcessError:
		print(f"NO se pudo borrar la Ruta correctamente para la interface {interface}")
		pass  # Maneja el error si el comando falla


def ConexCelular():
	if check_interface_status(USB_INTERFACE) and check_connectivity(USB_INTERFACE) == "Conectado" and ip_interface(USB_INTERFACE) != "0.0.0.0":
		hora, minutos, segundos, dia, mes, ano = HoraFecha()
		print(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> La interface de red {USB_INTERFACE} con mombre asignado {nombre_conexion(USB_INTERFACE)} está habilitada y está {check_connectivity(USB_INTERFACE)} a internet y con dirección ip: {ip_interface(USB_INTERFACE)}")  
		#Envio Estado de conexion a la base de datos
		Consulta ="UPDATE Configserver SET ST_Conex_Celular = %s WHERE NombreServer = %s" 
		Parametros = ("Conectado", "DomoServer")
		SQLCMD_To_MariaDB(Consulta, Parametros)   
	else:
		hora, minutos, segundos, dia, mes, ano = HoraFecha()
		print(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> La interface de red {USB_INTERFACE} con mombre asignado {nombre_conexion(USB_INTERFACE)} no está habilitada")   
		#Envio Estado de conexion a la base de datos
		Consulta ="UPDATE Configserver SET ST_Conex_Celular = %s WHERE NombreServer = %s" 
		Parametros = ("Desconectado", "DomoServer")
		SQLCMD_To_MariaDB(Consulta, Parametros) 

def ConexFibra():
	
	#Verifico si la placa de red esta habilitada, conectada a la red local, con IP asignada y con conexion a internet
	if check_interface_status(WIFI_INTERFACE) and ip_interface(WIFI_INTERFACE) == "192.168.68.100" and check_connectivity(WIFI_INTERFACE) == "Conectado" and ip_interface(WIFI_INTERFACE) != "0.0.0.0":
		hora, minutos, segundos, dia, mes, ano = HoraFecha()
		print(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> La interface de red {WIFI_INTERFACE} con mombre asignado {nombre_conexion(WIFI_INTERFACE)} está habilitada y está {check_connectivity(WIFI_INTERFACE)} a internet y con dirección ip: {ip_interface(WIFI_INTERFACE)}")	
		#Envio Estado de conexion a la base de datos
		Consulta ="UPDATE Configserver SET ST_Conex_Fibra = %s WHERE NombreServer = %s" 
		Parametros = ("Conectado", "DomoServer")
		SQLCMD_To_MariaDB(Consulta, Parametros)		
		# Abrir el archivo de texto en modo lectura
		with open("/home/villafapd/Documents/ConfigEspeciales/BotTelegram.txt", "r") as archivo:
			# Leer las líneas del archivo
			lineas = archivo.readlines()
		# Inicializar las variables
		USER = ""
		PASSWORD = ""
		# Procesar las lineas del archivo
		for linea in lineas:
			if linea.startswith("USER"):
				USER = linea.split("=")[1].strip().strip("'")
			elif linea.startswith("PASSWORD"):
				PASSWORD = linea.split("=")[1].strip().strip("'")
		#Consulto a la DB el estado de la variable Aux_Conex_Celular
		query = "SELECT Aux_Conex_Celular FROM {} WHERE {} = {}".format('Configserver', 'ID_Servidor', str(1))
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
			if activate_connection(Fibra):
				deactivate_connection(Celular)
				Aux_Conex_Celular = "False"
				Consulta ="UPDATE Configserver SET Aux_Conex_Celular = %s WHERE NombreServer = %s" 
				Parametros = (Aux_Conex_Celular, "DomoServer")
				SQLCMD_To_MariaDB(Consulta, Parametros)	
			
	else:
		hora, minutos, segundos, dia, mes, ano = HoraFecha()
		print(f"Hora: {hora}:{minutos}:{segundos} | Fecha: {dia}-{mes}-{ano} ---> La interface de red {WIFI_INTERFACE} con mombre asignado {nombre_conexion(WIFI_INTERFACE)} no está habilitada") 
		#Envio Estado de conexion a la base de datos
		Consulta ="UPDATE Configserver SET ST_Conex_Fibra = %s WHERE NombreServer = %s" 
		Parametros = ("Desconectado", "DomoServer")
		SQLCMD_To_MariaDB(Consulta, Parametros)	 
		with open("/home/villafapd/Documents/ConfigEspeciales/BotTelegram.txt", "r") as archivo:
			# Leer las líneas del archivo
			lineas = archivo.readlines()
		# Inicializar las variables
		USER = ""
		PASSWORD = ""
		# Procesar las lineas del archivo
		for linea in lineas:
			if linea.startswith("USER"):
				USER = linea.split("=")[1].strip().strip("'")
			elif linea.startswith("PASSWORD"):
				PASSWORD = linea.split("=")[1].strip().strip("'")
  
		#Consulto a la DB el estado de la variable Aux_Conex_Celular
		query = "SELECT Aux_Conex_Celular FROM {} WHERE {} = {}".format('Configserver', 'ID_Servidor', str(1))
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
		if Aux_Conex_Celular == "False" and activate_connection(Celular)== True:
			Ruta_Predeterminada = get_default_route_ip(USB_INTERFACE)
			del_route(WIFI_INTERFACE) #Borra la ruta por defecto de la wifi
			add_route(USB_INTERFACE,Ruta_Predeterminada) #Se agrega ruta celular por defecto 
			Aux_Conex_Celular = "True" #Var Auxiliar para guardar en base datos
			Consulta ="UPDATE Configserver SET Aux_Conex_Celular = %s WHERE NombreServer = %s" 
			Parametros = (Aux_Conex_Celular, "DomoServer")
			SQLCMD_To_MariaDB(Consulta, Parametros)		
			#enviarMensaje_a_mi("Conexión a internet conmutada a Celular y CONECTADA")
			#Envio TRUE a la variable Aux_Conex_Celular a la base de datos		
			
		elif Aux_Conex_Celular == "False" and activate_connection(Celular)== False:
			#enviarMensaje_a_mi("Fallo en la conmutación de la conexión a internet a través de Celular. \n Próximo intento de conmutación a celular en 3 segundos. ")
			print("Espera de 3 seg. para nuevo reintentoo")
			time.sleep(3)
			if activate_connection(Celular):
				#enviarMensaje_a_mi("Luego del reintento en la conmutación de la conexión a internet a través de Celular, se ha conectado exitosamente.")
				deactivate_connection(Fibra)
				#enviarMensaje_a_mi("Conexión a internet conmutada a Celular y CONECTADA")
				#Envio TRUE a la variable Aux_Conex_Celular a la base de datos
				Aux_Conex_Celular = "True"
				Consulta ="UPDATE Configserver SET Aux_Conex_Celular = %s WHERE NombreServer = %s" 
				Parametros = (Aux_Conex_Celular, "DomoServer")
				SQLCMD_To_MariaDB(Consulta, Parametros)				
	
			else:
				print("Fallo de reintento en la conmutación a la red celular. Espera de 30 seg. para reinicio de secuencia de conexión")
   
			
		  
		
			
def cerrar_programa(signal, frame):
	print("\nPrograma interrumpido por el usuario. Cerrando...")
	Ctrl_conex_fibra.cancel()
	#Ctrl_conex_celular.cancel()
	print("Cerrando Hilos y Chauuuu")   
	exit(0)




if __name__ == "__main__":
	#Se estable la prioridad de conexion de cada interface de red
	set_connection_priority(Fibra,200) #Conexion de fibra
	set_connection_priority(Celular,100) #Conexion celular
	set_connection_priority("ConexFibraMesh",50) #conexion de fibra a traves de cable red usando la red mesh
	# Se ejecuta la función una vez antes al inicio del programa antes del periodo de 10 seg. 
	ConexFibra()      
	Ctrl_conex_fibra = Temporizador_offDelay(10,ConexFibra)
	Ctrl_conex_fibra.start()#/.cancel    
	#ConexCelular() 	
	#Ctrl_conex_celular = Temporizador_offDelay(60,ConexCelular)
	#Ctrl_conex_celular.start()#/.cancel  


	while True:
		# Manejar el cierre del terminal
			signal.signal(signal.SIGTERM, cerrar_programa)
			#Manejar el cierre del programa con interrupcion de teclado ctrl+c
			signal.signal(signal.SIGINT, cerrar_programa) 


