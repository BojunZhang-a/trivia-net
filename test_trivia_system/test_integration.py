import subprocess
import socket
import time
import sys

# ============================
# Trivia.NET 集成测试脚本
# ============================

def wait_for_port(host, port, timeout=5):
    """等待服务器端口开放"""
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

    # 1️⃣ 启动服务器
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

    print("✅ Server listening on 7777", flush=True)

    # 2️⃣ 启动客户端（AUTO 模式）
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

    print("🔧 [TEST] Client launched, waiting for game...", flush=True)

    # 3️⃣ 捕获客户端输出直到 FINISHED
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

    # 4️⃣ 关闭进程
    client.terminate()
    server.terminate()

    if finished:
        print("✅ Integration test PASSED (client reached FINISHED)")
    else:
        print("❌ Integration test FAILED (client never reached FINISHED)")


if __name__ == "__main__":
    test_integration()
