# -*- coding: utf-8 -*-
"""by_second.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_9qlLv9X2avZ82UWYXxzP_vT-8WLzOci
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.optimize import minimize
from shapely import Polygon, Point
import shapely
import itertools
import numpy as np
import random
import logging
import copy
from collections import defaultdict
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent

logging.basicConfig(level=logging.INFO)

def angle_between(p1, p2):
    return (np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0])) + 360) % 360

class OffensivePlayer:
    def __init__(self, route_points, speed):
        self.route_points = route_points #location at 0 seconds, 1 second, 2 seconds, 3 seconds, and 4 seconds
        self.speed = speed

    def get_position_at_time(self, t_step):
        # If t_step is within the length of route_points, return the position at t_step
        if t_step < len(self.route_points):
            return self.route_points[t_step]

        # If t_step is beyond the length of route_points, return the last position
        return self.route_points[-1]

    def get_direction_at_time(self, t_step):
        t = t_step/10
        total_time = sum([dist/self.speed for dist in [np.linalg.norm(np.array(self.route_points[i+1]) - np.array(self.route_points[i])) for i in range(len(self.route_points)-1)]])

        #if the time requested is beyond the end of the route:
        if t > total_time:
            start_y = self.route_points[0][1]
            #direction towards the x=0 line at the player's starting y-coordinate
            direction = np.rad2deg(np.arctan2(0 - self.route_points[-1][1], start_y - self.route_points[-1][0]))
            return direction

        prevstep = t_step - 1
        loc_minus1 = tuple(self.calculate_positions(selected_frame=prevstep))
        loc_curr = tuple(self.calculate_positions(selected_frame=t_step))

        def angle_between_off(p1, p2):
            dy = p2[1] - p1[1]
            dx = p2[0] - p1[0]
            angle_rad = np.arctan2(dy, dx)
            angle_deg = np.degrees(angle_rad)
            return (angle_deg + 360) % 360

        direction = angle_between(loc_minus1, loc_curr)
        return direction

    def potential_next_locations_lim5(off_player, t_step):
        current_position = off_player.get_position_at_time(t_step)
        distance_moved = off_player.speed  # Moving for 1 second

        # Define the angles
        angles = [0, 90, 180, 270]

        # Calculate positions at each angle
        predicted_positions = [(round(current_position[0], 2), round(current_position[1], 2))]  # Include current position
        for angle in angles:
            angle_rad = np.radians(angle)
            dx = distance_moved * np.cos(angle_rad)
            dy = distance_moved * np.sin(angle_rad)
            new_position = (current_position[0] + dx, current_position[1] + dy)
            predicted_positions.append((round(new_position[0], 2), round(new_position[1], 2)))

        return predicted_positions


    def potential_next_locations_lim10(off_player, t_step):
        current_position = off_player.get_position_at_time(t_step)
        distance_moved = off_player.speed  # Moving for 1 second

        # Define the angles
        angles = [0, 45, 90, 135, 180, 225, 270, 315]

        # Calculate positions at each angle
        predicted_positions = [(round(current_position[0], 2), round(current_position[1], 2))]  # Include current position
        for angle in angles:
            angle_rad = np.radians(angle)
            dx = distance_moved * np.cos(angle_rad)
            dy = distance_moved * np.sin(angle_rad)
            new_position = (current_position[0] + dx, current_position[1] + dy)
            predicted_positions.append((round(new_position[0], 2), round(new_position[1], 2)))

        return predicted_positions


    def potential_next_locations_lim19(off_player, t_step):
        current_position = off_player.get_position_at_time(t_step)
        full_speed_distance = off_player.speed  # Moving for 1 second
        half_speed_distance = off_player.speed / 2  # Half the distance

        angles = [0, 45, 90, 135, 180, 225, 270, 315]

        # Calculate positions at each angle for full and half speed
        predicted_positions = [(round(current_position[0], 2), round(current_position[1], 2))]  # Include current position
        for distance_moved in [full_speed_distance, half_speed_distance]:
            for angle in angles:
                angle_rad = np.radians(angle)
                dx = distance_moved * np.cos(angle_rad)
                dy = distance_moved * np.sin(angle_rad)
                new_position = (current_position[0] + dx, current_position[1] + dy)
                predicted_positions.append((round(new_position[0], 2), round(new_position[1], 2)))

        return predicted_positions



class DefensivePlayer:
    def __init__(self, start_position, speed, allowable_area, current_position=None):
        self.start_position = np.array(start_position)
        if current_position is None:
            self.position = np.array(start_position)
        else:
            self.position = np.array(current_position)
        self.speed = speed
        self.allowable_area = allowable_area  #polygon object

    def get_position(self):
        return self.position

    def move(self, new_position):
        self.position = np.array(new_position)

    def distance_to(self, offensive_player, t_step=0):
        other_position = offensive_player.get_position_at_time(t_step)  #assuming t is the current time
        return np.linalg.norm(self.position - np.array(other_position))

    def relation_to_receiver_direction(self, theta_r, off_player_loc):

        #compute direction to defensive player
        theta_d = angle_between(off_player_loc, self.position)

        #angle difference
        delta_theta = (theta_d - theta_r + 360) % 360

        #check which sixth the defensive player lies in
        if 0 <= delta_theta < 60:
            return 1  # Front sixth
        elif 60 <= delta_theta < 180:
            return 2  #adjacent sixths (still in front half)
        else:
            return 3  #otherwise

    def potential_move_points_lim10(self):
        potential_points = []

        #create a range of movement values based on speed
        range_movement = np.arange(-self.speed, self.speed + 0.1, 0.1)

        for dx in range_movement:
            for dy in range_movement:
                #check if the combined movement is within the speed limit
                if np.sqrt(dx**2 + dy**2) <= self.speed:
                    #generate potential point by adding delta to current position
                    potential_point = (round(self.position[0] + dx, 1), round(self.position[1] + dy, 1))
                    potential_points.append(potential_point)

        #use set to filter out duplicates
        potential_points = list(set(potential_points))

        #filter points outside the allowable area
        allowed_points = [point for point in potential_points if Point(point).within(self.allowable_area)]

        return allowed_points

    def potential_move_points_lim5(self):
        x, y = self.position

        #potential points in the four cardinal directions
        potential_points = [
            (x, y + self.speed),  # up
            (x, y - self.speed),  # down
            (x - self.speed, y),  # left
            (x + self.speed, y)   # right
        ]

        #filter points to ensure they lie within the allowable area
        valid_points = [Point(p).intersection(self.allowable_area) for p in potential_points]

        #if a point lies on the boundary, keep that point. Otherwise, keep the original position.
        move_points = [p.coords[0] if p.within(self.allowable_area) or p.touches(self.allowable_area) else (x, y) for p in valid_points]

        #add current position to the list
        move_points.append((x, y))

        #get unique values
        move_points = list(set(move_points))

        return move_points


def all_available_defensive_moves(defensive_player_list):
    all_move_combinations = list(itertools.product(*[player.potential_move_points_lim5() for player in defensive_player_list]))
    return all_move_combinations



class GameState:
    def __init__(self, offensive_players=[], defensive_players=[], time_step=0):
        self.offensive_players = offensive_players
        self.time_step = time_step
        self.defensive_players = defensive_players

    def __str__(self):
        offensive_positions = [player.get_position_at_time(self.time_step) for player in self.offensive_players]  # Adjust based on your player object's structure
        defensive_positions = [player.get_position() for player in self.defensive_players]  # Adjust based on your player object's structure
        return f"GameState(time_step={self.time_step}, offensive_positions={offensive_positions}, defensive_positions={defensive_positions}\n)"

    def get_current_offensive_positions(self):
        #use the current time_step and the OffensivePlayer objects to get current positions
        return [player.get_position_at_time(self.time_step) for player in self.offensive_players]

    def get_time_step(self):
        return self.time_step

    def find_nearest_defender(self, off_player, predicted_pos):
        nearest_defender = None
        min_distance = float('inf')
        relative_angle = 0

        for def_player in self.defensive_players:
            distance = np.linalg.norm(np.array(def_player.get_position()) - np.array(predicted_pos))
            angle = self.calculate_relative_angle(off_player, predicted_pos, def_player.get_position())

            if distance < min_distance:
                nearest_defender = def_player
                min_distance = distance
                relative_angle = angle

        return nearest_defender, min_distance, relative_angle

    def calculate_relative_angle(self, off_player, predicted_pos, def_pos):
        # Calculate the direction of movement
        direction_vector = np.array(predicted_pos) - np.array(off_player.get_position_at_time(self.time_step))
        movement_angle = np.degrees(np.arctan2(direction_vector[1], direction_vector[0]))

        # Calculate the angle to the defender
        defender_vector = np.array(def_pos) - np.array(predicted_pos)
        defender_angle = np.degrees(np.arctan2(defender_vector[1], defender_vector[0]))

        # Calculate the relative angle
        relative_angle = (defender_angle - movement_angle + 360) % 360
        return relative_angle

    def evaluate_openness(self, off_player, predicted_pos):
        # Find the nearest defensive player and their distance and relative angle
        nearest_defender, distance, relative_angle = self.find_nearest_defender(off_player, predicted_pos)

        # Scoring based on relative position and distance
        if distance > 3:
            return 10  # Open if no defender within 5 distance units
        elif 45 <= relative_angle <= 135 and distance <= 3:
            return 2  # Less open if defender is directly in the path
        elif (0 <= relative_angle < 45 or 135 < relative_angle <= 180) and distance <= 2:
            return 4  # Somewhat open if defender is to the side
        else:
            return 0  # Not open if defender is very close


    def objective_function(self):
        total_score = 0
        penalty_for_open_receiver = 1000  # High penalty for leaving a receiver open
        for off_player in self.offensive_players:
            predicted_positions = off_player.potential_next_locations_lim5(self.time_step)
            for predicted_pos in predicted_positions:
                openness_score = self.evaluate_openness(off_player, predicted_pos)

                # Adjust the score based on openness
                if openness_score > 5:  # If the receiver is largely open
                    total_score += penalty_for_open_receiver
                else:
                    total_score += openness_score

        return total_score


    def get_legal_actions(self):
        available_moves = all_available_defensive_moves(self.defensive_players)
        return available_moves

    def is_game_over(self):
        min_route_length = min(len(player.route_points) for player in self.offensive_players)
        return self.time_step >= min_route_length

    #TODO
    def game_result(self):
        if self.is_game_over():
            """
            # Check for five consecutive scores above 40 anywhere in the list
            for i in range(len(self.objective_scores) - 4):
                if all(score > 40 for score in self.objective_scores[i:i+5]):
                    return -1  # Loss for defense"""
            return 1  # Win for defense
        return 0 #game ongoing

    def move(self, action):
        # Deep copy players to ensure complete independence of game states
        new_offensive_players = copy.deepcopy(self.offensive_players)
        new_defensive_players = copy.deepcopy(self.defensive_players)

        # Apply action to new defensive players
        for player, new_position in zip(new_defensive_players, action):
            player.move(new_position)

        # Create a new GameState instance reflecting the new state of the game
        new_state = GameState(new_offensive_players, new_defensive_players, self.time_step + 1)
        return new_state


def find_best_path_bfs(initial_state):
    current_state = initial_state
    best_action_sequence = []

    while not current_state.is_game_over():
        min_score = float('inf')
        best_next_state = None
        best_action = None

        for action in current_state.get_legal_actions():
            next_state = current_state.move(action)
            if next_state:
                score = next_state.objective_function()
                if score < min_score:
                    min_score = score
                    best_next_state = next_state
                    best_action = action

        if best_next_state:
            best_action_sequence.append(best_action)
            current_state = best_next_state
        else:
            # Handle case where no valid next states are found
            break

    return best_action_sequence

#player initialization

#offensive players
opl1 = [(20, 20), (20, 30), (24, 33), (24, 42),(25, 46)]
opl2 = [(-20, 20), (-20, 28), (-12, 28), (-2, 28), (4, 30)]
opl3 = [(-16, 19), (-16, 27), (-18, 23), (-26,23), (-26, 30)]
opl4 = [(2, 15), (16, 17), (23, 23)]

receiver1 = OffensivePlayer(opl1, 10) # 1 yard per 0.1 seconds = 10s 100yd dash
receiver2 = OffensivePlayer(opl2, 8)
receiver3 = OffensivePlayer(opl3, 9)
receiver4 = OffensivePlayer(opl4, 8)

#defensive players
allowable_area2 = Polygon([(-27,0), (27,0), (27,100), (-27,100)])
defplayer1 = DefensivePlayer((20,21), 9, allowable_area2)#cb1
defplayer2 = DefensivePlayer((-20,21), 10, allowable_area2)#cb2
defplayer3 = DefensivePlayer((-15,23), 9, allowable_area2)#ncb
defplayer4 = DefensivePlayer((0,25), 9, allowable_area2)#lb
defplayer5 = DefensivePlayer((-8,30), 8, allowable_area2)#lb
defplayer6 = DefensivePlayer((8,30), 8, allowable_area2)#lb

#running the code
defensive_players = [defplayer1,defplayer2,defplayer3,defplayer4,defplayer5,defplayer6]
offensive_players = [receiver1,receiver2, receiver3]

# Usage example
initial_state = GameState(offensive_players=offensive_players, defensive_players=defensive_players)
best_actions = find_best_path_bfs(initial_state)
print("Best action sequence:", best_actions)

def plot_players_at_time(t, receivers, best_actions):
    fig, ax = plt.subplots(figsize=(8, 5))

    # Plotting receivers
    for idx, receiver in enumerate(receivers, 1):
        # Check if the timestep is within the route points length
        if t < len(receiver.route_points):
            position = receiver.get_position_at_time(t)
            ax.scatter(*position, label=f'Receiver {idx}', s=100, c='blue')

    # Append initial positions of defenders for t=0
    if t == 0:
        initial_positions = [defender.get_position() for defender in defensive_players]
        defensive_positions = initial_positions
    else:
        # For t > 0, use the positions from best_actions
        defensive_positions = best_actions[t - 1]  # t - 1 since best_actions starts from t=1

    # Plotting defenders
    for defender_idx, position in enumerate(defensive_positions, 1):
        ax.scatter(*position, label=f'Defender {defender_idx}', s=100, c='red', marker='^')

    ax.set_xlim([-30, 30])
    ax.set_ylim([0, 100])
    ax.axhline(y=0, color='grey', linestyle='--')
    ax.axvline(x=6.1, color='grey', linestyle='--')
    ax.axvline(x=-6.1, color='grey', linestyle='--')
    ax.set_title(f"Players' positions at t={t} seconds")
    ax.set_aspect('equal', adjustable='box')
    ax.legend(loc='upper left')
    plt.show()

# Example usage
for t in range(len(best_actions) ):  # +1 to include initial position at t=0
    plot_players_at_time(t, offensive_players, best_actions)