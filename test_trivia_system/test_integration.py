import subprocess
import socket
import time
import sys

# ============================
# Trivia.NET Integration Test Script
# ============================

def wait_for_port(host, port, timeout=5):
    """Wait until the server port is open"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket()
            sock.settimeout(1)
            sock.connect((host, port))
            sock.close()
            return True
        except:
            time.sleep(0.1)
    return False


def test_integration():
    print("🔧 [TEST] Starting Trivia.NET integration test", flush=True)

    # 1️⃣ Start the server
    server_cmd = ["python", "server.py", "--config", "test_trivia_system/configs/server_test.json"]
    server = subprocess.Popen(
        server_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    time.sleep(1)
    print("🔧 [TEST] Server launched, waiting...", flush=True)

    if not wait_for_port("127.0.0.1", 7777, timeout=10):
        print("❌ Server did not start properly")
        server.terminate()
        return

    print("✅ Server is listening on port 7777", flush=True)

    # 2️⃣ Start the client (AUTO mode)
    client_cmd = [
        "python", "client.py",
        "--config", "test_trivia_system/configs/client_auto_test.json"
    ]

    client = subprocess.Popen(
        client_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    print("🔧 [TEST] Client launched, waiting for gameplay...", flush=True)

    # 3️⃣ Capture client output until FINISHED appears
    finished = False
    start_time = time.time()

    while time.time() - start_time < 60:
        line = client.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue

        print("[CLIENT]", line.strip(), flush=True)

        if "FINISHED" in line:
            finished = True
            break

    # 4️⃣ Terminate processes
    client.terminate()
    server.terminate()

    if finished:
        print("✅ Integration test PASSED (client reached FINISHED)")
    else:
        print("❌ Integration test FAILED (client never reached FINISHED)")


if __name__ == "__main__":
    test_integration()
