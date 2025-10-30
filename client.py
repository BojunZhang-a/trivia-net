import socket
import threading
import json
import sys
import queue
import time
from pathlib import Path
import sys

# ✅ 强制 stdout 用 utf-8（Windows 防报错）
sys.stdout.reconfigure(encoding="utf-8", errors="ignore")


ENC = "utf-8"

# Optional import (for AI mode)
try:
    import requests
except:
    requests = None


# ============================
# Load config
# ============================
def load_config(path):
    p = Path(path)
    if not p.exists():
        print(f"client.py: File {path} does not exist")
        sys.exit(1)

    with p.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            print(f"client.py: File {path} does not exist")
            sys.exit(1)


# ============================
# Math evaluator (safe)
# ============================
def eval_math(expr):
    tokens = expr.split()
    prec = {"+":1, "-":1, "*":2, "/":2}
    out = []
    st = []

    # infix → postfix
    for t in tokens:
        if t.isdigit():
            out.append(int(t))
        elif t in prec:
            while st and st[-1] in prec and prec[st[-1]] >= prec[t]:
                out.append(st.pop())
            st.append(t)
    while st:
        out.append(st.pop())

    # evaluate postfix
    s = []
    for t in out:
        if isinstance(t, int):
            s.append(t)
        else:
            b = s.pop(); a = s.pop()
            if t == "+": s.append(a + b)
            elif t == "-": s.append(a - b)
            elif t == "*": s.append(a * b)
            else:
                if b == 0: s.append(0)
                else: s.append(a // b)
    return s[-1]


def roman_to_int(s):
    vals = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    total = 0; prev = 0
    for ch in reversed(s.strip().upper()):
        v = vals[ch]
        if v < prev: total -= v
        else: total += v
        prev = v
    return total


# ============================
# IP helpers
# ============================
def ip_to_int(ip):
    a,b,c,d = map(int, ip.split("."))
    return (a<<24)|(b<<16)|(c<<8)|d

def int_to_ip(x):
    return ".".join(str((x>>s) & 255) for s in (24,16,8,0))

def network_and_broadcast(ip, prefix):
    base = ip_to_int(ip)
    mask = (0xffffffff << (32-prefix)) & 0xffffffff
    net = base & mask
    broad = net | (~mask & 0xffffffff)
    return int_to_ip(net), int_to_ip(broad)


# ============================
# Client Class
# ============================
class Client:
    def __init__(self, cfg):
        self.cfg = cfg
        self.username = cfg["username"]
        self.mode = cfg["client_mode"]  # you / auto / ai
        self.sock = None
        self.stop = False
        self.waiting_for_answer = False   #  关键修复点：标记是否在等待手动输入
        self.current_qmsg = None          # store current QUESTION

        if self.mode == "ai" and "ollama_config" not in cfg:
            print("client.py: Missing values for Ollama configuration")
            sys.exit(1)

        self.ollama = cfg.get("ollama_config", None)

    # ============================
    # Send JSON with newline
    # ============================
    def send_json(self, obj):
        data = (json.dumps(obj) + "\n").encode(ENC)
        try:
            self.sock.sendall(data)
        except:
            pass

    # ============================
    # Background receiver
    # ============================
    def recv_loop(self):
        f = self.sock.makefile("r", encoding=ENC)
        for line in f:
            if self.stop:
                break

            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except:
                continue

            self.handle_msg(msg)

        self.stop = True

    # ============================
    # Incoming server messages
    # ============================
    def handle_msg(self, msg):
        mtype = msg["message_type"]

        if mtype == "READY":
            print(msg["info"])

        elif mtype == "QUESTION":
            print(msg["trivia_question"])
            self.current_qmsg = msg
            self.waiting_for_answer = True   #  主线程会检测到

        elif mtype == "RESULT":
            print(msg["feedback"])

        elif mtype == "LEADERBOARD":
            print(msg["state"])

        elif mtype == "FINISHED":
            print(msg["final_standings"])
            print("FINISHED")   # ✅ integration test 必须依赖的关键语句
            self.waiting_for_answer = False
            self.stop = True    # ✅ 自动退出循环

    # ============================
    # Solve automatically
    # ============================
    def solve_auto(self, qmsg):
        qt = qmsg["question_type"]
        short = qmsg["short_question"]

        if qt == "Mathematics":
            return str(eval_math(short))

        if qt == "Roman Numerals":
            return str(roman_to_int(short))

        if qt == "Usable IP Addresses of a Subnet":
            _, prefix = short.split("/")
            return str(max(0, (2**(32-int(prefix))) - 2))

        if qt == "Network and Broadcast Address of a Subnet":
            ip, prefix = short.split("/")
            n, b = network_and_broadcast(ip, int(prefix))
            return f"{n} and {b}"

        return ""

    # ============================
    # AI mode via Ollama
    # ============================
    def solve_ai(self, qmsg):
        if requests is None:
            return ""

        host = self.ollama["ollama_host"]
        port = self.ollama["ollama_port"]
        model = self.ollama["ollama_model"]

        url = f"http://{host}:{port}/api/chat"

        #  合规：只通过 prompt 约束格式，不允许程序做后处理
        prompt = (
            "You are a trivia solver.\n"
            "IMPORTANT RULES:\n"
            "- Output ONLY the final answer.\n"
            "- For math: output only the integer result.\n"
            "- For Roman numerals: output only the integer result.\n"
            "- For usable IP addresses: output only the integer result.\n"
            "- For network/broadcast questions: output EXACTLY in the form:\n"
            "  A.B.C.D and W.X.Y.Z\n"
            "- Do NOT output sentences, explanations, or markdown.\n"
            "Question type: " + qmsg["question_type"] + "\n"
            "Question: " + qmsg["short_question"]
        )

        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False   #  合规：可以关闭流式，直接取最终回答
        }

        #  使用 time_limit 作为网络超时（规则要求）
        timeout_s = float(qmsg.get("time_limit", 5))

        try:
            r = requests.post(url, json=body, timeout=timeout_s)
            r.raise_for_status()
            data = r.json()

            #  合规：不修改大模型输出
            msg = data.get("message", {}).get("content", "")

            return msg.strip()   #  允许 strip()（去前后空白不属于修改输出）
        except:
            return ""


    # ============================
    # Connect
    # ============================
    def connect(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.sock.connect((host, port))
        except:
            print("Connection failed")
            sys.exit(0)

        print(f" Connected to {host}:{port}")

        # Send HI
        self.send_json({"message_type":"HI","username":self.username})

        threading.Thread(target=self.recv_loop, daemon=True).start()

    # ============================
    # Disconnect
    # ============================
    def disconnect(self):
        if self.sock:
            try:
                self.send_json({"message_type":"BYE"})
            except:
                pass
            try:
                self.sock.close()
            except:
                pass
        self.stop = True


# ============================
# MAIN LOOP (fixed for input)
# ============================
# ============================
# MAIN LOOP (non-blocking for auto/ai)
# ============================
def main():

    if "--config" not in sys.argv:
        print("client.py: Configuration not provided")
        sys.exit(1)

    idx = sys.argv.index("--config")
    cfg_path = sys.argv[idx + 1]
    cfg = load_config(cfg_path)

    client = Client(cfg)

    # ✅ AUTO / AI 模式：自动连接，不进入 input()
    if client.mode in ("auto", "ai"):
        host = "127.0.0.1"
        port = cfg.get("auto_connect_port", 7777)

        print(f"[CLIENT] Auto/AI mode connecting to {host}:{port}")
        client.connect(host, port)

        # ✅ 自动答题循环
        while not client.stop:
            if client.waiting_for_answer:
                if client.mode == "auto":
                    ans = client.solve_auto(client.current_qmsg)
                else:
                    ans = client.solve_ai(client.current_qmsg)

                client.send_json({"message_type": "ANSWER", "answer": ans})
                client.waiting_for_answer = False

            time.sleep(0.05)

        return  # ✅ 不进入 YOU 模式

    # ✅ YOU 模式 — 手动
    print("[CLIENT] Client ready. Please type CONNECT 127.0.0.1:7777")

    while True:
        if client.waiting_for_answer:
            ans = input("Your answer: ").strip()
            client.send_json({"message_type": "ANSWER", "answer": ans})
            client.waiting_for_answer = False
            continue

        cmd = input().strip()
        if cmd.upper().startswith("CONNECT "):
            addr = cmd.split()[1]
            host, port = addr.split(":")
            client.connect(host, int(port))
        elif cmd.upper() == "DISCONNECT":
            client.disconnect()
            break
        elif cmd.upper() == "EXIT":
            client.disconnect()
            break


if __name__ == "__main__":
    main()

