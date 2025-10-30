import subprocess
import time
import sys
import os
import signal


def test_client_connects():
    print("\n🔧 [TEST] Client CONNECT test")

    # ✅ 启动 server
    server = subprocess.Popen(
        ["python", "server.py", "--config", "test_trivia_system/configs/server_test.json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    time.sleep(1.2)

    # ✅ 启动 client（YOU 模式）
    client = subprocess.Popen(
        ["python", "client.py", "--config", "test_trivia_system/configs/client_you_test.json"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # ✅ 发送 CONNECT 指令
    try:
        client.stdin.write("CONNECT 127.0.0.1:7777\n")
        client.stdin.flush()
    except Exception as e:
        print("❌ Failed to write to client:", e)

    # ✅ 等待一段时间让 client 打印 READY
    time.sleep(1.5)

    # ✅ 尝试非阻塞读取（communicate 有 timeout）
    output = ""
    try:
        output, _ = client.communicate(timeout=0.5)
    except subprocess.TimeoutExpired:
        # 说明 client 还没退出 → 强制停止
        client.kill()
        try:
            out2, _ = client.communicate(timeout=0.2)
            output += out2
        except:
            pass

    # ✅ 停止 server
    server.kill()

    print(output)

    # ✅ 判断结果
    if "Player connected" in output:
        print("✅ Client CONNECT test passed")
    else:
        print("❌ Client CONNECT test failed")


if __name__ == "__main__":
    test_client_connects()
