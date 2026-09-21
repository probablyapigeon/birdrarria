"""Loopback bridge shared by Desktop Lonk and Terraria adapters."""
from __future__ import annotations
import argparse, json, socketserver, threading, uuid
from collections import deque
from colony import Colony
from protocol import BIRDS, MAX_TEXT, PROTOCOL_VERSION, decode

class BridgeState:
    def __init__(self):
        self.lock=threading.Lock(); self.memories={bird:deque(maxlen=32) for bird in BIRDS}; self.project={"name":"Terraria nest","goal":"build a shared birdhouse","progress":[],"updated_by":None}; self.builds=deque(maxlen=16); self.colony=Colony()
    def snapshot(self):
        with self.lock: return {"memories":{k:list(v) for k,v in self.memories.items()},"project":dict(self.project),"build_requests":list(self.builds),"colony":self.colony.snapshot()}
    def handle(self,message):
        kind=message["kind"]; bird=message.get("bird"); world=message.get("world"); payload=message["payload"]
        if kind=="hello": return {"ok":True,"version":PROTOCOL_VERSION,"capabilities":["observe","visit","teach","project","bounded_build_requests","colony"],"birds":sorted(BIRDS)}
        if kind in {"observe","teach"}:
            entry={"bird":bird,"world":world,"kind":kind,"text":payload["text"][:MAX_TEXT]}
            with self.lock:
                for member in BIRDS: self.memories[member].append(entry)
            return {"ok":True,"recorded":entry,"shared":self.snapshot()}
        if kind=="visit": return {"ok":True,"visitor":bird,"world":world,"shared":self.snapshot()}
        if kind=="colony":
            action=payload.get("action","status")
            with self.lock:
                if action=="register": result=self.colony.register(payload.get("resident_id", bird),world,payload.get("role","scout"),payload.get("faction","wanderers"))
                elif action=="bond": self.colony.bond(payload.get("resident_id", bird),payload["other"],int(payload.get("amount",1))); result={"bonded":[payload.get("resident_id", bird),payload["other"]]}
                elif action=="job": result=self.colony.add_job(payload["title"],payload["target"],bird)
                elif action=="myth": result=self.colony.add_myth(payload["title"],payload["telling"],bird)
                elif action=="family": result=self.colony.create_family(payload["name"],payload.get("members",[bird]),payload.get("parents",[]))
                elif action=="child": result=self.colony.add_child(payload["family"],payload["child"],payload.get("parents",[bird]))
                elif action=="settlement": result=self.colony.add_settlement(payload["name"],world or "desktop",int(payload["x"]),int(payload["y"]))
                else: result=self.colony.snapshot()
            return {"ok":True,"action":action,"result":result,"colony":self.colony.snapshot()}
        if kind=="project":
            action=payload.get("action","status")
            with self.lock:
                if action=="start": self.project["name"]=payload.get("name",self.project["name"]); self.project["goal"]=payload.get("goal",self.project["goal"])
                elif action=="progress" and isinstance(payload.get("note"),str) and payload["note"].strip(): self.project["progress"].append({"bird":bird,"world":world,"note":payload["note"][:MAX_TEXT]}); self.project["progress"]=self.project["progress"][-32:]
                self.project["updated_by"]=bird
            return {"ok":True,"project":self.snapshot()["project"]}
        if kind=="build_request":
            action=payload["action"]
            with self.lock:
                request_id=payload.get("request_id",uuid.uuid4().hex[:12])
                if action=="propose": request={"id":request_id,"status":"pending","bird":bird,"world":world,"target":payload["target"],"bounds":payload["bounds"]}; self.builds.append(request)
                else:
                    request=next((item for item in reversed(self.builds) if item["id"]==request_id),None)
                    if request is None: return {"ok":False,"error":"unknown build request"}
                    request["status"]="approved" if action=="approve" else "rejected"; request["decided_by"]=bird
            return {"ok":True,"request":request,"shared":self.snapshot()}
        return {"ok":False,"error":"unhandled message"}

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        for raw in self.rfile:
            try: message=decode(raw.rstrip(b"\r\n")); response=self.server.state.handle(message); print(f"portal: {message['kind']} from {message.get('bird','adapter')} ({message.get('world','?')})",flush=True)
            except (ValueError,json.JSONDecodeError) as exc: response={"ok":False,"error":str(exc)}
            try: self.wfile.write((json.dumps(response,ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8")); self.wfile.flush()
            except (ConnectionResetError,BrokenPipeError): pass
class BridgeServer(socketserver.ThreadingTCPServer):
    allow_reuse_address=True; daemon_threads=True
    def __init__(self,port): super().__init__(("127.0.0.1",port),Handler); self.state=BridgeState()
def main():
    parser=argparse.ArgumentParser(description="Loopback Lonk bird portal bridge"); parser.add_argument("--port",type=int,default=45871); args=parser.parse_args(); server=BridgeServer(args.port); print(f"Lonk portal bridge listening on 127.0.0.1:{args.port}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
if __name__=="__main__": main()


