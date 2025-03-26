# Welcome to
# __________         __    __  .__                               __
# \______   \_____ _/  |__/  |_|  |   ____   ______ ____ _____  |  | __ ____
#  |    |  _/\__  \\   __\   __\  | _/ __ \ /  ___//    \\__  \ |  |/ // __ \
#  |    |   \ / __ \|  |  |  | |  |_\  ___/ \___ \|   |  \/ __ \|    <\  ___/
#  |________/(______/__|  |__| |____/\_____>______>___|__(______/__|__\\_____>
#
# This file can be a nice home for your Battlesnake logic and helper functions.
#
# To get you started we've included code to prevent your Battlesnake from moving backwards.
# For more info see docs.battlesnake.com

import random
import typing
import queue
import time
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/info", methods=["GET"])
def info():
    return jsonify({
        "apiversion": "1",
        "author": "YourUsername",  # Add your username
        "color": "#FF5733",       # Choose a custom color
        "head": "beluga",         # Choose a custom head
        "tail": "round-bum",      # Choose a custom tail
    })

@app.route("/start", methods=["POST"])
def start():
    print("GAME STARTED")
    return "ok"

@app.route("/move", methods=["POST"])
def move():
    game_state = request.get_json()
    is_move_safe = {"up": True, "down": True, "left": True, "right": True}

    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"
    board_height = game_state["board"]["height"]
    board_width = game_state["board"]["width"]
    opponents = game_state["board"]["snakes"]
    food_pellets = game_state["board"]["food"]

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
                maze[segment["y"] + 1][segment["x"] + 1] = "@"  # Offset by +1 to account for walls

                # Add avoidance spots around the head if the opponent is equal or larger in size
                opponent_length = len(opponent["body"])
                my_length = len(game_state["you"]["body"])
                if opponent_length >= my_length:
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Up, Down, Left, Right
                        avoid_y = segment["y"] + dy + 1  # Offset by +1 for walls
                        avoid_x = segment["x"] + dx + 1  # Offset by +1 for walls
                        if 0 <= avoid_y < board_height + 2 and 0 <= avoid_x < board_width + 2:
                            if maze[avoid_y][avoid_x] == " ":  # Only mark empty spaces
                                maze[avoid_y][avoid_x] = "."  # Mark as avoidance spot
            else:  # Body segments of the opponent snake
                maze[segment["y"] + 1][segment["x"] + 1] = "*"  # Offset by +1 to account for walls

    # Mark your snake's body
    for i, segment in enumerate(game_state["you"]["body"]):
        if i == 0:  # Head of your snake
            maze[segment["y"] + 1][segment["x"] + 1] = "O"  # Offset by +1 to account for walls
        else:  # Body segments of your snake
            maze[segment["y"] + 1][segment["x"] + 1] = "o"  # Offset by +1 to account for walls

    # Mark food locations
    for food in food_pellets:
        # Only mark food if it hasn't been excluded by avoidance logic
        if maze[food["y"] + 1][food["x"] + 1] == " ":
            maze[food["y"] + 1][food["x"] + 1] = "X"  # Offset by +1 to account for walls

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
    ### Set Default Target ###
    ####################
    if not target_food:
        # Default target is the middle of the board
        target_food = {"x": board_width // 2, "y": board_height // 2}
        print(f"No valid food found. Defaulting target to middle of the board: {target_food}")

    def find_path(maze, stdscr):
        end = find_target_food()
        start_pos = my_head["x"], my_head["y"]

        q = queue.Queue()
        q.put((start_pos, [start_pos]))

        visited = set()

        while not q.empty():
            current_pos, path = q.get()
            row, col = current_pos

            if maze[row][col] == end:
                return path

            neighbors = find_neighbors(maze, row, col)
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                r, c = neighbor
                if maze[r][c] == "#":
                    continue

                new_path = path + [neighbor]
                q.put((neighbor, new_path))
                visited.add(neighbor)

    def find_neighbors(maze, row, col):
        neighbors = []

        if row > 0:  # Up
            neighbors.append((row - 1, col))
        if row < len(maze):  # Down
            neighbors.append((row + 1, col))
        if col > 0:  # Left
            neighbors.append((row - 1, col))
        if col + 1 < len(maze[0]):  # Right
            neighbors.append((row, col + 1))

        return neighbors

    def find_weak_snake():
        for opponent_number in range(len(opponents)):
            get_bot_num = 999
            opponent_name = opponents[opponent_number]["name"]
            opponent_length = len(opponents[opponent_number]["body"])
            my_length = len(game_state["you"]["body"])
            if game_state["you"]["name"] == opponent_name:
                print("Your Length: " + str(my_length))
            else:
                print(opponent_name + " Length:" + str(opponent_length))
                if opponent_length + 1 < my_length:
                    print("Get " + opponents[opponent_number]["name"])
                    get_bot_num = opponent_number
        return get_bot_num

    def find_target_food():
        min_dist = 999
        for food in range(len(food_pellets)):
            food_dist = (abs(my_head["x"] - food_pellets[food]["x"]) +
                         abs(my_head["y"] - food_pellets[food]["y"]))
            if min_dist > food_dist:
                min_dist = food_dist
                min_food_num = food
        print(food_pellets[min_food_num]["x"])
        one, two = food_pellets[min_food_num]["x"], food_pellets[min_food_num]["y"]
        print(f"X: {one} Y:{two}")
        end = find_target_food()
        start_pos = my_head["x"], my_head["y"]
        print(end)
        print(start_pos)
        return end

    ####################
    ### Calculate Priority Score ###
    ####################
    def calculate_priority_score(target, center):
        """
        Calculate the priority score for a target based on its distance to the center.
        :param target: Dictionary with "x" and "y" coordinates of the target.
        :param center: Tuple (x, y) representing the center of the board.
        :return: A priority score (higher is better).
        """
        distance_to_center = abs(target["x"] - center[0]) + abs(target["y"] - center[1])
        return max(0, board_width + board_height - distance_to_center)  # Higher score for closer to center

    ####################
    ### Initialize Variables ###
    ####################
    target_snake = 999  # Default value if no weaker snake is found
    target_coordinates = None
    highest_priority_score = -1

    ####################
    ### Determine Target ###
    ####################
    center_of_board = (board_width // 2, board_height // 2)

    # Check if health is greater than 75
    if game_state["you"]["health"] > 75:
        # Prioritize weaker snakes
        target_snake = find_weak_snake()
        if target_snake < 999:
            snake_head = opponents[target_snake]["body"][0]
            priority_score = calculate_priority_score({"x": snake_head["x"], "y": snake_head["y"]}, center_of_board)
            if priority_score > highest_priority_score:
                highest_priority_score = priority_score
                target_coordinates = {"x": snake_head["x"], "y": snake_head["y"]}
            print(f"Weaker Snake at {snake_head} has priority score {priority_score}")

    # Check for food if no valid snake target or health <= 75
    if not target_coordinates:
        for food in valid_food_pellets:
            priority_score = calculate_priority_score(food, center_of_board)
            if priority_score > highest_priority_score:
                highest_priority_score = priority_score
                target_coordinates = {"x": food["x"], "y": food["y"]}
            print(f"Food at {food} has priority score {priority_score}")

    # Default to the center of the board if no valid target is found
    if not target_coordinates:
        target_coordinates = {"x": center_of_board[0], "y": center_of_board[1]}
        print(f"No valid target found. Defaulting to center of the board: {target_coordinates}")
    else:
        print(f"Selected target: {target_coordinates} with priority score {highest_priority_score}")

    ####################
    ### BFS Pathfinding ###
    ####################
    def bfs_path(start, target, maze):
        """        https://battlesnake-r7i5hrftf-michael-freeloves-projects.vercel.app/info
        Perform BFS to find the shortest path from start to target in the maze.
        :param start: Tuple (x, y) representing the starting position.
        :param target: Tuple (x, y) representing the target position.
        :param maze: The maze grid.
        :return: A list of moves to reach the target or None if no path exists.
        """
        directions = {"up": (0, 1), "down": (0, -1), "left": (-1, 0), "right": (1, 0)}
        bfs_queue = queue.Queue()  # Renamed to avoid shadowing the `queue` module
        bfs_queue.put((start, []))  # (current_position, path_to_position)
        visited = set()
        visited.add(start)

        while not bfs_queue.empty():
            current_pos, path = bfs_queue.get()
            if current_pos == target:
                return path  # Return the path to the target

            for move, (dx, dy) in directions.items():
                next_pos = (current_pos[0] + dx, current_pos[1] + dy)
                if next_pos not in visited and maze[next_pos[1] + 1][next_pos[0] + 1] in [" ", "X"]:  # Valid cell
                    visited.add(next_pos)
                    bfs_queue.put((next_pos, path + [move]))

        return None  # No path found

    ####################
    ### Use BFS to Find Path ###
    ####################
    if target_coordinates:
        start_pos = (my_head["x"], my_head["y"])
        target_pos = (target_coordinates["x"], target_coordinates["y"])
        path = bfs_path(start_pos, target_pos, maze)

        if path:
            print(f"Path to target: {path}")
            next_move = path[0]  # Take the first step in the path
        else:
            print("No path to target found. Choosing a random safe move.")
            next_move = random.choice([move for move, isSafe in is_move_safe.items() if isSafe])
    else:
        print("No target found. Choosing a random safe move.")
        next_move = random.choice([move for move, isSafe in is_move_safe.items() if isSafe])

    ####################
    ### Print Final Maze ###
    ####################
    print("Final Maze:")
    for row in maze[::-1]:  # Print from top to bottom
        print("".join(row))

    ####################
    ### Enforce Avoidance ###
    ####################
    # Update is_move_safe to avoid cells marked as "."
    for move, is_safe in is_move_safe.items():
        if not is_safe:
            continue  # Skip already unsafe moves

        # Calculate the next position based on the move
        next_x, next_y = my_head["x"], my_head["y"]
        if move == "up":
            next_y += 1
        elif move == "down":
            next_y -= 1
        elif move == "left":
            next_x -= 1
        elif move == "right":
            next_x += 1

        # Check if the next position is marked as "." in the maze
        if maze[next_y + 1][next_x + 1] == ".":  # Offset by +1 for walls
            is_move_safe[move] = False

    ####################
    ### Avoid snakes ###
    ####################

    for opponent_number in range(len(opponents)):
        opponent_body = opponents[opponent_number]["body"]
        for opp_body_loc in range(len(opponent_body)):
            avoid_loc = opponent_body[opp_body_loc]

            # up
            if avoid_loc["x"] == my_head["x"] and avoid_loc["y"] == (my_head["y"] + 1):
                is_move_safe["up"] = False

            # down
            if avoid_loc["x"] == my_head["x"] and avoid_loc["y"] == (my_head["y"] - 1):
                is_move_safe["down"] = False

            # left
            if avoid_loc["x"] == (my_head["x"] - 1) and avoid_loc["y"] == my_head["y"]:
                is_move_safe["left"] = False

            # right
            if avoid_loc["x"] == (my_head["x"] + 1) and avoid_loc["y"] == my_head["y"]:
                is_move_safe["right"] = False

    ####################
    ### Avoid neck  ###
    ####################

    if my_neck["x"] < my_head["x"]:  # Neck is left of head, don't move left
        is_move_safe["left"] = False

    elif my_neck["x"] > my_head["x"]:  # Neck is right of head, don't move right
        is_move_safe["right"] = False

    elif my_neck["y"] < my_head["y"]:  # Neck is below head, don't move down
        is_move_safe["down"] = False

    elif my_neck["y"] > my_head["y"]:  # Neck is above head, don't move up
        is_move_safe["up"] = False

    ####################
    ### Avoid edges  ###
    ####################

    # Looking for board edge
    if my_head["y"] == 0:  # Neck is left of head, don't move left
        is_move_safe["down"] = False

    if my_head["y"] == board_width - 1:  # Neck is right of head, don't move right
        is_move_safe["up"] = False

    if my_head["x"] == 0:  # Neck is below head, don't move down
        is_move_safe["left"] = False

    if my_head["x"] == board_height - 1:  # Neck is above head, don't move up
        is_move_safe["right"] = False

    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    if len(safe_moves) == 0:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving down")
        return jsonify({"move": "down"})

    if target_snake < 999:
        print("Killing: " + opponents[opponent_number]["name"])
        dist_x = opponents[target_snake]["body"][0]["x"] - my_head["x"]
        dist_y = opponents[target_snake]["body"][0]["y"] - my_head["y"]

        if abs(dist_x) >= abs(dist_y):
            if dist_x >= 0:
                preferred_move = "right"
            if dist_x < 0:
                preferred_move = "left"

        if abs(dist_x) < abs(dist_y):
            if dist_y > 0:
                preferred_move = "up"
            if dist_y < 0:
                preferred_move = "down"

    elif len(food_pellets) > 0:
        dist_x = target_food["x"] - my_head["x"]
        dist_y = target_food["y"] - my_head["y"]

        if abs(dist_x) >= abs(dist_y):
            if dist_x >= 0:
                preferred_move = "right"
            if dist_x < 0:
                preferred_move = "left"

        if abs(dist_x) < abs(dist_y):
            if dist_y > 0:
                preferred_move = "up"
            if dist_y < 0:
                preferred_move = "down"

    else:
        preferred_move = random.choice(safe_moves)

    if preferred_move in safe_moves:
        next_move = preferred_move
    else:
        next_move = random.choice(safe_moves)

    print(f"MOVE {game_state['turn']}: {next_move}")
    return jsonify({"move": next_move})

@app.route("/end", methods=["POST"])
def end():
    print("GAME OVER")
    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use the PORT environment variable or default to 8000
    app.run(host="0.0.0.0", port=port)
