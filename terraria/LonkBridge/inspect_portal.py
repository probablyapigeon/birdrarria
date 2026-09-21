import json
import socket

message = {"version": 1, "kind": "visit", "bird": "lonk", "world": "desktop", "payload": {}}
with socket.create_connection(("127.0.0.1", 45871), timeout=3) as sock:
    sock.sendall((json.dumps(message) + "\n").encode("utf-8"))
    print(sock.recv(16384).decode("utf-8"))
