import socket
import time


def test_nc_sim():
    print("\n🔧 [TEST] nc simulation test")

    s = socket.socket()
    try:
        s.connect(("127.0.0.1", 7777))
        print("✅ nc simulation connected successfully")
    except Exception as e:
        print("❌ nc simulation failed:", e)

    s.close()


if __name__ == "__main__":
    test_nc_sim()
