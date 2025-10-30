import sys
from pathlib import Path

# ✅ Add project root so client.py can be imported
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from client import eval_math, roman_to_int, network_and_broadcast


def test_eval_math():
    print("🔧 test: eval_math")
    assert eval_math("1 + 2 + 3") == 6
    assert eval_math("5 * 3") == 15
    assert eval_math("8 / 2") == 4
    print("✅ eval_math passed")


def test_roman():
    print("🔧 test: roman_to_int")
    assert roman_to_int("X") == 10
    assert roman_to_int("IV") == 4
    assert roman_to_int("MCMXC") == 1990
    print("✅ roman_to_int passed")


def test_network():
    print("🔧 test: network_and_broadcast")
    n, b = network_and_broadcast("192.168.1.10", 24)
    assert n == "192.168.1.0"
    assert b == "192.168.1.255"
    print("✅ network_and_broadcast passed")


if __name__ == "__main__":
    test_eval_math()
    test_roman()
    test_network()
    print("✅ ALL UTILS TESTS PASSED")
