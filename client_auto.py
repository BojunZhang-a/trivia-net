import socket
import json
import time

ENC = "utf-8"

def send_json(sock, obj):
    data = (json.dumps(obj) + "\n").encode(ENC)
    sock.sendall(data)

def recv_json_lines(sock):
    f = sock.makefile("r", encoding=ENC)
    for line in f:
        line = line.strip()
        if line:
            yield json.loads(line) 

# Automatically solve Roman Numerals
def roman_to_int(s):
    vals = {"I":1,"V":5,"X":10,"L":50,"C":100,"D":500,"M":1000}
    total = 0
    prev = 0
    for ch in reversed(s.strip().upper()):
        v = vals[ch]
        if v < prev:
            total -= v
        else:
            total += v
        prev = v
    return total

# Automatically solve IP address questions
def ip_to_int(ip):
    a,b,c,d = map(int, ip.split("."))
    return (a<<24)|(b<<16)|(c<<8)|d

def int_to_ip(x):
    return ".".join(str((x>>s)&255) for s in (24,16,8,0))

def network_and_broadcast(ip, prefix):
    mask = (0xffffffff << (32-prefix)) & 0xffffffff
    ipi = ip_to_int(ip)
    net = ipi & mask
    bcast = net | (~mask & 0xffffffff)
    return int_to_ip(net), int_to_ip(bcast)

def auto_answer(qtype, short):
    if qtype == "Mathematics":
        return str(eval(short))

    if qtype == "Roman Numerals":
        return str(roman_to_int(short))

    if qtype == "Usable IP Addresses of a Subnet":
        _, prefix = short.split("/")
        return str(max(0, 2**(32-int(prefix)) - 2))

    if qtype == "Network and Broadcast Address of a Subnet":
        ip, prefix = short.split("/")
        n, b = network_and_broadcast(ip, int(prefix))
        return f"{n} and {b}"

    return "0"

def main():
    print("🤖 Auto client starting...")

    sock = socket.socket()
    sock.connect(("127.0.0.1", 7777))

    print("✅ Connected to server, sending HI...")
    send_json(sock, {"message_type": "HI", "username": "auto_client"})

    for msg in recv_json_lines(sock):

        mtype = msg["message_type"]

        if mtype == "READY":
            print("✅ Server is ready:", msg["info"])

        elif mtype == "QUESTION":
            qtype = msg["question_type"]
            short = msg["short_question"]

            print("\n📘 Received question:", msg["trivia_question"])
            ans = auto_answer(qtype, short)

            print("🧠 Auto answer:", ans)
            send_json(sock, {"message_type": "ANSWER", "answer": ans})

        elif mtype == "RESULT":
            print("📌 Result:", msg["feedback"])

        elif mtype == "FINISHED":
            print("\n🏁 Game finished!")
            print(msg["final_standings"])
            break

if __name__ == "__main__":
    main()
