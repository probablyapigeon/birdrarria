import json
import socket

with socket.create_connection(("127.0.0.1", 45871), timeout=3) as sock:
    sock.sendall((json.dumps({"version": 1, "kind": "hello", "payload": {}}) + "\n").encode("utf-8"))
    print(sock.recv(4096).decode("utf-8"), end="")
