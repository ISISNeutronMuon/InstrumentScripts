import socket
from contextlib import closing


def send_tcpip(message, host, port, reply):
    """
    Sends a message to tcp port on host.

    Args:
        message (string):  the message to send
        host    (string):  the host address to use
        port    (integer): the tcpip port to use
        reply   (bool):    whether to wait for a reply

    Returns:
        None if reply False else the bytes that the server sends back
    """
    try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.connect((host, port))
            s.sendall(bytes(message, "utf-8"))
            if reply:
                data = s.recv(1024)
            else:
                data = None
        return data
    except Exception as e:
        raise Exception("Could not send message to tcp port: {}".format(e))
