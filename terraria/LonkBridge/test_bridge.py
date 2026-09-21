import json
import socket
import threading
import unittest

from protocol import decode, encode
from bridge import BridgeServer


class BridgeTests(unittest.TestCase):
    def test_protocol_rejects_bad_world(self):
        with self.assertRaises(ValueError):
            encode({"version": 1, "kind": "observe", "bird": "lonk", "world": "internet", "payload": {"text": "x"}})

    def test_round_trip_shares_memory(self):
        server = BridgeServer(0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with socket.create_connection(server.server_address, timeout=2) as sock:
                stream = sock.makefile("rwb")
                stream.write(encode({"version": 1, "kind": "observe", "bird": "lonk", "world": "desktop", "payload": {"text": "I found a portal."}}))
                stream.flush()
                response = json.loads(stream.readline())
                self.assertTrue(response["ok"])
                self.assertEqual(response["shared"]["memories"]["pip"][0]["text"], "I found a portal.")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_decode_caps_input(self):
        with self.assertRaises(ValueError):
            decode(b"{" + b"x" * 17000)


if __name__ == "__main__":
    unittest.main()

