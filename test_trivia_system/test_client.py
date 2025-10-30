import subprocess
import time
import sys
import os
import signal


def test_client_connects():
    print("\n🔧 [TEST] Client CONNECT test")

    # ✅ Start server
    server = subprocess.Popen(
        ["python", "server.py", "--config", "test_trivia_system/configs/server_test.json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    time.sleep(1.2)

    # ✅ Start client (YOU mode)
    client = subprocess.Popen(
        ["python", "client.py", "--config", "test_trivia_system/configs/client_you_test.json"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # ✅ Send CONNECT command
    try:
        client.stdin.write("CONNECT 127.0.0.1:7777\n")
        client.stdin.flush()
    except Exception as e:
        print("❌ Failed to write to client:", e)

    # ✅ Wait for the client to print READY
    time.sleep(1.5)

    # ✅ Try non-blocking read (communicate with timeout)
    output = ""
    try:
        output, _ = client.communicate(timeout=0.5)
    except subprocess.TimeoutExpired:
        # Client did not exit → kill the process
        client.kill()
        try:
            out2, _ = client.communicate(timeout=0.2)
            output += out2
        except:
            pass

    # ✅ Stop server
    server.kill()

    print(output)

    # ✅ Check result
    if "Player connected" in output:
        print("✅ Client CONNECT test passed")
    else:
        print("❌ Client CONNECT test failed")


if __name__ == "__main__":
    test_client_connects()
