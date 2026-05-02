import httpx
import os
import sys
import time

# Configuration
GATEWAY_URL = "http://localhost:8000"
CHAR_URL    = "http://localhost:8001"
WORD_URL    = "http://localhost:8002"

TEST_IMAGE_CHAR = "tested_photos/gray_letter_A.jpeg"
TEST_IMAGE_WORD = "tested_photos/mazen_word.jpeg"

def check_health():
    print("[1/2] Checking Service Health...")
    services = {
        "Character": f"{CHAR_URL}/health",
        "Word": f"{WORD_URL}/health",
        "Gateway": f"{GATEWAY_URL}/health"
    }
    
    all_ok = True
    for name, url in services.items():
        try:
            resp = httpx.get(url, timeout=5.0)
            if resp.status_code == 200:
                print(f"OK: {name:10} is UP")
            else:
                print(f"FAIL: {name:10} returned {resp.status_code}")
                all_ok = False
        except Exception as e:
            print(f"FAIL: {name:10} is UNREACHABLE")
            all_ok = False
    return all_ok

def test_predictions():
    print("\n[2/2] Testing OCR Predictions via Gateway...")
    
    # Test Character Prediction
    if os.path.exists(TEST_IMAGE_CHAR):
        print(f"Testing Character OCR with {TEST_IMAGE_CHAR}...")
        with open(TEST_IMAGE_CHAR, "rb") as f:
            files = {"file": (TEST_IMAGE_CHAR, f, "image/jpeg")}
            resp = httpx.post(f"{GATEWAY_URL}/predict/character", files=files, timeout=30.0)
            if resp.status_code == 200:
                res = resp.json()
                print(f"SUCCESS: Character Result: {res.get('predicted_letter')} (Conf: {res.get('confidence')})")
            else:
                print(f"FAIL: Character Test Failed: {resp.text}")
    else:
        print(f"SKIP: Character test: {TEST_IMAGE_CHAR} not found.")

    # Test Word Prediction
    if os.path.exists(TEST_IMAGE_WORD):
        print(f"Testing Word OCR with {TEST_IMAGE_WORD}...")
        with open(TEST_IMAGE_WORD, "rb") as f:
            files = {"file": (TEST_IMAGE_WORD, f, "image/jpeg")}
            resp = httpx.post(f"{GATEWAY_URL}/predict/word", files=files, timeout=30.0)
            if resp.status_code == 200:
                res = resp.json()
                print(f"SUCCESS: Word Result: {res.get('predicted_word')} (Conf: {res.get('avg_confidence')})")
            else:
                print(f"FAIL: Word Test Failed: {resp.text}")
    else:
        print(f"SKIP: Word test: {TEST_IMAGE_WORD} not found.")

if __name__ == "__main__":
    print("Starting OCR System Verification Test\n")
    if check_health():
        test_predictions()
        print("\nAll tests completed.")
    else:
        print("\nTests aborted: Not all services are running.")
        sys.exit(1)
