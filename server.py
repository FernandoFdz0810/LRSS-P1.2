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



"""
Se recoge en la linea de ordenes que tipo de conexión se desea establecer con el servidor. 
Para ello, se chequea si se desea conexión "Persistente" o "No-Persistente".
En caso de ser persistente para la cabecera "Connection" se elige "Keep-Alive"
y se establecen los valores de la cabecera Keep-Alive, que se guarda en la
variable Keep_Alive para posteriormente pasarlo a la cabecera correspondiente.
En caso de seleccionar tipo de conexión "No Persistente", la cabecera "Connection" se selecciona como
"close" y la cabecera "Keep-Alive" se deja vacia.
"""

if sys.argv[1] == "Persistente":
    Tipo_Conexion = "Keep-Alive"
    Keep_Alive = "timeout=10, max=1000"

if sys.argv[1] == "No-Persistente":
    Tipo_Conexion = "close"
    Keep_Alive = " "

"""
Para la realización de la conexión SQL se utiliza el modulo pymysql que se importa de la 
librería pertinente. Además, se pasan los parámetros correspondientes para realizar dicha conexión
como "host" donde está ubicada la BBDD, usuario, contraseña y Base de Datos con la que se desea 
trabajar.
"""


Conexion_SQL = pymysql.connect(host='localhost', user='fernando', passwd='Fernando0810_', db='LRSS2')
#La conexión SQL tiene un cursor que es la que permite enviar las sentencias SQL pertinentes.
cur = Conexion_SQL.cursor()

# Establecer el host y el puerto del servidor
server_address = ('192.168.2.4', 8080)

# Crear un objeto socket, además de comprobar que no ocurren errores en la creación del socket.
try:
    socketserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except Exception as e:
    print("Error creando el socket: ", e)

# Configurar el socket para reutilizar la dirección del servidor después de cerrar la conexión.-
socketserv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Enlazar el objeto socket al host y puerto especificados
try:
    socketserv.bind(server_address)
except Exception as e:
    print("Error en la asociación del socket: ", e)

# Escuchar por conexiones entrantes
socketserv.listen(5)

"""
El segundo argumento que se pasa por linea de ordenes será el de si se desea establecer una 
conexion HTTP o HTTPS. En caso de ser HTTPS se crea un contexto para realizar conexiones mediante
SSL, aplicando un certificado creado anteriormente y la clave pertinente. 
Una vez se ha aplicado, se solapa la configuración del contexto al socket creado anteriormente, 
almacenado como "socketserv" y dicho solape se almacena en una variable llamada "secure_socket".
"""

if sys.argv[2] == "HTTPS":
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile='server.cert', keyfile='server.key')
    secure_socket = ssl_context.wrap_socket(socketserv, server_side=True)


print('Escuchando en ip ', server_address[0], 'y puerto:', server_address[1])

"""
Dependiendo de si escogemos conexiones HTTP o HTTPS, en la lista de entradas de la función select, 
se añade o el socket original para conexiones HTTP, o el socket con el contexto SSL para conexiones
HTTPS.
"""

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
    """
    La función select es bloqueante hasta que se reciben peticiones al servidor, tiene 3 listas,
    la lista readable será donde se almacenen los clientes que realizan peticiones sobre el servidor. 
    La lista writable, será donde se almacenen los clientes a los que se les va a realizar un envio de información, 
    y que por tanto estan listos para ser "escritos".
    Por último, la lista excepcional almacenará aquellos sockets cliente que produzcan algun tipo
    de excepción.
    """
    readable, writable, exceptional = select.select(entradas, salidas, entradas, 10)
    if len(readable) == 0:
        print("Servidor desconectado debido a temporizador 'timeout'")

    """
    A continuación, se realiza una iteracción sobre la lista de sockets clientes que han realizado algún tipo
    de petición al servidor.
    En caso de que el socket sobre el que se intenta leer sea el servidor, estamos preparados para aceptar conexiones
    entrantes por parte de los clientes.

    """

    for s in readable:
        if s is Descriptor_socket_serv:
            # Un socket en modo lectura esta preparado para aceptar la conexion
            conexion, client_address = s.accept()
            """
            La función setblocking() permite establecer si una operación de E/S se bloqueará. 
            En este caso se establece como '0' o 'False', por lo que la conexión se realizará de forma
            no bloqueante. El hilo de ejecución continuará ejecutandose sin esperar a que se complete
            la operación.
            """
            conexion.setblocking(0)
            # Una vez realizada la conexión, se añade a la lista de entradas de la función select()
            entradas.append(conexion)

            # A continuación le damos a la conexion una cola para los
            # datos que queremos enviar

            cola_mensajes[conexion] = queue.Queue()

        # La otra opcion la encontramos para una coonexión establecida
        # con un cliente que ha enviado datos.

        else:

            data = s.recv(1024)

            if not data:
                # Si no hay datos entrantes, significa que el cliente cerró la conexión.
                print('Conexión cerrada por {}:{}\n'.format(*client_address))
                # En ese caso, se saca al cliente de la lista de entradas y, se cierra el socket.
                entradas.pop()
                s.close()

            else:
                # En caso contrario, significa que el servidor ha recibido datos. 
                """
                En las peticiones HTTP, el navegador web envia al servidor una serie de cabeceras
                que son de cierto interes. 
                Las operaciones que se realizan a continuación pretenden separar los datos recibidos, 
                para guardar en variables, el tipo de solicitud recibida como pudiera ser "GET" o "POST".
                Guarda, el archivo que se haya pedido, por defecto, la petición "/", se traduce más adelante como 
                la petición del archivo "index.html". También se pueden almacenar otro tipo de peticiones de archivo
                para diferente códigos HTML, CSS o incluso JS.
                """

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

                """
                A continuación abre y lee los diferentes archivos que pudieran ser solicitados por parte
                del cliente que se encuentran almacenados de forma local en el servidor, como archivos 'html' o 'css'.
                """

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

                    """
                    Debido a que en el nuevo_archivo_pedido se van a almacenar los diferentes 
                    archivos solicitados, y a que tenemos diferente tipos de "html" en el servidor,
                    si la petición del archivo finaliza en '.html' se almacena en una variable el nombre del archivo pedido. 
                    Debido a que solo existe un archivo CSS, se almacena el nombre del archivo para CSS. 

                    Posteriormente, mediante la función os.path.getsize() a la que se le pasa como parámetro el nombre del archivo, 
                    o la ruta donde se encuentra el archivo para que pueda guardarse el tamaño del documento en bytes que se le va a pasar al servidor
                    mediante una cabera posteriormente. 

                    """

                    if nuevo_archivo_pedido.endswith('.html'):
                        ruta_archivo_html = nuevo_archivo_pedido

                    ruta_archivo_css = "css/index.css"
                    tamaño_html = os.path.getsize(ruta_archivo_html)
                    tamaño_css = os.path.getsize(ruta_archivo_css)
                    tamaño_total = tamaño_css + tamaño_html
                    tamaño_total = str(tamaño_total)

                    """
                    Existe otro tipo de cabecera que es mimetype, que indica el formato del archivo que se le esta 
                    enviando al cliente por parte del servidor. 
                    Mediante condicionales se selecciona el tipo de mimetype que corresponde a cada tipo de petición para
                    posteriormente pasarlo como cabecera HTTP.
                    """

                    if (archivo_pedido.endswith('/')):
                        mimetype = 'text/html'

                    elif (archivo_pedido.endswith('.html')):
                        mimetype = 'text/html'

                    elif (archivo_pedido.endswith('.css')):
                        mimetype = 'text/css'

                    elif (archivo_pedido.endswith('.png')):
                        mimetype = 'image/png'

                    """
                    Anteriormente hemos almacenado en la variable cabecera, la cabecera de petición realizada por el cliente. 
                    Se diferencia entre peticiones "GET" o "POST". En caso de ser una u otra, operamos en el servidor de un modo
                    u otro.
                    """

                    if cabecera.startswith('GET'):
                        
                        # Parametros que se calculan en el instante de la petición para pasarlos como cabecera HTTP.

                        fecha_hora = datetime.datetime.now()
                        fecha_bytes = fecha_hora.strftime("%Y-%m-%d %H:%M:%S.%f")
                        plataforma = platform.system()
                        cabecera_1 = 'HTTP/1.1 200 OK\r\nDate: ' + fecha_bytes + '\r\nConnection: ' + Tipo_Conexion + '\r\nKeep-Alive: ' + Keep_Alive + '\r\nServidor:' + plataforma + '\r\nContent-type: ' + \
                            mimetype + '; charset=utf-8\r\nContent-length:' + tamaño_total + \
                            '\r\n\n{}'.format(index + '<style>' + response_css + '</style>')
                        print(cabecera_1)

                        """
                        A continuación se prueba a enviar todo el contenido solicitado mediante la peticion GET,
                        incluyendo cabeceras, contenido del archivo HTML solicitado y archivo CSS.
                        
                        Por último, se realiza el envio, en caso de haber algun tipo de excepcion, se añade a la lista de 
                        exceptional, de la función select el socket, y se imprime un mensaje por pantalla informando del error.
                        """
                        try:
                            s.sendall(cabecera_1.encode())
                        except Exception as e:
                            exceptional.append(s)
                            print("Error al enviar los datos ", e)

                        """
                        Una vez se ha realizado el envio, procedemos a eliminar al cliente de la lista de entradas
                        a la que va a recurrir la función select para verificar qué clientes se encuentran listos para realizar
                        una conexión con el servidor. Debido a que ya se le ha enviado lo solicitado se elimina. 
                        Por último, se cierra la conexión.
                        """

                        entradas.pop()
                        s.close()
                        break

                    if cabecera.startswith('POST'):
                        """
                        En caso de recibir cabeceras del tipo "POST", será por que el cliente ha enviado datos
                        mediante un formulario implementado en el archivo HTML.
                        A parte de enviar cabeceras HTTP mediante la petición POST, también se reciben los datos 
                        introducidos en el formulario. 
                        Es de interes obtener estos datos enviados a través del formulario para poder almacenarlos
                        en una Base de Datos. 
                        Para ello, procedemos a realizar una serie de operaciones, entre ellas, separar los campos de las peticiones, 
                        y quedarnos solamente con los datos introducidos en el formulario. 
                        Estos datos se almacenan en un Diccionario de Python, almacenando como "clave" el dato que se solicita en el formulario
                        como "DNI", "Nombre", "Apellidos"..., y como "valor" el valor que ha introducido el usuario mediante el 
                        formulario.
                        Finalmente, se unen todos los diccionarios en uno, denominado como Diccionario_Solicitud_Final

                        Del diccionario que hemos creado, nos interesa quedarnos con el "Valor", por lo que se procede a iterar en estos valores 
                        y almacenarlos en variables que corresponden con el dato solicitado.

                        Finalmente, se procede a realizar una sentencia SQL, a la que se le pasan como parámetros los valores de interes 
                        que hemos recogido anteriormente. Y mediante el cursor de la conexión inicial con SQL se mandan los datos con la sentencia 
                        pertinente a la BBDD. Estos datos quedarán almacenado en la BBDD.

                        Cuando se han realizado todas estas tareas, en un intervalo corto de tiempo se generan la cabeceras del mismo modo que como
                        hicimos para las peticiones GET y se envía todo al cliente. 
                        """
                        
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

                        """
                        Una vez atendida la petición del cliente, se le procede a eliminar de la lista de entradas.
                        """
                        entradas.pop()
                        s.close()

                    break

                except Exception as e:
                    print("error: ", e)

        break

    """
    En caso de haberse añadido alguna excepcion en la lista exceptional, se itera sobre la misma, y se informa que se produjo un error
    en el socket, indicando la dirección IP y Puerto del socket que ha producido dicha excepción.
    """

    for s in exceptional:
        print("Excepcion en el socket desde {}:{}", format(entradas[s]))
