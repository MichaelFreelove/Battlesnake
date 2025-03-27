import random
import typing
import queue
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/info", methods=["GET"])
def info():
    print("INFO endpoint called")  # Log when the endpoint is called
    return jsonify({
        "apiversion": "1",
        "author": "",  # TODO: Your Battlesnake Username
        "color": "#888888",  # TODO: Choose color
        "head": "default",  # TODO: Choose head
        "tail": "default",  # TODO: Choose tail
    })

@app.route("/start", methods=["POST"])
def start():
    if request.is_json:
        print("START Request:")  # Log the incoming request
    else:
        print("START Request: No JSON payload received")
    print("GAME STARTED")
    return "ok"

@app.route("/move", methods=["POST"])
def move():
    game_state = request.get_json()

    # Print game details on the first move
    if game_state["turn"] == 1:
        print("Game Details:", game_state["game"])

    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_body = game_state["you"]["body"]  # Coordinates of your body
    board_height = game_state["board"]["height"]
    board_width = game_state["board"]["width"]
    opponents = game_state["board"]["snakes"]
    food_pellets = game_state["board"]["food"]

    ####################
    ### Initialize Maze ###
    ####################
    # Dynamically initialize the maze with an extra layer of walls
    maze = [["#" for _ in range(board_width + 2)] for _ in range(board_height + 2)]

    # Mark the inner playable area as empty
    for y in range(1, board_height + 1):
        for x in range(1, board_width + 1):
            maze[y][x] = " "

    # Mark opponent body segments and heads
    for opponent in opponents:
        if opponent["id"] == game_state["you"]["id"]:
            continue  # Skip your own snake

        for i, segment in enumerate(opponent["body"]):
            if i == 0:  # Head of the opponent snake
                maze[segment["y"] + 1][segment["x"] + 1] = "@"

                # Mark areas around the head as unsafe if the opponent is >= my length
                opponent_length = len(opponent["body"])
                my_length = len(my_body)
                if opponent_length >= my_length:
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Up, Down, Left, Right
                        adjacent_y = segment["y"] + dy
                        adjacent_x = segment["x"] + dx
                        if 0 <= adjacent_y < board_height and 0 <= adjacent_x < board_width:
                            if maze[adjacent_y + 1][adjacent_x + 1] == " ":  # Only mark empty spaces
                                maze[adjacent_y + 1][adjacent_x + 1] = "."

            else:  # Body segments of the opponent snake
                maze[segment["y"] + 1][segment["x"] + 1] = "*"

    # Mark your snake's body
    for i, segment in enumerate(my_body):
        if i == 0:  # Head of your snake
            maze[segment["y"] + 1][segment["x"] + 1] = "O"
        else:  # Body segments of your snake
            maze[segment["y"] + 1][segment["x"] + 1] = "o"

    # Mark food locations
    for food in food_pellets:
        # Check if the food is within one square of an enemy snake head
        is_safe_food = True
        for opponent in opponents:
            if opponent["id"] == game_state["you"]["id"]:
                continue  # Skip your own snake

            opponent_length = len(opponent["body"])
            my_length = len(my_body)
            if opponent_length >= my_length:
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Up, Down, Left, Right
                    adjacent_y = food["y"] + dy
                    adjacent_x = food["x"] + dx
                    if 0 <= adjacent_y < board_height and 0 <= adjacent_x < board_width:
                        if maze[adjacent_y + 1][adjacent_x + 1] == "@":  # Enemy head nearby
                            is_safe_food = False

        # Mark food as unsafe if it is near an enemy head
        if is_safe_food and maze[food["y"] + 1][food["x"] + 1] == " ":
            maze[food["y"] + 1][food["x"] + 1] = "X"
        elif not is_safe_food:
            maze[food["y"] + 1][food["x"] + 1] = "."  # Mark unsafe food with "."

    ####################
    ### Recalculate Target Food ###
    ####################
    def find_valid_food():
        valid_food = []
        for food in food_pellets:
            if maze[food["y"] + 1][food["x"] + 1] == "X":  # Only consider valid food spaces
                valid_food.append(food)
        return valid_food

    valid_food_pellets = find_valid_food()

    def find_closest_valid_food():
        if not valid_food_pellets:
            return None  # No valid food available
        min_dist = float("inf")
        closest_food = None
        for food in valid_food_pellets:
            dist = abs(my_head["x"] - food["x"]) + abs(my_head["y"] - food["y"])
            if dist < min_dist:
                min_dist = dist
                closest_food = food
        return closest_food

    target_food = find_closest_valid_food()

    ####################
    ### Determine Target ###
    ####################
    if not target_food:
        # Default target is the middle of the board
        target_food = {"x": board_width // 2, "y": board_height // 2}
        print(f"No valid food found. Defaulting target to middle of the board: {target_food}")
    else:
        print(f"Target food found at: {target_food}")

    # Mark the target on the maze
    if target_food:
        maze[target_food["y"] + 1][target_food["x"] + 1] = "T"

    ####################
    ### Calculate Safe Moves ###
    ####################
    # Check for walls
    if my_head["x"] == 0:
        is_move_safe["left"] = False
    if my_head["x"] == board_width - 1:
        is_move_safe["right"] = False
    if my_head["y"] == 0:
        is_move_safe["down"] = False
    if my_head["y"] == board_height - 1:
        is_move_safe["up"] = False

    # Check for collisions with own body
    for segment in my_body[1:]:  # Skip the head
        if segment["x"] == my_head["x"] and segment["y"] == my_head["y"] + 1:
            is_move_safe["up"] = False
        if segment["x"] == my_head["x"] and segment["y"] == my_head["y"] - 1:
            is_move_safe["down"] = False
        if segment["x"] == my_head["x"] - 1 and segment["y"] == my_head["y"]:
            is_move_safe["left"] = False
        if segment["x"] == my_head["x"] + 1 and segment["y"] == my_head["y"]:
            is_move_safe["right"] = False

    # Check for collisions with other snakes and unsafe areas around their heads
    for opponent in opponents:
        if opponent["id"] == game_state["you"]["id"]:
            continue  # Skip your own snake

        for i, segment in enumerate(opponent["body"]):
            if i == 0:  # Head of the opponent snake
                opponent_length = len(opponent["body"])
                my_length = len(my_body)
                if opponent_length >= my_length:
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Up, Down, Left, Right
                        adjacent_y = segment["y"] + dy
                        adjacent_x = segment["x"] + dx
                        if adjacent_x == my_head["x"] and adjacent_y == my_head["y"] + 1:
                            is_move_safe["up"] = False
                        if adjacent_x == my_head["x"] and adjacent_y == my_head["y"] - 1:
                            is_move_safe["down"] = False
                        if adjacent_x == my_head["x"] - 1 and adjacent_y == my_head["y"]:
                            is_move_safe["left"] = False
                        if adjacent_x == my_head["x"] + 1 and adjacent_y == my_head["y"]:
                            is_move_safe["right"] = False

    ####################
    ### Use BFS to Find Path ###
    ####################
    def bfs_path(start, target, maze):
        directions = {
            "up": (0, 1),
            "down": (0, -1),
            "left": (-1, 0),
            "right": (1, 0)
        }
        bfs_queue = queue.Queue()
        bfs_queue.put((start, []))  # (current_position, path_to_position)
        visited = set()
        visited.add(start)

        while not bfs_queue.empty():
            current_pos, path = bfs_queue.get()
            if current_pos == target:
                return path  # Return the path to the target

            for move, (dx, dy) in directions.items():
                next_pos = (current_pos[0] + dx, current_pos[1] + dy)
                if next_pos not in visited and maze[next_pos[1] + 1][next_pos[0] + 1] in [" ", "X", "T"]:  # Valid cell
                    visited.add(next_pos)
                    bfs_queue.put((next_pos, path + [move]))

        return None  # No path found

    ####################
    ### Determine Next Move ###
    ####################
    if target_food:
        start_pos = (my_head["x"], my_head["y"])
        target_pos = (target_food["x"], target_food["y"])
        path = bfs_path(start_pos, target_pos, maze)

        if path:
            print(f"Path to target: {path}")
            next_move = path[0]  # Take the first step in the path
        else:
            print("No path to target found. Choosing a random safe move.")
            # Filter out unsafe moves
            safe_moves = [move for move, is_safe in is_move_safe.items() if is_safe]
            print(f"Safe moves: {safe_moves}")
            if safe_moves:
                next_move = random.choice(safe_moves)
            else:
                print("No safe moves detected! Defaulting to 'down'.")
                next_move = "down"  # Default to "down" if no safe moves are available
    else:
        print("No target found. Choosing a random safe move.")
        # Filter out unsafe moves
        safe_moves = [move for move, is_safe in is_move_safe.items() if is_safe]
        print(f"Safe moves: {safe_moves}")
        if safe_moves:
            next_move = random.choice(safe_moves)
        else:
            print("No safe moves detected! Defaulting to 'down'.")
            next_move = "down"  # Default to "down" if no safe moves are available

    ####################
    ### Print Final Maze ###
    ####################
    print("Final Maze:")
    for row in maze[::-1]:  # Print from top to bottom
        print("".join(row))

    print(f"MOVE {game_state['turn']}: {next_move}")
    return jsonify({"move": next_move})

@app.route("/end", methods=["POST"])
def end():
    if request.is_json:
        print("END Request:")  # Log the incoming request
    else:
        print("END Request: No JSON payload received")
    print("GAME OVER")
    return "ok"

@app.route("/", methods=["GET"])
def root():
    return "Battlesnake server is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use the PORT environment variable or default to 8000
    app.run(host="0.0.0.0", port=port)