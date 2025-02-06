import socket
import time
import os

server_address = './uds_socket'

# Make sure the socket does not already exist
try:
    os.unlink(server_address)
except OSError:
    if os.path.exists(server_address):
        raise

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
print('starting up on {}'.format(server_address))
sock.bind(server_address)
sock.listen(1)

while True:
    print('\nwaiting for a connection')

    connection, client_address = sock.accept()
    connection.settimeout(300)

    try:
        print('connected')
        connect_time = time.time()
        while True:
            try:
                data = connection.recv(640)
                if not data:
                    elapsed_time = int(time.time() - connect_time)
                    print(f'no data after {elapsed_time}s')
                    break
            except socket.timeout as exc:
                elapsed_time = int(time.time() - connect_time)
                print(f'timeout after {elapsed_time}s on recv')
                break
    finally:
        connection.close()
