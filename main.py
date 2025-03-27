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
        "head": "missile",  # TODO: Choose head
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

    # Determine game type
    game_type = game_state["game"]["ruleset"]["name"].lower()  # Normalize to lowercase for consistency
    print(f"Game Type Detected: {game_type}")

    ####################
    ### Branch Logic Based on Game Type ###
    ####################
    if game_type == "standard":
        print("Using Standard Logic")
        return handle_standard_logic(game_state)
    elif game_type == "constrictor":
        print("Using Constrictor Logic")
        return handle_constrictor_logic(game_state)
    elif game_type == "royale":
        print("Using Royale Logic")
        return handle_royale_logic(game_state)
    else:
        print(f"Unknown game type: {game_type}. Defaulting to Standard Logic")
        return handle_standard_logic(game_state)

####################
### Standard Logic ###
####################
def handle_standard_logic(game_state):
    print("Handling Standard Logic")
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

    # Check for collisions with enemy snake bodies
    for opponent in opponents:
        for segment in opponent["body"]:
            if segment["x"] == my_head["x"] and segment["y"] == my_head["y"] + 1:
                is_move_safe["up"] = False
            if segment["x"] == my_head["x"] and segment["y"] == my_head["y"] - 1:
                is_move_safe["down"] = False
            if segment["x"] == my_head["x"] - 1 and segment["y"] == my_head["y"]:
                is_move_safe["left"] = False
            if segment["x"] == my_head["x"] + 1 and segment["y"] == my_head["y"]:
                is_move_safe["right"] = False

    ####################
    ### Filter Out Unsafe Moves ###
    ####################
    # Ensure moves into your own body and enemy bodies are marked as unsafe
    for segment in my_body + [seg for opp in opponents for seg in opp["body"]]:
        if segment["x"] == my_head["x"] and segment["y"] == my_head["y"] + 1:
            is_move_safe["up"] = False
        if segment["x"] == my_head["x"] and segment["y"] == my_head["y"] - 1:
            is_move_safe["down"] = False
        if segment["x"] == my_head["x"] - 1 and segment["y"] == my_head["y"]:
            is_move_safe["left"] = False
        if segment["x"] == my_head["x"] + 1 and segment["y"] == my_head["y"]:
            is_move_safe["right"] = False

    ####################
    ### Determine Target ###
    ####################
    target_food = None
    target_enemy = None
    my_health = game_state["you"]["health"]

    if my_health > 30:
        # Look for shorter enemy snakes to target
        closest_enemy_target = None
        min_dist = float("inf")

        for opponent in opponents:
            if opponent["id"] == game_state["you"]["id"]:
                continue  # Skip your own snake

            opponent_length = len(opponent["body"])
            my_length = len(my_body)

            if opponent_length < my_length:  # Only target shorter snakes
                opponent_head = opponent["body"][0]
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Up, Down, Left, Right
                    adjacent_y = opponent_head["y"] + dy
                    adjacent_x = opponent_head["x"] + dx

                    # Ensure the adjacent cell is within bounds and not part of the opponent's body
                    if 0 <= adjacent_y < board_height and 0 <= adjacent_x < board_width:
                        if maze[adjacent_y + 1][adjacent_x + 1] == " ":
                            dist = abs(my_head["x"] - adjacent_x) + abs(my_head["y"] - adjacent_y)
                            if dist < min_dist:
                                min_dist = dist
                                closest_enemy_target = {"x": adjacent_x, "y": adjacent_y}

        if closest_enemy_target:
            target_enemy = closest_enemy_target
            print(f"Targeting shorter enemy snake at: {target_enemy}")

    if not target_enemy:
        # Default to food targeting if no enemy target is found
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
    ### Mark Target on Maze ###
    ####################
    if target_enemy:
        maze[target_enemy["y"] + 1][target_enemy["x"] + 1] = "T"
    elif target_food:
        maze[target_food["y"] + 1][target_food["x"] + 1] = "T"

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
    target = target_enemy if target_enemy else target_food
    if target:
        start_pos = (my_head["x"], my_head["y"])
        target_pos = (target["x"], target["y"])
        path = bfs_path(start_pos, target_pos, maze)

        if path:
            print(f"Path to target: {path}")
            next_move = path[0]  # Take the first step in the path

            # Mark the path on the maze
            current_pos = start_pos
            for move in path:
                if move == "up":
                    current_pos = (current_pos[0], current_pos[1] + 1)
                elif move == "down":
                    current_pos = (current_pos[0], current_pos[1] - 1)
                elif move == "left":
                    current_pos = (current_pos[0] - 1, current_pos[1])
                elif move == "right":
                    current_pos = (current_pos[0] + 1, current_pos[1])

                # Ensure current_pos is a tuple and mark the path
                maze[current_pos[1] + 1][current_pos[0] + 1] = "P"
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

####################
### Constrictor Logic ###
####################
def handle_constrictor_logic(game_state):
    print("Handling Constrictor Logic")
    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_body = game_state["you"]["body"]  # Coordinates of your body
    board_height = game_state["board"]["height"]
    board_width = game_state["board"]["width"]
    opponents = game_state["board"]["snakes"]

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
        for segment in opponent["body"]:
            maze[segment["y"] + 1][segment["x"] + 1] = "*"

    # Mark your snake's body
    for segment in my_body:
        maze[segment["y"] + 1][segment["x"] + 1] = "o"

    ####################
    ### Mark Unsafe Areas Around Opponent Heads ###
    ####################
    for opponent in opponents:
        if opponent["id"] == game_state["you"]["id"]:
            continue  # Skip your own snake

        opponent_head = opponent["body"][0]
        opponent_length = len(opponent["body"])
        my_length = len(my_body)

        # Mark adjacent cells around the opponent's head as unsafe if their length >= our length
        if opponent_length >= my_length:
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Up, Down, Left, Right
                adjacent_y = opponent_head["y"] + dy
                adjacent_x = opponent_head["x"] + dx
                if 0 <= adjacent_x < board_width and 0 <= adjacent_y < board_height:
                    if maze[adjacent_y + 1][adjacent_x + 1] == " ":
                        maze[adjacent_y + 1][adjacent_x + 1] = "."

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

    # Check for collisions with own body and other snakes
    for segment in my_body[1:] + [seg for opp in opponents for seg in opp["body"]]:
        if segment["x"] == my_head["x"] and segment["y"] == my_head["y"] + 1:
            is_move_safe["up"] = False
        if segment["x"] == my_head["x"] and segment["y"] == my_head["y"] - 1:
            is_move_safe["down"] = False
        if segment["x"] == my_head["x"] - 1 and segment["y"] == my_head["y"]:
            is_move_safe["left"] = False
        if segment["x"] == my_head["x"] + 1 and segment["y"] == my_head["y"]:
            is_move_safe["right"] = False

    ####################
    ### Flood Fill to Calculate Free Space ###
    ####################
    def flood_fill(start_x, start_y):
        visited = set()
        queue = [(start_x, start_y)]
        free_space = 0

        while queue:
            x, y = queue.pop(0)
            if (x, y) in visited or maze[y + 1][x + 1] != " ":
                continue

            visited.add((x, y))
            free_space += 1

            # Add neighbors to the queue
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < board_width and 0 <= ny < board_height:
                    queue.append((nx, ny))

        return free_space

    ####################
    ### Evaluate Moves ###
    ####################
    move_scores = {}
    for move, is_safe in is_move_safe.items():
        if not is_safe:
            move_scores[move] = -1  # Unsafe moves get a score of -1
            continue

        # Simulate the move
        if move == "up":
            next_x, next_y = my_head["x"], my_head["y"] + 1
        elif move == "down":
            next_x, next_y = my_head["x"], my_head["y"] - 1
        elif move == "left":
            next_x, next_y = my_head["x"] - 1, my_head["y"]
        elif move == "right":
            next_x, next_y = my_head["x"] + 1, my_head["y"]

        # Calculate free space using flood fill
        move_scores[move] = flood_fill(next_x, next_y)

    ####################
    ### Print Maze and Move Scores ###
    ####################
    print("Final Maze:")
    for row in maze[::-1]:  # Print from top to bottom
        print("".join(row))

    print(f"Move {game_state['turn']} Scores: {move_scores}")  # Added move number before move scores

    ####################
    ### Choose the Best Move ###
    ####################
    best_move = max(move_scores, key=move_scores.get)  # Choose the move with the highest score
    if move_scores[best_move] == -1:
        print("No safe moves detected! Defaulting to 'down'.")
        best_move = "down"  # Default to "down" if no safe moves are available

    print(f"Chosen Move: {best_move}")  # Debug: Print chosen move

    return jsonify({"move": best_move})

####################
### Royale Logic ###
####################
def handle_royale_logic(game_state):
    print("Handling Royale Logic")
    return handle_standard_logic(game_state)

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