import subprocess
import time
import socket
import os
import signal


SERVER_CMD = [
    "python",
    "server.py",
    "--config",
    "test_trivia_system/configs/server_test.json"
]


def test_server_starts():
    print("🔧 [TEST] Starting server...")

    # Start the server
    p = subprocess.Popen(
        SERVER_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    time.sleep(1.5)  # Give the server some time to initialize

    ok = False
    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect(("127.0.0.1", 7777))
        ok = True
        s.close()
    except Exception as e:
        print("⚠️ Connection error:", e)
        ok = False

    # Terminate the server process
    p.terminate()

    if ok:
        print("✅ Server start test passed")
    else:
        print("❌ Server start test failed")


if __name__ == "__main__":
    test_server_starts()
