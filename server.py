import sys
import socket
import select

# Establecer el host y el puerto del servidor
server_address = ('192.168.2.3', 1025)

# Crear un objeto socket
socketserv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Configurar el socket para reutilizar la dirección del servidor después de cerrar la conexión
socketserv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Enlazar el objeto socket al host y puerto especificados
socketserv.bind(server_address)

# Escuchar por conexiones entrantes
socketserv.listen(5)
print('Esperando por conexiones...')
print('Escuchando en ip ', server_address[0], 'y puerto:', server_address[1])

# Lista de sockets para selección
sockets_list = []

# Diccionario de clientes (socket: nombre de cliente)
clientes = {}

# Cargamos el contenido del archivo HTML que se va a solicitar al servidor en una cadena.

with open('index.html', 'r') as doc:
    contenido_html = doc.read()


"""
while True:
    # Esperar por cambios en los sockets listados
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    # Manejar los sockets que tienen datos entrantes
    for notified_socket in read_sockets:
        # Si el socket listado es el socket servidor, significa que hay una nueva conexión entrante
        if notified_socket == server_socket:
            cliente_socket, client_address = server_socket.accept()

            # Agregar el nuevo socket cliente a la lista de sockets listados y al diccionario de clientes
            sockets_list.append(cliente_socket)
            clients[cliente_socket] = client_address

            print('Nueva conexión aceptada desde {}:{}'.format(*client_address))

        # Si no es una nueva conexión, significa que hay datos entrantes desde un cliente existente
        else:
            # Obtener el nombre de cliente correspondiente al socket cliente que envió la solicitud HTTP
            client_address = clients[notified_socket]

            # Recibir los datos entrantes desde el socket cliente
            data = notified_socket.recv(1024)

            # Si no hay datos entrantes, significa que el cliente cerró la conexión
            if not data:
                print('Conexión cerrada por {}:{}'.format(*client_address))

                # Eliminar el socket cliente de la lista de sockets listados y del diccionario de clientes
                sockets_list.remove(notified_socket)
                del clients[notified_socket]

            else:
                # Convertir los datos entrantes en una solicitud HTTP
                
                Se guarda la respuesta en una variable, para ello obtenemos decodificamos los datos recibidos
                y separamos las lineas por espacios, esta separación se guarda en un array, nos quedamos con la primera palabra 
                recibida. Esta primera palabra es la que indica el tipo de solicitud HTTP ('GET' o 'POST')
                
                request = data.decode().splitlines()[0]

                # Si la solicitud es una solicitud GET.
                if request.startswith('GET'):
                    response = 'HTTP/1.1 200 OK\nContent-Type: text/html\n\n'
                    response += contenido_html.encode()

                    notified_socket.send(response)

                elif request.startswith('POST'):
                    content_length = int(data.decode().splitlines()[2].split(': ')[1])
                    data = notified_socket.recv(content_length).decode()

                    response = 'HTTP/1.1 200 OK\nContent-Type: text/html\n\n'
                    response += '<html><body><h1>Los datos recibidos son:</h1><p>{}</p></body></html>'.format(data).encode()

                    notified_socket.send(response)

    # Manejar los sockets que tienen excepciones
    for notified_socket in exception_sockets:
        print('Excepción en el socket desde {}:{}'.format(*clients[notified_socket]))
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
"""