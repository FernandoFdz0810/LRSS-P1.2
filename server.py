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
import requests
import base64

#Conexion con Base de datos

Conexion_SQL = pymysql.connect(host='localhost', user='fernando', passwd='Fernando0810_', db='LRSS2')
cur = Conexion_SQL.cursor()

# Establecer el host y el puerto del servidor
server_address = ('192.168.189.64', 8080)

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
print('Escuchando en ip ', server_address[0], 'y puerto:', server_address[1])

entradas = [socketserv] #Sockets de los que esperamos hacer lectura
salidas = [] # Sockets sobre los que esperamos escribir
cola_mensajes = {} # Buffer de salida para conexiones de salida

# Cargamos el contenido del archivo HTML que se va a solicitar al servidor en una cadena.


while entradas != -1:
    print('Esperando peticiones entrantes...\n')
    readable, writable, exceptional = select.select(entradas, salidas, entradas, 10)
    if len(readable) == 0:
        print("Servidor desconectado debido a temporizador 'timeout'")

    for s in readable:
        if s is socketserv:
            # Un socket en modo lectura esta preparado para aceptar la conexion
            try:
                conexion, client_address = socketserv.accept()
            except Exception as e:
                print("Error conectando servidor con el cliente: ", e)
                
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

                entradas.pop()
                s.close()
            
            else:
                # Convertir los datos de entrada en una solicitud HTTP.

                solicitud = data.decode('utf-8')
                separacion = data.decode().split(' ')
                cabecera = separacion[0]
                archivo_pedido = separacion[1]
                nuevo_archivo_pedido = archivo_pedido.replace('/','')
                # Con esto obtenemos la cabecera de una peticion HTTP, dependiento del tipo
                # de solicitud, realizaremos una acción u otra.
                print(solicitud,"\n")
                print(cabecera)
                print(nuevo_archivo_pedido)

                try: 

                    file = open("index.html", 'r')
                    response = file.read() 
                    file.close()

                    file = open("css/index.css", 'r')
                    response_css = file.read()
                    file.close()

                    file = open("img/redes.jpg", 'rb')
                    imagen_bytes = file.read()
                    file.close()
                    
                    data_uri = "data:image/jpeg;base64," + base64.b64encode(imagen_bytes).decode("ascii")

                    ruta_archivo_html = "index.html"
                    ruta_archivo_css = "css/index.css"
                    ruta_img = "img/redes.jpg"
                    tamaño_html = os.path.getsize(ruta_archivo_html)
                    tamaño_css = os.path.getsize(ruta_archivo_css)
                    tamaño_img = os.path.getsize(ruta_img)
                    tamaño_total = tamaño_css + tamaño_html
                    tamaño_total = str(tamaño_total)
                    
                    if(archivo_pedido.endswith('/')):
                        mimetype = 'text/html'

                    elif(archivo_pedido.endswith('.html')):
                        mimetype = 'text/html'


                    if cabecera.startswith('GET'):
                        fecha_hora = datetime.datetime.now()
                        fecha_bytes = fecha_hora.strftime("%Y-%m-%d %H:%M:%S.%f")
                        plataforma = platform.system()
                        Tipo_Conexion = "keep-alive"
                        cabecera_1 = 'HTTP/1.1 200 OK\r\nDate: '+ fecha_bytes + '\r\nConnection: ' + Tipo_Conexion + '\r\nServidor:' + plataforma + '\r\nContent-type: ' + mimetype + '\r\nContent-length:' + tamaño_total + '\r\n\n{}'.format(response + '<style>' + response_css + '</style>')
                        print(cabecera_1)
                        respuesta = cabecera_1.encode("utf-8") 
                        print(respuesta)
                        s.sendall(respuesta)
                        entradas.pop()
                        s.close()
                        break

                    if cabecera.startswith('POST'):

                        if nuevo_archivo_pedido == 'index2.html':
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
                            val = (DNI,Nombre,Apellido,Fecha)
                            cur.execute(sql,val)
                            Conexion_SQL.commit()
                        
                            file = open(nuevo_archivo_pedido, 'r')
                            contenido = file.read()
                            file.close()

                            file = open("css/index.css", 'r')
                            contenido_css = file.read()
                            file.close()

                            ruta_archivo_css = "css/index.css"
                            tamaño_archivo = os.path.getsize(nuevo_archivo_pedido)
                            tamaño_css = os.path.getsize(ruta_archivo_css)
                            tamaño_total = tamaño_css + tamaño_archivo
                            tamaño_total = str(tamaño_total)
                            
                            fecha_hora = datetime.datetime.now()
                            fecha_bytes = fecha_hora.strftime("%Y-%m-%d %H:%M:%S.%f")
                            plataforma = platform.system()
                            Tipo_Conexion = "keep-alive"
                            cabecera_1 = 'HTTP/1.1 200 OK\r\nDate: '+ fecha_bytes + '\r\n Connection: ' + Tipo_Conexion + '\r\nServidor:' + plataforma + '\r\nContent-type: ' + mimetype + '\r\nContent-length:' + tamaño_total + '\r\n{}'.format(contenido + '<style>' + response_css + '</style>')
                            respuesta_final = cabecera_1
                            s.sendall(respuesta_final.encode("utf-8"))
                            entradas.pop()
                            s.close()

                    break
                        
                except Exception as e:
                    print("error: ",e)

        break
    
    

    for s in exceptional:
        print("Excepcion en el socket desde {}:{}",format(entradas[s]))
        