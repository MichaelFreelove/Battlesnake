import requests

BASE_URL = "https://battlesnake-30ulcor4m-michael-freeloves-projects.vercel.app"  # Change this to your deployed URL if testing remotely

# Test /info endpoint
def test_info():
    response = requests.get(f"{BASE_URL}/info")
    print("INFO Response:", response.json())

# Test /start endpoint
def test_start():
    response = requests.post(f"{BASE_URL}/start")
    print("START Response:", response.text)

# Test /move endpoint
def test_move():
    payload = {
        "game": {"id": "game-id"},
        "turn": 1,
        "board": {
            "height": 11,
            "width": 11,
            "food": [{"x": 5, "y": 5}],
            "snakes": [
                {
                    "id": "snake-id",
                    "name": "My Battlesnake",
                    "health": 100,
                    "body": [{"x": 0, "y": 0}, {"x": 0, "y": 1}, {"x": 0, "y": 2}],
                    "head": {"x": 0, "y": 0},
                    "length": 3
                }
            ]
        },
        "you": {
            "id": "snake-id",
            "name": "My Battlesnake",
            "health": 100,
            "body": [{"x": 0, "y": 0}, {"x": 0, "y": 1}, {"x": 0, "y": 2}],
            "head": {"x": 0, "y": 0},
            "length": 3
        }
    }
    response = requests.post(f"{BASE_URL}/move", json=payload)
    print("MOVE Response:", response.json())

# Test /end endpoint
def test_end():
    response = requests.post(f"{BASE_URL}/end")
    print("END Response:", response.text)

if __name__ == "__main__":
    print("Testing /info endpoint...")
    test_info()
    print("\nTesting /start endpoint...")
    test_start()
    print("\nTesting /move endpoint...")
    test_move()
    print("\nTesting /end endpoint...")
    test_end()
