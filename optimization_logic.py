import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.optimize import minimize
from shapely import Polygon, Point
import itertools
import numpy as np
import random
import logging
import copy
from collections import defaultdict

logging.basicConfig(level=logging.INFO)

def angle_between(p1, p2):
    return (np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0])) + 360) % 360

class OffensivePlayer:
    def __init__(self, route_points, speed):
        self.route_points = route_points
        self.speed = speed

    def get_position_at_time(self, t_step):
        return self.calculate_positions(selected_frame=t_step)

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


    def calculate_positions(self, time_duration_per_step=0.1, play_frames=50, selected_frame=None):
        playerspeed = self.speed*10
        total_play_time = play_frames * time_duration_per_step

        segment_distances = [np.linalg.norm(np.array(self.route_points[i+1]) - np.array(self.route_points[i])) 
                             for i in range(len(self.route_points)-1)]
        segment_times = [dist/playerspeed for dist in segment_distances]

        time_intervals = np.arange(0, total_play_time, time_duration_per_step)

        current_segment = 0
        current_position = np.array(self.route_points[0], dtype=float)
        positions = [current_position]

        for t in time_intervals[1:]:
            if current_segment < len(segment_distances):
                direction_vector = np.array(self.route_points[current_segment+1]) - np.array(self.route_points[current_segment])
                direction_vector = direction_vector.astype(float)
                direction_vector /= np.linalg.norm(direction_vector)

                segment_elapsed_time = t - sum(segment_times[:current_segment])
                movement_distance = segment_elapsed_time * playerspeed
                new_position = np.array(self.route_points[current_segment]) + direction_vector * movement_distance

                #check if the calculated new_position has overshot the current segment's endpoint
                if np.linalg.norm(new_position - self.route_points[current_segment]) > segment_distances[current_segment]:
                    current_segment += 1
                    if current_segment < len(segment_distances):
                        residual_distance = movement_distance - segment_distances[current_segment - 1]
                        direction_vector = np.array(self.route_points[current_segment+1]) - np.array(self.route_points[current_segment])
                        direction_vector = direction_vector.astype(float)
                        direction_vector /= np.linalg.norm(direction_vector)
                        new_position = np.array(self.route_points[current_segment]) + direction_vector * residual_distance
                    else:
                        new_position = self.route_points[-1]
                positions.append(list(new_position))
            else:
                positions.append(self.route_points[-1])

        if len(positions) > play_frames:
            positions = positions[:play_frames]
        elif len(positions) < play_frames:
            positions.extend([positions[-1]] * (play_frames - len(positions)))

        rounded_positions = [(round(pos[0], 2), round(pos[1], 2)) for pos in positions]

        if selected_frame == None:
            return rounded_positions
        else:
            return rounded_positions[selected_frame]
        


def predict_offensive_position_off(off_player, t_step, reaction_time=2):
    
    if t_step < reaction_time:
        return off_player.get_position_at_time(t_step)
    
    past_step = t_step-reaction_time

    #get the player's direction and position at the past time step
    past_direction_deg = off_player.get_direction_at_time(past_step)
    past_position = off_player.calculate_positions(selected_frame=past_step)

    #convert the direction from degrees to a unit vector
    past_direction_rad = np.radians(past_direction_deg)
    direction_vector = np.array([np.cos(past_direction_rad), np.sin(past_direction_rad)])

    #predict the new position based on speed and direction
    distance_moved = off_player.speed * reaction_time # speed * time
    predicted_position = past_position + (direction_vector * distance_moved)

    return (round(predicted_position[0], 2), round(predicted_position[1], 2))


def full_offensive_position(off_players, time_step):
    full_list = list(tuple(singleoff.calculate_positions(selected_frame=time_step)) for singleoff in off_players)
    return full_list

#need to address ts=1
#ts=49 should be closer given angle of direction of the player
def full_offensive_position_pred(off_players, time_step):
    full_list = list(tuple(predict_offensive_position_off(singleoff, time_step)) for singleoff in off_players)
    return full_list



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
    
    def potential_move_points(self):
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
    
    def potential_move_points_limited_to_five(self):
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
    all_move_combinations = list(itertools.product(*[player.potential_move_points_limited_to_five() for player in defensive_player_list]))
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
        return [player.calculate_positions(selected_frame = self.time_step) for player in self.offensive_players]

    def get_predicted_offensive_positions(self):
        #use the next time_step and the OffensivePlayer objects to get predicted positions
        return [predict_offensive_position_off(player, self.time_step + 1) for player in self.offensive_players]

    def get_time_step(self):
        return self.time_step
    
    def objective_function(self):
        totalscore = 0
        for i in self.offensive_players:
            print('Current offensive position: ',i.get_position_at_time(self.time_step),'\n')
            print('Predicted offensive position: ',predict_offensive_position_off(i, self.time_step),'\n')
            savescore = 10000000
            for j in self.defensive_players:
                def_positioning = j.relation_to_receiver_direction(i.get_direction_at_time(self.time_step),predict_offensive_position_off(i, self.time_step) #i.get_position_at_time(self.time_step)
                                                                  )
                currscore = (j.distance_to(i, self.time_step)**2)*(def_positioning**2)
                if currscore < savescore:
                    savescore = currscore
                
            totalscore += savescore
        print(totalscore)
        return totalscore
    
    def get_legal_actions(self):
        available_moves = all_available_defensive_moves(self.defensive_players)
        return available_moves
    
    def is_game_over(self):
        #check for five consecutive scores above 40 in the latest scores
        """
        if len(self.objective_scores) >= 5:
            if all(score > 40 for score in self.objective_scores[-5:]):
                logging.info(f"Game over detected at timestep {self.time_step} due to objective scores.")
                return True"""

        #check play length based on number of defensive players
        defensive_count = len(self.defensive_players)
        if defensive_count >= 8:
            play_length = 50
        elif defensive_count == 7:
            play_length = 40
        elif defensive_count == 6:
            play_length = 35
        else:
            play_length = 30
        if self.time_step >= play_length:
            logging.info(f"Game over detected at timestep {self.time_step} due to reaching play length.")
            return True
        return False
        #return self.time_step >= 30

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

        # Create a new GameState instance
        new_state = GameState(new_offensive_players, new_defensive_players, self.time_step + 1)
        score = new_state.objective_function()

        if score < 3000:
            print(f"Making move: {action} at timestep {self.time_step}, Score: {score}\n")
            print(f"New state details: {new_state}\n")            
            return new_state
        else:
            print(f"NOT making move: {action} at timestep {self.time_step}, Score: {score}\n")
            return None


class MonteCarloTreeSearchNode():
    def __init__(self, state, parent=None, parent_action=None):
        self.state = state
        self.parent = parent
        self.parent_action = parent_action
        self.children = []
        self.action_sequence = [] if not parent else parent.action_sequence + [parent_action]
        self._number_of_visits = 0
        self._results = defaultdict(int)
        self._results[1] = 0
        self._results[-1] = 0
        self._untried_actions = None
        self._untried_actions = self.untried_actions()
        return
    
    
    def untried_actions(self):
        self._untried_actions = self.state.get_legal_actions()
        return self._untried_actions

    
    def q(self):
        wins = self._results[1]
        loses = self._results[-1]
        return wins - loses

    
    def n(self):
        return self._number_of_visits

    
    def expand(self):
        while self._untried_actions:
            action = self._untried_actions.pop()
            next_state = self.state.move(action)
            if next_state:  # Move is viable
                print('Next action to be taken: ',action)
                print('Existing action sequence: ',self.action_sequence)
                new_action_sequence = self.action_sequence + [action]
                child_node = MonteCarloTreeSearchNode(next_state, parent=self, parent_action=action)
                child_node.action_sequence = new_action_sequence
                self.children.append(child_node)
                logging.info(f"Expanding: Action={action}, Child Node={child_node}, Child Action Sequence={new_action_sequence}, Parent Node={self}, Parent Action Sequence={self.action_sequence}")
                return child_node
        logging.info("No more actions to expand")
        return None  # All actions tried and not viable

    
    def is_terminal_node(self):
        if self.state.is_game_over():
            logging.info(f"Node at timestep {self.state.get_time_step()} is terminal.")
            return True
        return False

    
    def rollout(self):
        current_rollout_state = self.state
        rollout_sequence = []  # Initialize the sequence of actions
        while not current_rollout_state.is_game_over():
            possible_moves = current_rollout_state.get_legal_actions()
            action = self.rollout_policy(possible_moves)
            logging.info(f"Rollout: Taking action {action} at timestep {current_rollout_state.get_time_step()}.")
            current_rollout_state = current_rollout_state.move(action)
            rollout_sequence.append(action)

            if not current_rollout_state:  # Handle non-viable move
                logging.info("Non-viable move encountered. Ending rollout.")
                return -1, rollout_sequence  # Return the result and the sequence

        result = current_rollout_state.game_result()
        logging.info(f"Rollout finished with result: {result} at timestep {self.state.get_time_step()}.")
        return result, rollout_sequence  # Return the result and the sequence

    
    def backpropagate(self, result):
        self._number_of_visits += 1.
        self._results[result] += 1.
        logging.info(f"Backpropagating with result: {result} from node at timestep {self.state.get_time_step()}.")
        if self.parent:
            self.parent.backpropagate(result)

            
    def is_fully_expanded(self):
        return len(self._untried_actions) == 0

    
    def best_child(self, c_param=10):
        if not self.children:  # Check if there are no children
            logging.info("No children to select from.")
            return None

        choices_weights = [
            (c.q() / c.n()) + c_param * np.sqrt((2 * np.log(self.n()) / c.n()))
            for c in self.children
        ]
        return self.children[np.argmax(choices_weights)]


    
    def rollout_policy(self, possible_moves):
        return possible_moves[np.random.randint(len(possible_moves))]

    
    def _tree_policy(self):
        current_node = self
        while not current_node.is_terminal_node():
            if not current_node.is_fully_expanded():
                expanded_node = current_node.expand()
                if expanded_node is not None:
                    return expanded_node
                else:
                    logging.info(f"No more viable expansions at timestep {current_node.state.get_time_step()}.")
                    break
            else:
                current_node = current_node.best_child()
                if current_node is None:
                    logging.info(f"No best child found at timestep {current_node.state.get_time_step()}.")
                    break
        return current_node


    def best_action(self):
        simulation_no = 100
        best_node = None
        best_rollout_sequence = []
        for i in range(simulation_no):
            logging.info(f"Starting simulation {i + 1} of {simulation_no}...")
            v = self._tree_policy()
            if v is not None:
                reward, rollout_sequence = v.rollout()
                v.backpropagate(reward)
                if reward == 1:
                    best_node = v  # Save the winning node
                    best_rollout_sequence = rollout_sequence
                    logging.info(f"Winning sequence found at simulation {i + 1}, Node={v}, Action Sequence={v.action_sequence}")
                    break
            else:
                logging.info("No viable actions found in tree policy.")
                break
        
        if best_node is not None:
            logging.info(f"Best Node Depth (Time Step): {best_node.state.get_time_step()}, Best Node Action Sequence Length: {len(best_node.action_sequence)}")
            best_action_sequence = best_node.action_sequence + best_rollout_sequence
            logging.info(f"Best action sequence: {best_action_sequence}")
            return best_action_sequence
        else:
            logging.info("No winning sequence found")
            return None  # Return None if no winning sequence was found

    
    def get_action_sequence(self):
        """
        Traces back the actions from this node to the root node.
        """
        sequence = []
        current_node = self
        while current_node and current_node.parent is not None:
            sequence.append(current_node.parent_action)
            current_node = current_node.parent
        return sequence[::-1]  # Reverse to get actions from root to this node


def round_action_sequence(action_sequence):
    rounded_sequence = []
    for action in action_sequence:
        rounded_action = tuple(tuple(round(coord, 1) for coord in position) for position in action)
        rounded_sequence.append(rounded_action)
    return rounded_sequence



def create_oplayer(rec1, rec2, rec3, rec4, rec5):
    offensive_players = [rec1, rec2, rec3, rec4, rec5]

    return offensive_players


def create_dplayer(cov1, cov2, cov3, cov4, cov5, cov6, cov7, cov8):
    defensive_players = [cov1, cov2, cov3, cov4, cov5, cov6, cov7, cov8]

    return defensive_players


def mcts(offplayers, defplayers):
    #create initial game state
    initial_state = GameState(offensive_players=offplayers, defensive_players=defplayers)

    #create root node for MCTS
    root_node = MonteCarloTreeSearchNode(initial_state)

    best_action_sequence = root_node.best_action()

    if best_action_sequence is not None:
        rounded_best_action_sequence = round_action_sequence(best_action_sequence)
        print(f"Best action sequence found: {rounded_best_action_sequence}")
    else:
        print("No winning sequence found")
    
    return rounded_best_action_sequence