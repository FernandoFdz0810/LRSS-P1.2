import sys
import os
import socket
import select
import queue
import datetime
import platform
import mimetypes
import string
import pymysql
import ssl

# Conexion con Base de datos

if sys.argv[1] == "Persistente":
    Tipo_Conexion = "Keep-Alive"
    Keep_Alive = "timeout=10, max=1000"

if sys.argv[1] == "No-Persistente":
    Tipo_Conexion = "close"
    Keep_Alive = " "


Conexion_SQL = pymysql.connect(host='localhost', user='ismael', passwd='ismael', db='LRSS2')
cur = Conexion_SQL.cursor()

# Establecer el host y el puerto del servidor
server_address = ('192.168.0.31', 8080)

# Crear un objeto socket
try:
    socketserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except Exception as e:
    print("Error creando el socket: ", e)

# Configurar el socket para reutilizar la dirección del servidor después de cerrar la conexión
socketserv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Enlazar el objeto socket al host y puerto especificados
try:
    socketserv.bind(server_address)
except Exception as e:
    print("Error en la asociación del socket: ", e)

# Escuchar por conexiones entrantes
socketserv.listen(5)

if sys.argv[2] == "HTTPS":
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile='/etc/ssl/web.crt', keyfile='/etc/ssl/web.key')
    secure_socket = ssl_context.wrap_socket(socketserv, server_side=True)


print('Escuchando en ip ', server_address[0], 'y puerto:', server_address[1])

if sys.argv[2] == "HTTP":
    entradas = [socketserv]  # Sockets de los que esperamos hacer lectura
elif sys.argv[2] == "HTTPS":
    entradas = [secure_socket]

salidas = []  # Sockets sobre los que esperamos escribir
cola_mensajes = {}  # Buffer de salida para conexiones de salida

if sys.argv[2] == "HTTP":
    Descriptor_socket_serv = socketserv
elif sys.argv[2] == "HTTPS":
    Descriptor_socket_serv = secure_socket

while entradas != -1:
    print('Esperando peticiones entrantes...\n')
    readable, writable, exceptional = select.select(entradas, salidas, entradas, 10)
    if len(readable) == 0:
        print("Servidor desconectado debido a temporizador 'timeout'")

    for s in readable:
        if s is Descriptor_socket_serv:
            # Un socket en modo lectura esta preparado para aceptar la conexion
            conexion, client_address = s.accept()
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

                entradas.pop()
                s.close()

            else:
                # Convertir los datos de entrada en una solicitud HTTP.

                solicitud = data.decode('utf-8')
                separacion = data.decode().split(' ')
                cabecera = separacion[0]
                archivo_pedido = separacion[1]
                nuevo_archivo_pedido = archivo_pedido.replace('/', '')
                if len(archivo_pedido) == 1:

                    nuevo_archivo_pedido = "index.html"

                # Con esto obtenemos la cabecera de una peticion HTTP, dependiento del tipo
                # de solicitud, realizaremos una acción u otra.
                print(solicitud, "\n")
                print(cabecera)
                print(nuevo_archivo_pedido)

                try:
                    if nuevo_archivo_pedido == "index.html":
                        file = open("index.html", 'r')
                        index = file.read()
                        file.close()

                    elif nuevo_archivo_pedido == "index2.html":

                        file = open("index2.html", 'r')
                        index = file.read()
                        file.close()

                    elif nuevo_archivo_pedido == "index3.html":

                        file = open("index3.html", 'r')
                        index = file.read()
                        file.close()

                    file = open("css/index.css", 'r')
                    response_css = file.read()
                    file.close()

                    if nuevo_archivo_pedido.endswith('.html'):
                        ruta_archivo_html = nuevo_archivo_pedido

                    ruta_archivo_css = "css/index.css"
                    tamaño_html = os.path.getsize(ruta_archivo_html)
                    tamaño_css = os.path.getsize(ruta_archivo_css)
                    tamaño_total = tamaño_css + tamaño_html
                    tamaño_total = str(tamaño_total)

                    if (archivo_pedido.endswith('/')):
                        mimetype = 'text/html'

                    elif (archivo_pedido.endswith('.html')):
                        mimetype = 'text/html'

                    elif (archivo_pedido.endswith('.css')):
                        mimetype = 'text/css'

                    elif (archivo_pedido.endswith('.png')):
                        mimetype = 'image/png'

                    if cabecera.startswith('GET'):

                        fecha_hora = datetime.datetime.now()
                        fecha_bytes = fecha_hora.strftime("%Y-%m-%d %H:%M:%S.%f")
                        plataforma = platform.system()
                        cabecera_1 = 'HTTP/1.1 200 OK\r\nDate: ' + fecha_bytes + '\r\nConnection: ' + Tipo_Conexion + '\r\nKeep-Alive: ' + Keep_Alive + '\r\nServidor:' + plataforma + '\r\nContent-type: ' + \
                            mimetype + '; charset=utf-8\r\nContent-length:' + tamaño_total + \
                            '\r\n\n{}'.format(index + '<style>' + response_css + '</style>')
                        print(cabecera_1)
                        try:
                            s.sendall(cabecera_1.encode())
                        except Exception as e:
                            exceptional.append(s)
                            print("Error al enviar los datos ", e)

                        entradas.pop()
                        s.close()
                        break

                    if cabecera.startswith('POST'):

                        datos_formulario = separacion[-1]
                        datos_formulario = datos_formulario.split('\r')[2]
                        datos_formulario = datos_formulario.split('&')
                        longitud = len(datos_formulario)

                        for i in range(longitud):
                            if i == 0:
                                Dni_Formulario = datos_formulario[i].split('=')
                                Dni_Formulario = dict([Dni_Formulario])
                            if i == 1:
                                Nombre_formulario = datos_formulario[i].split('=')
                                Nombre_formulario = dict([Nombre_formulario])

                            if i == 2:
                                Apellido_formulario = datos_formulario[i].split('=')
                                Apellido_formulario = dict([Apellido_formulario])

                            if i == 3:
                                Fecha_formulario = datos_formulario[i].split('=')
                                Fecha_formulario = dict([Fecha_formulario])

                        Dni_Formulario.update(Nombre_formulario)
                        Dni_Formulario.update(Apellido_formulario)
                        Dni_Formulario.update(Fecha_formulario)
                        Diccionario_Solicitud_Final = Dni_Formulario

                        Diccionario_Solicitud_Final = list(Diccionario_Solicitud_Final.values())
                        longitud = len(Diccionario_Solicitud_Final)

                        for i in range(longitud):
                            if i == 0:
                                DNI = Diccionario_Solicitud_Final[i]
                            if i == 1:
                                Nombre = Diccionario_Solicitud_Final[i]
                            if i == 2:
                                Apellido = Diccionario_Solicitud_Final[i]
                            if i == 3:
                                Fecha = Diccionario_Solicitud_Final[i]

                        sql = "INSERT INTO DatosFormulario (DNI, nombre, apellidos, fecha) VALUES (%s,%s,%s,%s)"
                        val = (DNI, Nombre, Apellido, Fecha)
                        cur.execute(sql, val)
                        Conexion_SQL.commit()

                        fecha_hora = datetime.datetime.now()
                        fecha_bytes = fecha_hora.strftime(
                            "%Y-%m-%d %H:%M:%S.%f")
                        plataforma = platform.system()
                        cabecera_1 = 'HTTP/1.1 200 OK\r\nDate: ' + fecha_bytes + '\r\nConnection: ' + Tipo_Conexion + '\r\nKeep-Alive: ' + Keep_Alive + '\r\nServidor:' + plataforma + \
                            '\r\nContent-type: ' + mimetype + '\r\nContent-length:' + tamaño_total + \
                            '\r\n{}'.format(
                                index + '<style>' + response_css + '</style>')
                        respuesta_final = cabecera_1
                        print(respuesta_final)
                        try:
                            s.sendall(respuesta_final.encode("utf-8"))
                        except Exception as e:
                            print("Error al enviar los datos ", e)
                            exceptional.append(s)
                        entradas.pop()
                        s.close()

                    break

                except Exception as e:
                    print("error: ", e)

        break

    for s in exceptional:
        print("Excepcion en el socket desde {}:{}", format(entradas[s]))
