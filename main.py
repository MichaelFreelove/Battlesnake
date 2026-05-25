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
    ### Flood Fill Move Scoring ###
    ####################
    directions = {
        "up": (0, 1),
        "down": (0, -1),
        "left": (-1, 0),
        "right": (1, 0)
    }
    passable_cells = [" ", "X", "T"]
    immediate_move_cells = passable_cells + ["."]
    my_length = len(my_body)
    unsafe_score = -100000

    def position_key(position):
        return (position["x"], position["y"])

    def in_bounds(x, y):
        return 0 <= x < board_width and 0 <= y < board_height

    def manhattan_distance(start, target):
        return abs(start["x"] - target["x"]) + abs(start["y"] - target["y"])

    def opponent_legal_next_moves(opponent):
        opponent_head = opponent["body"][0]
        occupied_positions = set()

        for snake in opponents:
            body_segments = snake["body"]
            if snake["id"] == opponent["id"] and len(body_segments) > 1:
                body_segments = body_segments[:-1]

            for segment in body_segments:
                occupied_positions.add(position_key(segment))

        legal_moves = []
        for dx, dy in directions.values():
            next_x = opponent_head["x"] + dx
            next_y = opponent_head["y"] + dy
            if in_bounds(next_x, next_y) and (next_x, next_y) not in occupied_positions:
                legal_moves.append((next_x, next_y))

        return legal_moves

    def enemy_head_danger_scores():
        danger_scores = {}

        for opponent in opponents:
            if opponent["id"] == game_state["you"]["id"]:
                continue

            opponent_length = len(opponent["body"])
            if opponent_length > my_length:
                penalty = 2000
            elif opponent_length == my_length:
                penalty = 1000
            else:
                penalty = 25

            for square in opponent_legal_next_moves(opponent):
                danger_scores[square] = max(danger_scores.get(square, 0), penalty)

        return danger_scores

    head_danger_scores = enemy_head_danger_scores()
    print(f"Enemy Head Danger Scores: {head_danger_scores}")

    def count_reachable_space(start_x, start_y):
        visited = set()
        fill_queue = queue.Queue()
        fill_queue.put((start_x, start_y))

        while not fill_queue.empty():
            x, y = fill_queue.get()
            if (x, y) in visited:
                continue
            if not (0 <= x < board_width and 0 <= y < board_height):
                continue
            if maze[y + 1][x + 1] not in passable_cells:
                continue

            visited.add((x, y))

            for dx, dy in directions.values():
                fill_queue.put((x + dx, y + dy))

        return visited

    def count_available_exits(x, y):
        exits = 0
        for dx, dy in directions.values():
            next_x = x + dx
            next_y = y + dy
            if in_bounds(next_x, next_y) and maze[next_y + 1][next_x + 1] in passable_cells:
                exits += 1

        return exits

    def estimate_contested_territory(reachable_cells, start_x, start_y):
        contested_cells = 0
        larger_or_equal_next_moves = []

        for opponent in opponents:
            if opponent["id"] == game_state["you"]["id"]:
                continue
            if len(opponent["body"]) >= my_length:
                larger_or_equal_next_moves.extend(opponent_legal_next_moves(opponent))

        for cell_x, cell_y in reachable_cells:
            my_distance = abs(start_x - cell_x) + abs(start_y - cell_y)
            for enemy_x, enemy_y in larger_or_equal_next_moves:
                enemy_distance = abs(enemy_x - cell_x) + abs(enemy_y - cell_y)
                if enemy_distance <= my_distance:
                    contested_cells += 1
                    break

        return contested_cells

    def evaluate_territory_quality(move, next_x, next_y):
        reachable_cells = count_reachable_space(next_x, next_y)
        reachable_space = len(reachable_cells)
        available_exits = count_available_exits(next_x, next_y)
        contested_cells = estimate_contested_territory(reachable_cells, next_x, next_y)
        danger_penalty = head_danger_scores.get((next_x, next_y), 0)

        score = reachable_space
        score -= contested_cells * 3
        score -= danger_penalty

        if reachable_space < my_length:
            score -= (my_length - reachable_space) * 100
        if available_exits <= 1:
            score -= 75
        elif available_exits >= 3:
            score += 20

        territory_details = {
            "reachable": reachable_space,
            "contested": contested_cells,
            "exits": available_exits,
            "danger_penalty": danger_penalty,
            "score": score
        }
        print(f"Territory score for {move}: {territory_details}")

        return score

    def food_urgency_score(health):
        if health < 25:
            return 200
        if health <= 50:
            return 100
        return 25

    def enemy_can_contest_food(food):
        my_distance = manhattan_distance(my_head, food)

        for opponent in opponents:
            if opponent["id"] == game_state["you"]["id"]:
                continue
            if len(opponent["body"]) < my_length:
                continue

            opponent_head = opponent["body"][0]
            opponent_distance = manhattan_distance(opponent_head, food)
            if opponent_distance <= my_distance:
                return True

        return False

    def score_food_target(food, health):
        if maze[food["y"] + 1][food["x"] + 1] != "X":
            print(f"Ignoring food at {food}: marked unsafe on maze")
            return None

        distance = manhattan_distance(my_head, food)
        reachable_cells = count_reachable_space(food["x"], food["y"])
        reachable_space = len(reachable_cells)
        available_exits = count_available_exits(food["x"], food["y"])
        contested_cells = estimate_contested_territory(reachable_cells, food["x"], food["y"])
        contested_food = enemy_can_contest_food(food)

        urgency = food_urgency_score(health)
        score = urgency
        score += min(reachable_space, board_width * board_height)
        score -= distance * 8
        score -= contested_cells * 2

        if contested_food:
            score -= 120
        if reachable_space < my_length + 2:
            score -= (my_length + 2 - reachable_space) * 80
        if available_exits <= 1:
            score -= 90
        elif available_exits >= 3:
            score += 30
        if health > 50 and (contested_food or available_exits <= 1 or reachable_space < my_length * 2):
            score -= 100

        food_details = {
            "distance": distance,
            "urgency": urgency,
            "reachable": reachable_space,
            "contested_cells": contested_cells,
            "enemy_contested": contested_food,
            "exits": available_exits,
            "score": score
        }
        print(f"Food score for {food}: {food_details}")

        return score

    def choose_food_target(health):
        scored_food = {}
        best_food = None
        best_score = None

        for food in food_pellets:
            score = score_food_target(food, health)
            if score is None:
                continue

            food_key = (food["x"], food["y"])
            scored_food[food_key] = score
            if best_score is None or score > best_score:
                best_food = food
                best_score = score

        if best_food is None:
            print("No food target selected: no safe food scored well enough")
            return None, scored_food
        if health > 50 and best_score < 80:
            print(f"Ignoring food at {best_food}: high health and low food score {best_score}")
            return None, scored_food

        print(f"Chosen food target: {best_food} with score {best_score}")
        return best_food, scored_food

    def score_safe_moves(food_scores=None):
        if food_scores is None:
            food_scores = {}

        move_scores = {}
        for move, is_safe in is_move_safe.items():
            if not is_safe:
                move_scores[move] = unsafe_score
                continue

            dx, dy = directions[move]
            next_x = my_head["x"] + dx
            next_y = my_head["y"] + dy
            if maze[next_y + 1][next_x + 1] not in immediate_move_cells:
                move_scores[move] = unsafe_score
                continue

            move_scores[move] = evaluate_territory_quality(move, next_x, next_y)
            if (next_x, next_y) in food_scores:
                move_scores[move] += food_scores[(next_x, next_y)] * 0.25

        return move_scores

    def best_scored_safe_move(move_scores):
        safe_moves = [move for move, score in move_scores.items() if score > unsafe_score]
        if not safe_moves:
            return None

        return max(safe_moves, key=lambda move: move_scores[move])

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
        target_food, food_scores = choose_food_target(my_health)
    else:
        food_scores = {}

    ####################
    ### Mark Target on Maze ###
    ####################
    if target_enemy:
        maze[target_enemy["y"] + 1][target_enemy["x"] + 1] = "T"
    elif target_food:
        maze[target_food["y"] + 1][target_food["x"] + 1] = "T"

    move_scores = score_safe_moves(food_scores)
    print(f"Standard Move {game_state['turn']} Scores: {move_scores}")

    ####################
    ### Use BFS to Find Path ###
    ####################
    def bfs_path(start, target, maze):
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
            path_move = path[0]  # Take the first step in the path
            best_move = best_scored_safe_move(move_scores)
            path_score = move_scores.get(path_move, unsafe_score)
            best_score = move_scores.get(best_move, unsafe_score) if best_move else unsafe_score

            if path_score > unsafe_score and path_score + 40 >= best_score:
                next_move = path_move
            else:
                print(f"Path move {path_move} scored {path_score}. Choosing higher territory score: {best_move} ({best_score}).")
                next_move = best_move
                if next_move is None:
                    print("No safe moves detected! Defaulting to 'down'.")
                    next_move = "down"

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
            print("No path to target found. Choosing the highest-scored safe move.")
            next_move = best_scored_safe_move(move_scores)
            if next_move is None:
                print("No safe moves detected! Defaulting to 'down'.")
                next_move = "down"  # Default to "down" if no safe moves are available
    else:
        print("No target found. Choosing the highest-scored safe move.")
        next_move = best_scored_safe_move(move_scores)
        if next_move is None:
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
    return info()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use the PORT environment variable or default to 8000
    app.run(host="0.0.0.0", port=port)
