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
import curses
from curses import wrapper
import queue
import time

# info is called when you create your Battlesnake on play.battlesnake.com
# and controls your Battlesnake's appearance
# TIP: If you open your Battlesnake URL in a browser you should see this data
def info() -> typing.Dict:
    print("INFO")

    return {
        "apiversion": "1",
        "author": "",  # TODO: Your Battlesnake Username
        "color": "#888888",  # TODO: Choose color
        "head": "missle",  # TODO: Choose head
        "tail": "default",  # TODO: Choose tail
    }


  # start is called when your Battlesnake begins a game
def start(game_state: typing.Dict):
    print("GAME STARTED")



# end is called when your Battlesnake finishes a game
def end(game_state: typing.Dict):
    print("GAME OVER\n")


# move is called on every turn and returns your next move
# Valid moves are "up", "down", "left", or "right"
# See https://docs.battlesnake.com/api/example-move for available data






def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {
      "up": True, 
      "down": True, 
      "left": True, 
      "right": True
    }



    # We've included code to prevent your Battlesnake from moving backwards
    my_head = game_state["you"]["body"][0]  # Coordinates of your head
    my_neck = game_state["you"]["body"][1]  # Coordinates of your "neck"
    board_height = game_state["board"]["height"]
    board_width = game_state["board"]["width"]
    opponents = game_state['board']['snakes']
    food_pellets = game_state["board"]["food"]

    maze = [
    ["#", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", "#"],
    ["#", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#", "#"]
    ]

    for opponent_number in range(len(opponents)):
      
      opponent_body = opponents[opponent_number]["body"]
      for opp_body_loc in range(len(opponent_body)): 
        block_x = opponent_body[opp_body_loc]["y"]
        block_y = opponent_body[opp_body_loc]["x"]
        print(f"X: {block_x} Y:{block_y}")
        maze[block_x][block_y] = "#"

    min_dist = 999
    for food in range(len(food_pellets)):
      food_dist = ((abs(my_head["x"] - food_pellets[food]["x"])) + 
            (abs(my_head["y"] - food_pellets[food]["y"])))
      if min_dist > food_dist:
        min_dist = food_dist
        min_food_num = food
    one, two = food_pellets[min_food_num]["y"], food_pellets[min_food_num]["x"]
    maze[one][two] = "X"   
    maze[my_head["x"]][my_head["y"]] = "O"

  
    for i in range(12,0, -1):
      print(maze[i])  
      print("\n")

  
  
    def find_path(maze, stdscr):
        end = find_target_food()
        start_pos = start_pos = my_head["x"], my_head["y"]
    
        q= queue.Queue()
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
    
        if row > 0:#Up
            neighbors.append((row - 1, col))
        if row < len(maze):#Down
            neighbors.append((row + 1, col))
        if col > 0:#Left
            neighbors.append((row, col - 1))
        if col + 1 < len(maze[0]):#Right
            neighbors.append((row, col + 1))
    
        return neighbors

  
  

    def find_weak_snake():
      for opponent_number in range(len(opponents)):
       get_bot_num = 999
       opponent_name = opponents[opponent_number]["name"]
       opponent_length = len(opponents[opponent_number]["body"])
       my_length = (len(game_state["you"]["body"]))
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
        food_dist = ((abs(my_head["x"] - food_pellets[food]["x"])) + 
              (abs(my_head["y"] - food_pellets[food]["y"])))
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


  
    def find_close_food():
      min_dist = 999
      for food in range(len(food_pellets)):
        food_dist = ((abs(my_head["x"] - food_pellets[food]["x"])) + 
              (abs(my_head["y"] - food_pellets[food]["y"])))
        if min_dist > food_dist:
          min_dist = food_dist
          min_food_num = food
      return min_food_num

    if len(food_pellets) > 0:
      target_food = find_close_food()

  
    target_snake = find_weak_snake()
  
    

  
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
        return {"move": "down"}


    print(target_snake)

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
      dist_x = food_pellets[target_food]["x"] - my_head["x"]
      dist_y = food_pellets[target_food]["y"] - my_head["y"]
  
    
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
    return {"move": next_move}


# Start server when `python main.py` is run
if __name__ == "__main__":
    from server import run_server

    run_server({
        "info": info, 
        "start": start, 
         "move": move, 
        "end": end
    })
