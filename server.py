import socket
import threading
import json
import time
import sys

ENC = "utf-8"


# =============================
# JSON send util
# =============================
def send_json(sock, obj):
    """Send newline-terminated JSON."""
    data = (json.dumps(obj) + "\n").encode(ENC)
    try:
        sock.sendall(data)
    except Exception:
        pass


# =============================
# Player object
# =============================
class Player:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.username = None
        self.points = 0
        self.last_answer = None


# =============================
# No-eval math expression evaluator
# =============================
def eval_math(expr):
    tokens = expr.split()
    prec = {"+": 1, "-": 1, "*": 2, "/": 2}

    # Shunting-yard → RPN
    output = []
    stack = []

    for t in tokens:
        if t.isdigit():
            output.append(int(t))
        elif t in prec:
            while stack and stack[-1] in prec and prec[stack[-1]] >= prec[t]:
                output.append(stack.pop())
            stack.append(t)

    while stack:
        output.append(stack.pop())

    # Evaluate RPN
    s = []
    for t in output:
        if isinstance(t, int):
            s.append(t)
        else:
            b = s.pop()
            a = s.pop()
            if t == "+":
                s.append(a + b)
            elif t == "-":
                s.append(a - b)
            elif t == "*":
                s.append(a * b)
            else:
                if b == 0:
                    s.append(0)
                else:
                    s.append(a // b)  # integer division

    return s[-1]


# =============================
# Roman numeral → int
# =============================
def roman_to_int(s):
    vals = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
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


# =============================
# IP helpers
# =============================
def ip_to_int(ip):
    a, b, c, d = map(int, ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def int_to_ip(x):
    return ".".join(str((x >> s) & 255) for s in (24, 16, 8, 0))


def network_and_broadcast(ip, prefix):
    mask = (0xffffffff << (32 - prefix)) & 0xffffffff
    base = ip_to_int(ip)
    net = base & mask
    bcast = net | (~mask & 0xffffffff)
    return int_to_ip(net), int_to_ip(bcast)


# =============================
# MAIN SERVER CLASS
# =============================
class TriviaServer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.players_needed = cfg["players"]
        self.players = []          # list of Player objects
        self.lock = threading.Lock()
        self.server_sock = None

        # Import questions
        from questions import (
            generate_mathematics_question,
            generate_roman_numerals_question,
            generate_usable_ip_question,
            generate_network_broadcast_question
        )

        self.q_mat = generate_mathematics_question
        self.q_rom = generate_roman_numerals_question
        self.q_ip = generate_usable_ip_question
        self.q_net = generate_network_broadcast_question

    # =============================
    # Accept client connections
    # =============================
    def accept_loop(self):
        while True:
            try:
                conn, addr = self.server_sock.accept()
            except OSError:
                break

            player = Player(conn, addr)
            threading.Thread(target=self.handle_client, args=(player,), daemon=True).start()

    # =============================
    # Handle one client's messages
    # =============================
    def handle_client(self, player):
        f = player.conn.makefile("r", encoding=ENC)

        for line in f:
            line = line.strip()
            if not line:
                continue

            msg = json.loads(line)
            mtype = msg.get("message_type")

            # ========== HI ==========
            if mtype == "HI":
                username = msg.get("username", "")
                if not any(c.isalnum() for c in username):
                    # Username invalid → server immediate exit
                    self.shutdown_all()
                    print("Invalid username received. Exiting.")
                    sys.exit(0)

                player.username = username

                # Add player
                with self.lock:
                    self.players.append(player)

                # Send READY (but game starts later)
                info = self.cfg["ready_info"].format(**self.cfg)
                send_json(player.conn, {"message_type": "READY", "info": info})

            # ========== Player Answer ==========
            elif mtype == "ANSWER":
                player.last_answer = str(msg.get("answer"))

            # ========== Player BYE ==========
            elif mtype == "BYE":
                break

        # Cleanup
        try:
            player.conn.close()
        except:
            pass

    # =============================
    # Generate a question
    # =============================
    def generate_short(self, qtype):
        if qtype == "Mathematics":
            return self.q_mat()
        if qtype == "Roman Numerals":
            return self.q_rom()
        if qtype == "Usable IP Addresses of a Subnet":
            return self.q_ip()
        return self.q_net()

    def compute_correct(self, qtype, short):
        if qtype == "Mathematics":
            return str(eval_math(short))
        if qtype == "Roman Numerals":
            return str(roman_to_int(short))
        if qtype == "Usable IP Addresses of a Subnet":
            _, p = short.split("/")
            return str(max(0, (2 ** (32 - int(p))) - 2))
        if qtype == "Network and Broadcast Address of a Subnet":
            ip, p = short.split("/")
            n, b = network_and_broadcast(ip, int(p))
            return f"{n} and {b}"
        return ""

    # =============================
    # Ranking logic
    # =============================
    def final_ranking(self):
        # Sort by points desc, username lexicographically
        ps = sorted(self.players, key=lambda p: (-p.points, p.username))
        heading = self.cfg["final_standings_heading"]
        lines = [heading]

        # tie-handling: same points => same place number
        place = 0
        prev_score = None
        for idx, p in enumerate(ps):
            if p.points != prev_score:
                place = idx + 1
                prev_score = p.points
            noun = (self.cfg["points_noun_singular"]
                    if p.points == 1 else
                    self.cfg["points_noun_plural"])
            lines.append(f"{place}. {p.username}: {p.points} {noun}")

        # Winner(s)
        top = ps[0].points
        winners = sorted([p.username for p in ps if p.points == top])
        if len(winners) == 1:
            lines.append(self.cfg["one_winner"].format(winners[0]))
        else:
            lines.append(self.cfg["multiple_winners"].format(", ".join(winners)))

        return "\n".join(lines)

    # =============================
    # Run the entire game
    # =============================
    def run_game(self):
        # Wait for all players
        while True:
            with self.lock:
                if len(self.players) >= self.players_needed:
                    break
            time.sleep(0.05)

        # Broadcast READY already done in HI messages
        time.sleep(float(self.cfg["question_interval_seconds"]))

        qtypes = self.cfg["question_types"]
        for qn, qt in enumerate(qtypes, 1):

            short = self.generate_short(qt)
            full = self.cfg["question_formats"][qt].format(short)

            # Broadcast QUESTION
            for p in self.players:
                p.last_answer = None
                send_json(p.conn, {
                    "message_type": "QUESTION",
                    "question_type": qt,
                    "trivia_question": f"{self.cfg['question_word']} {qn} ({qt}):\n{full}",
                    "short_question": short,
                    "time_limit": self.cfg["question_seconds"]
                })

            # Wait for answers
            end = time.time() + float(self.cfg["question_seconds"])
            while time.time() < end:
                # If all answered early → break
                if all(p.last_answer is not None for p in self.players):
                    break
                time.sleep(0.05)

            correct_answer = self.compute_correct(qt, short)

            # Send RESULT
            for p in self.players:
                ans = p.last_answer
                correct = (ans == correct_answer)
                if correct:
                    p.points += 1

                tpl = (self.cfg["correct_answer"]
                       if correct else
                       self.cfg["incorrect_answer"])
                fb = tpl.format(answer=ans, correct_answer=correct_answer)

                send_json(p.conn, {
                    "message_type": "RESULT",
                    "correct": correct,
                    "feedback": fb
                })

            # LEADERBOARD (except after last question)
            if qn < len(qtypes):
                lb = self.final_ranking()
                for p in self.players:
                    send_json(p.conn, {"message_type": "LEADERBOARD", "state": lb})
                time.sleep(float(self.cfg["question_interval_seconds"]))

        # FINISHED
        final = self.final_ranking()
        for p in self.players:
            send_json(p.conn, {
                "message_type": "FINISHED",
                "final_standings": final
            })

        # Close all connections
        self.shutdown_all()

    # =============================
    # Shut down server and all players
    # =============================
    def shutdown_all(self):
        for p in self.players:
            try:
                p.conn.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                p.conn.close()
            except:
                pass
        if self.server_sock:
            try:
                self.server_sock.close()
            except:
                pass

    # =============================
    # Start server
    # =============================
    def start(self):
        # Create socket
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind port
        try:
            self.server_sock.bind(("0.0.0.0", self.cfg["port"]))
        except OSError:
            print(f"server.py: Binding to port {self.cfg['port']} was unsuccessful")
            sys.exit(1)

        self.server_sock.listen(16)

        # Accept connections
        threading.Thread(target=self.accept_loop, daemon=True).start()

        # Run game
        self.run_game()


# =============================
# MAIN ENTRY
# =============================
def load_config(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"server.py: File {path} does not exist")
        sys.exit(1)


if __name__ == "__main__":
    if "--config" not in sys.argv:
        print("server.py: Configuration not provided")
        sys.exit(1)

    idx = sys.argv.index("--config")
    if idx + 1 >= sys.argv.__len__():
        print("server.py: Configuration not provided")
        sys.exit(1)

    cfg_path = sys.argv[idx + 1]
    cfg = load_config(cfg_path)

    TriviaServer(cfg).start()
