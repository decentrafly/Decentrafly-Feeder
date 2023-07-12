import json
import os
import select
import socket
import ssl


def load_config():
    config_file_path = os.path.expanduser("/etc/decentrafly/config.json")
    if os.path.isfile(config_file_path):
        config = json.load(open(config_file_path))
        return config
    else:
        return {}


default_config = {
    'DCF_MLAT_CA_FILE': '/etc/decentrafly/ca-crt.pem',
    'DCF_MLAT_CLIENT_CRT_FILE': '/etc/decentrafly/client-crt.pem',
    'DCF_MLAT_CLIENT_KEY_FILE': '/etc/decentrafly/client-key.pem',
    'DCF_MLAT_FORWARDER_BIND_ADDRESS': '0.0.0.0'
    'DCF_MLAT_FORWARDER_PORT': '41090',
    'DCF_MLAT_SECURE_PORT': '31090',
    'DCF_MLAT_SECURE_SERVER': 'mlat.decentrafly.org',
    'DCF_MLAT_SECURE_SERVER_NAME': 'mlat.decentrafly.org',
    }

environment_config = {k: os.getenv(k) for k in default_config.keys()
                      if os.getenv(k) is not None}

# Effective Config (after resolving overrides)
ec = {**default_config, **load_config(), **environment_config}


def forward_to_all(payload, socklist):
    for sock in socklist:
        try:
            if sock.sendall(payload) is not None:
                exit(3)
        except Exception:
            exit(3)


def connect_sock(host, port):
    newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    newsock.settimeout(10)
    print("Attempting connection to {}:{}".format(host, port))
    newsock.connect((host, port))
    print("Connected to {}:{}".format(host, port))
    return newsock


class Bridge:

    def __init__(self, accepted_socket):
        self.incoming_socket = accepted_socket
        self.forward_socket = None
        self.status = 'initial'

    def connect_forwarder(self):
        context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH,
                                             cafile=ec['DCF_MLAT_CA_FILE'])
        context.verify_mode = ssl.VerifyMode.CERT_REQUIRED
        context.check_hostname = True
        context.load_cert_chain(ec['DCF_MLAT_CLIENT_CRT_FILE'],
                                keyfile=ec['DCF_MLAT_CLIENT_KEY_FILE'])

        plain_sock = connect_sock(ec['DCF_MLAT_SECURE_SERVER'],
                                  int(ec['DCF_MLAT_SECURE_PORT']))
        self.forward_socket = context.wrap_socket(plain_sock,
                                                  server_side=False,
                                                  server_hostname=ec['DCF_MLAT_SECURE_SERVER_NAME'])
        self.status = 'connected'

    def handle_disconnect(self):
        self.incoming_socket.close()
        self.forward_socket.close()
        self.status = 'dead'

    def forward_to(self, out_socket, data):
        try:
            if out_socket.sendall(data) is not None:
                self.status = 'error'
        except Exception:
            self.status = 'error'

    def forward_from(self, in_socket, data):
        if in_socket == self.incoming_socket:
            self.forward_to(self.forward_socket, data)
        elif in_socket == self.forward_socket:
            self.forward_to(self.incoming_socket, data)
        else:
            raise Exception("Wrong bridge")


class MlatMtlsForwarder:

    def __init__(self):
        self.plaintext_listen_sockets = []
        self.bridges = []
        self.socket_map = {}

    def listen_sock(self, host, port):
        newsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        newsock.bind((host, port))
        newsock.listen(5)
        print("Listening on {}:{}".format(host, port))
        return newsock

    def listen_plaintext(self, host, port):
        self.plaintext_listen_sockets.append(self.listen_sock(host, port))

    def handle_disconnect(self, sock):
        if sock in self.plaintext_sockets:
            self.plaintext_sockets.remove(sock)
            print("Lost connection from {}".format(sock.getsockname()))
            sock.close()
        if sock in self.mtls_sockets:
            self.mtls_sockets.remove(sock)
            print("Lost forwarder connection to {}".format(sock.getsockname()))
            exit(2)

    def run(self):
        while True:
            all_socks = [*self.plaintext_listen_sockets,
                         *[b.incoming_socket for b in self.bridges],
                         *[b.forward_socket for b in self.bridges]]

            r, w, x = select.select(all_socks, [], all_socks, 3.0)

            if len(x) > 0:
                exit(4)

            for rs in r:
                if rs in self.plaintext_listen_sockets:
                    conn, addr = rs.accept()
                    print("New connection from {}".format(addr))
                    new_bridge = Bridge(conn)
                    try:
                        new_bridge.connect_forwarder()
                    except Exception:
                        print("Establishing bridging connection failed")
                        conn.close()
                        continue
                    self.bridges.append(new_bridge)
                    self.socket_map[new_bridge.incoming_socket] = new_bridge
                    self.socket_map[new_bridge.forward_socket] = new_bridge
                elif rs in self.socket_map:
                    bridge = self.socket_map[rs]
                    buff = rs.recv(8192)
                    if not buff or bridge.status == 'error':
                        print("Connection failed")
                        self.socket_map.pop(bridge.incoming_socket)
                        self.socket_map.pop(bridge.forward_socket)
                        self.bridges.remove(bridge)
                        bridge.handle_disconnect()
                    else:
                        bridge.forward_from(rs, buff)
                else:
                    raise Exception("Socket not in socket map")
                    pass


def run():
    forwarder = MlatMtlsForwarder()
    forwarder.listen_plaintext(ec['DCF_MLAT_FORWARDER_BIND_ADDRESS'],
                               ec['DCF_MLAT_FORWARDER_PORT'])
    forwarder.run()
