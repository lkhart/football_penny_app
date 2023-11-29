import streamlit as st
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
import pandas as pd
import plotly.graph_objects as go
from by_second import OffensivePlayer, DefensivePlayer, GameState, find_best_path_bfs


# Initialize session state
if 'player_positions' not in st.session_state:
    st.session_state.player_positions = {'offensive': [], 'defensive': []}
if 'current_player' not in st.session_state:
    st.session_state.current_player = ('offensive', 0)
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'input'

allowable_area2 = Polygon([(-27,0), (27,0), (27,100), (-27,100)])

# Function to create a football field figure
def create_football_field():
    field_fig = go.Figure()

    # Draw the outline of the field
    field_fig.add_shape(type="rect", x0=-27, y0=0, x1=27, y1=100, line=dict(color="green"))

    # Add yard lines and other field markings as necessary
    for i in range(0, 101, 10):
        field_fig.add_shape(type="line", x0=-27, y0=i, x1=27, y1=i, line=dict(color="white", width=2))

    # Set the axes ranges
    field_fig.update_xaxes(range=[-27, 27], showgrid=False)
    field_fig.update_yaxes(range=[0, 100], showgrid=False)

    # Remove axis ticks and labels
    field_fig.update_xaxes(tickvals=[])
    field_fig.update_yaxes(tickvals=[])

    # Set the figure's layout
    field_fig.update_layout(width=300, height=600, clickmode='event+select')
    
    return field_fig

# Function to add route point input sliders in the sidebar
def add_route_point_inputs(num_offensive_players):
    route_points = {}
    for i in range(num_offensive_players):
        st.sidebar.subheader(f'Offensive Player {i+1} Route Points')
        num_points = st.sidebar.slider(f'Number of Route Points for Player {i+1}', 2, 4, 2, key=f'num_points_{i}')
        route_points[i] = []
        for j in range(num_points):
            x = st.sidebar.slider(f'Player {i+1} Point {j+1} X', -27, 27, 0, key=f'x_{i}_{j}')
            y = st.sidebar.slider(f'Player {i+1} Point {j+1} Y', 0, 100, 50, key=f'y_{i}_{j}')
            route_points[i].append((x, y))
    return route_points

# Function to plot the football field with player positions
def create_and_plot_field(route_points=None):
    field_fig = create_football_field()
    for p_type in st.session_state.player_positions:
        for player_data in st.session_state.player_positions[p_type]:
            if player_data:
                field_fig.add_trace(go.Scatter(
                    x=[player_data['x_position']],
                    y=[player_data['y_position']],
                    mode='markers',
                    marker=dict(color='red' if p_type == 'offensive' else 'blue'),
                    text=f"Speed: {player_data['speed_rating']}",
                    hoverinfo='text'
                ))

    # Plot the route points
    if route_points:
        for player_id, points in route_points.items():
            if points:
                # Add route points as yellow hollow circles
                x_vals, y_vals = zip(*points)
                field_fig.add_trace(go.Scatter(
                    x=x_vals, y=y_vals, mode='markers+lines',
                    marker=dict(color='yellow', size=10, line=dict(color='yellow', width=2)),
                    line=dict(color='yellow', width=2),
                    name=f'Player {player_id+1} Route'
                ))

    return field_fig

# Function to update the offensive players' data with route points
def update_offensive_players_with_routes(route_points):
    for player_id, points in route_points.items():
        if player_id < len(st.session_state.player_positions['offensive']):
            st.session_state.player_positions['offensive'][player_id]['route_points'] = points


# Function to create the summary table
def create_summary_table():
    summary_data = {
        'Player Type': [],
        'Player Number': [],
        'Speed Rating': [],
        'Sideline Position': [],
        'Yardline Position': []
    }
    for p_type, players in st.session_state.player_positions.items():
        for index, player_data in enumerate(players):
            if isinstance(player_data, dict) and player_data:
                summary_data['Player Type'].append(p_type.capitalize())
                summary_data['Player Number'].append(index + 1)
                summary_data['Speed Rating'].append(player_data['speed_rating'])
                summary_data['Sideline Position'].append(player_data['x_position'])
                summary_data['Yardline Position'].append(player_data['y_position'])
    return pd.DataFrame(summary_data)

def format_offensive_player_data():
    formatted_data = {}
    for player_id, player_data in enumerate(st.session_state.player_positions['offensive']):
        if player_data:
            # Combine starting position with route points
            all_points = [tuple(player_data['x_position'], player_data['y_position'])] + player_data.get('route_points', [])
            formatted_data[f'opl{player_id+1}'] = all_points
    return formatted_data

def format_and_create_offensive_players():
    offensive_players = []
    for player_id, player_data in enumerate(st.session_state.player_positions['offensive']):
        if player_data:
            all_points = [(player_data['x_position'], player_data['y_position'])] + player_data.get('route_points', [])
            speed = player_data['speed_rating']
            offensive_player = OffensivePlayer(all_points, speed)
            offensive_players.append(offensive_player)
    return offensive_players

def plot_players_at_time_newversion(t, receivers, best_actions):
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

    return fig

# Main app
def main():
    st.title('Football Defensive Strategy Optimization')

    if st.session_state.current_page == 'input':
        with st.sidebar:
            num_offensive_players = st.slider('Number of Offensive Players', 2, 5, 3)
            num_defensive_players = st.slider('Number of Defensive Players', 3, 8, 5)
        
            # Sidebar input logic
            # Check if the number of players has changed, and reset the current player
            if ('num_offensive_players' not in st.session_state or 
                'num_defensive_players' not in st.session_state or 
                st.session_state.num_offensive_players != num_offensive_players or 
                st.session_state.num_defensive_players != num_defensive_players):
    
                # Reset the current player
                st.session_state.current_player = ('offensive', 0)
                st.session_state.player_positions['offensive'] = [{} for _ in range(num_offensive_players)]
                st.session_state.player_positions['defensive'] = [{} for _ in range(num_defensive_players)]
                st.session_state.num_offensive_players = num_offensive_players
                st.session_state.num_defensive_players = num_defensive_players
       
        # Sliders for player positions now in the sidebar
            st.write("Position and Speed of the Player:")
            x_position = st.slider('X Position (Left -> Right)', -27, 27, 0)
            y_position = st.slider('Y Position (End Zone -> End Zone)', 0, 100, 50)
            speed_rating = st.slider('Speed Rating', 5, 10, 7)  # Slider for speed rating

            # Button to add player position and advance to the next player
            player_type, player_index = st.session_state.current_player
            player_number = player_index + 1  # Player index is 0-based, so add 1 for the display
            button_label = f"Place {player_type.capitalize()} Player {player_number}"

            # Button to add player position and advance to the next player
            if st.button(button_label):
                # Update the player_positions with the new speed rating
                # Ensure that the list for the current player type is initialized
                if len(st.session_state.player_positions[player_type]) <= player_index:
                    st.session_state.player_positions[player_type].append({})

                st.session_state.player_positions[player_type][player_index] = {
                    'x_position': x_position,
                    'y_position': y_position,
                    'speed_rating': speed_rating
                }

    
                # Logic to advance to the next player
                if player_type == 'offensive' and player_index < num_offensive_players - 1:
                    st.session_state.current_player = (player_type, player_index + 1)
                elif player_type == 'offensive':
                    st.session_state.current_player = ('defensive', 0)
                elif player_index < num_defensive_players - 1:
                    st.session_state.current_player = (player_type, player_index + 1)
                else:
                    # Reset for next round or end the input phase
                    st.session_state.current_player = ('offensive', 0)

        # Initialize player positions lists when number of players changes
        if ('init' not in st.session_state or 
            st.session_state.num_offensive_players != num_offensive_players or 
            st.session_state.num_defensive_players != num_defensive_players):
            st.session_state.player_positions['offensive'] = [[] for _ in range(num_offensive_players)]
            st.session_state.player_positions['defensive'] = [[] for _ in range(num_defensive_players)]
            st.session_state.current_player = ('offensive', 0)
            st.session_state.num_offensive_players = num_offensive_players
            st.session_state.num_defensive_players = num_defensive_players
            st.session_state.init = True

        # Plot the field and table
        field_fig = create_and_plot_field()
        st.plotly_chart(field_fig)
        summary_df = create_summary_table()
        st.table(summary_df)

        if st.button("Next Step"):
            st.session_state.current_page = 'next_step'

    elif st.session_state.current_page == 'next_step':
        with st.sidebar:
            if st.button("Submit"):
                st.session_state.submit = True

                offensive_players = format_and_create_offensive_players()

                defensive_players = []

                for player_data in st.session_state.player_positions['defensive']:
                    def_player = DefensivePlayer((player_data['x_position'], player_data['y_position']), player_data['speed_rating'], allowable_area2)
                    defensive_players.append(def_player)

                initial_state = GameState(offensive_players=offensive_players, defensive_players=defensive_players)
                st.session_state.best_actions = find_best_path_bfs(initial_state)
                



        # Display the same field and table on the next step page
        field_fig = create_and_plot_field()
        st.plotly_chart(field_fig)
        summary_df = create_summary_table()
        st.table(summary_df)

        # Get the number of offensive players from the session state
        num_offensive_players = st.session_state.num_offensive_players

        # Add route point input sliders in the sidebar
        route_points = add_route_point_inputs(num_offensive_players)

        # Update the offensive players' data with the route points
        update_offensive_players_with_routes(route_points)

        # Display the field with the players and their routes
        field_fig = create_and_plot_field(route_points)
        st.plotly_chart(field_fig)


        # Display the best action sequence on the main page
        if 'best_actions' in st.session_state and st.session_state.submit:
            st.write("Best action sequence:")
            st.write(st.session_state.best_actions)

            for t in range(len(st.session_state.best_actions) ):  # +1 to include initial position at t=0
                fig = plot_players_at_time_newversion(t, offensive_players, st.session_state.best_actions)
                st.pyplot(fig)



    

if __name__ == "__main__":
    main()
