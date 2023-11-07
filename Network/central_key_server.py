from node import Node
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec


class KeyServer(Node):
    def __init__(self, host, port):
        super().__init__(self, host, port)
        self.keyserver = {}
        self.private_key = ec.generate_private_key(
            ec.SECP384R1()
            )

    def add_network(self, name, key):
        self.keyserver[name] = key
    
    def get_key(self, name):
        if name in self.keyserver:
            return self.keyserver[name]
        return "No server found"

    def run(self):
        try:
            print("Node: Wait for incoming connection")
            while True:
                connection, client_address = self.receive_socket.accept()
                data = connection.recv(1024)
                data = KeyPacket.decode_tlv(data)
                data = self.key.
                if TLVType.KEY_PACKET in data:
                    

                elif TLVType.KEY_REQUEST_PACKET in data:
                    chosen_hash = hashes.SHA256()
                    hasher = hashes.Hash(chosen_hash)
                    key = self.get_key(name)
                    hasher.update(key)
                    digest = hasher.finalize()
                    sig = self.private_key.sign(
                        digest,
                        ec.ECDSA(utils.Prehashed(chosen_hash))
                    )

                    client_address.send(KeyPacket.encode_key(data, sig))

        except Exception as e:
            raise e
