import sys
import os
import socket
import select
import queue
import datetime
import platform
import mimetypes
from http.server import HTTPServer

# Establecer el host y el puerto del servidor
server_address = ('192.168.189.147', 8080)

# Crear un objeto socket
socketserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Configurar el socket para reutilizar la dirección del servidor después de cerrar la conexión
socketserv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Enlazar el objeto socket al host y puerto especificados
socketserv.bind(server_address)

# Escuchar por conexiones entrantes
socketserv.listen(5)
print('Escuchando en ip ', server_address[0], 'y puerto:', server_address[1])

"""
# Lista de sockets para selección
sockets_list = []

# Diccionario de clientes (socket: nombre de cliente)
clientes = {}
"""

entradas = [socketserv] #Sockets de los que esperamos hacer lectura
salidas = [] # Sockets sobre los que esperamos escribir
cola_mensajes = {} # Buffer de salida para conexiones de salida

# Cargamos el contenido del archivo HTML que se va a solicitar al servidor en una cadena.


while entradas:
    print('Esperando por conexiones...\n')
    readable, writable, exceptional = select.select(entradas, salidas, entradas)

    for s in readable:
        if s is socketserv:
            # Un socket en modo lectura esta preparado para aceptar la conexion
            conexion, client_address = socketserv.accept()
            print("Conexión procedente de ", client_address)
            conexion.setblocking(0)
            entradas.append(conexion)

            # A continuación le damos a la conexion una cola para los
            # datos que queremos enviar

            cola_mensajes[conexion] = queue.Queue()

        # La otra opcion la encontramos para una coonexión establecida
        # con un cliente que ha enviado datos.

        else:

            data = s.recv(1024)

            if not data:
                # Si no hay datos entrantes, significa que el cliente cerro la conexión.
                print('Conexión cerrada por {}:{}\n'.format(*client_address))

                entradas.remove(s)
            
            else:
                # Convertir los datos de entrada en una solicitud HTTP.

                solicitud = data.decode('utf-8')
                separacion = data.decode().split(' ')
                cabecera = separacion[0]
                archivo_pedido = separacion[1]
                # Con esto obtenemos la cabecera de una peticion HTTP, dependiento del tipo
                # de solicitud, realizaremos una acción u otra.
                print(solicitud,"\n")
                print(cabecera)
                print(archivo_pedido)

                try: 
                    file = open("index.html", 'r')
                    response = file.read() 
                    file.close()

                    ruta_archivo_html = "index.html"

                    tamaño_html = os.path.getsize(ruta_archivo_html)
                    tamaño_html = str(tamaño_html)

                    if(archivo_pedido.endswith('/')):
                        mimetype = 'text/html'

                    else:
                        mimetype = 'h'

                    if cabecera.startswith('GET'):
                        fecha_hora = datetime.datetime.now()
                        fecha_bytes = fecha_hora.strftime("%Y-%m-%d %H:%M:%S.%f")
                        plataforma = platform.system()
                        cabecera_1 = 'HTTP/1.1 200 OK\r\nDate: '+ fecha_bytes + '\r\nServidor:' + plataforma + '\r\nContent-type: ' + mimetype + '\r\nContent-length:' + tamaño_html + '\r\n'
                        respuesta_final = cabecera_1
                        respuesta_final += response
                        s.sendall(respuesta_final.encode("utf-8"))

                except Exception as e:
                    print("error: ",e)
    
    

    for s in exceptional:
        print("Excepcion en el socket desde {}:{}",format(entradas[s]))
        