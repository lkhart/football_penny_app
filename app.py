import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates 
# from sqlalchemy import create_engine
from urllib.parse import quote
import requests
# import pymysql
import utils
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
import by_second as ol
from PIL import Image, ImageDraw
from io import BytesIO


### Setup

# load data

test_plays_url = 'https://raw.githubusercontent.com/lkhart/football_penny_app/main/Test_Plays.csv'

test_play_data = utils.load_data_from_github(test_plays_url)

# st.write(test_play_data)

# Streamlit App

st.set_page_config(
    page_title="Penny: Football Play Analysis Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.title("Penny: Football Play Analysis Tool")

# function draw markers on the field image
def draw_positions_on_image(image_path, positions):
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        marker_size = 10
        marker_color = 'blue'

        for pos in positions:
            # Assume positions are already scaled to image dimensions
            x, y = pos
            draw.ellipse((x - marker_size, y - marker_size, x + marker_size, y + marker_size), fill=marker_color)

        return img
    
def load_image_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        return Image.open(BytesIO(response.content))
    except requests.RequestException as e:
        st.error(f"Error loading image: {e}")
        return None
    
def draw_positions_on_image(image, positions):
    draw = ImageDraw.Draw(image)
    marker_size = 10
    marker_color = 'blue'

    for pos in positions:
        # Assume positions are already scaled to image dimensions
        x, y = pos
        draw.ellipse((x - marker_size, y - marker_size, x + marker_size, y + marker_size), fill=marker_color)

    return image

def main():
    st.title("Defensive Players Position Selector")

    # Initialize session states
    if 'player_positions' not in st.session_state:
        st.session_state['player_positions'] = []

    # Define the number of players and image dimensions
    num_players = st.slider("Select number of defensive players", 1, 11, 1)
    image_width, image_height = 1140, 520

    # Image URL
    img_url = 'https://user-images.githubusercontent.com/97354054/284066828-45296866-70f9-448e-8cc7-b30e24c88490.png'  # Replace with your image URL

    image = load_image_from_url(img_url)

    if image is not None:
        # Display the image for user interaction
        # st.image(image, use_column_width=True)

        # Initialize coordinates
        x_coord, y_coord = None, None
        
        # Prompt user for each player's position
        current_player = len(st.session_state['player_positions']) + 1
        
        if current_player <= num_players:
            st.write(f"Select starting position for player {current_player}.")
            
            x_coord, y_coord = utils.get_click_coordinates()

        if x_coord is not None and y_coord is not None:
            yard_line, side_line = utils.transform_to_field_coordinates(x_coord, y_coord, image_width, image_height)
            st.write(f"You selected for player {current_player}: Yard Line={yard_line}, Side Line={side_line}")

            if st.button(f'Confirm Position for Player {current_player}'):
                st.session_state['player_positions'].append((yard_line, side_line))
        else:

            # Draw the positions on the image
            if len(st.session_state['player_positions']) == num_players:
                st.write("All player positions selected:")
                for i, position in enumerate(st.session_state['player_positions']):
                    st.write(f"Player {i+1}: {position}")
                
                # transform from yard coords to image coords
                image_positions = [utils.transform_back_to_image_coordinates(pos[0], pos[1], image_width, image_height) for pos in st.session_state['player_positions']]
                # Convert the image to RGB (to ensure compatibility with ImageDraw)
                image_rgb = image.convert("RGB")
                image_with_positions = draw_positions_on_image(image_rgb, image_positions)
                st.image(image_with_positions, use_column_width=True)

     # Now, get routes for each player
    if len(st.session_state['player_positions']) == num_players:
        # Display starting positions
        image_positions = [utils.transform_back_to_image_coordinates(pos[0], pos[1], image_width, image_height) for pos in st.session_state['player_positions']]
        image_rgb = image.convert("RGB")
        image_with_positions = draw_positions_on_image(image_rgb, image_positions)
        st.image(image_with_positions, use_column_width=True)

        # Initialize routes in session state
        if 'player_routes' not in st.session_state:
            st.session_state['player_routes'] = [[] for _ in range(num_players)]

        # Iterate through each player for route selection
        for player_index in range(num_players):
            st.write(f"Select route for player {player_index + 1}")

            # Check if route is complete for this player
            if len(st.session_state['player_routes'][player_index]) < 3:
                x_coord, y_coord = utils.get_click_coordinates()

                if x_coord is not None and y_coord is not None:
                    # Append the point to the player's route
                    st.session_state['player_routes'][player_index].append((x_coord, y_coord))

                    # Draw the route on the image
                    route_image = draw_positions_on_image(image_with_positions.copy(), st.session_state['player_routes'][player_index])
                    st.image(route_image, use_column_width=True)

            # Display the selected route
            st.write(f"Route for Player {player_index + 1}: {st.session_state['player_routes'][player_index]}")


if __name__ == "__main__":
    main()


# def main():
#     st.title("Defensive Players Position Selector")

#     # Initialize session states
#     if 'player_positions' not in st.session_state:
#         st.session_state['player_positions'] = []

#     # Define the number of players
#     num_players = st.slider("Select number of defensive players", 1, 11, 1)

#     # Define image dimensions
#     image_width, image_height = 1140, 520  

#     # Prompt user for each player's position
#     current_player = len(st.session_state['player_positions']) + 1

#     if current_player <= num_players:
#         st.write(f"Select starting position for player {current_player}.")

#         # User clicks on the image
#         x_coord, y_coord = utils.get_click_coordinates()

#         if x_coord is not None and y_coord is not None:
#             yard_line, side_line = utils.transform_to_field_coordinates(x_coord, y_coord, image_width, image_height)
#             st.write(f"You selected for player {current_player}: Yard Line={yard_line}, Side Line={side_line}")

#             if st.button(f'Confirm Position for Player {current_player}'):
#                 st.session_state['player_positions'].append((yard_line, side_line))
#     else:
#         st.write("All player positions selected:")
#         for i, position in enumerate(st.session_state['player_positions']):
#             st.write(f"Player {i+1}: {position}")

# if __name__ == "__main__":
#     main()



# User input for basic selectors
st.subheader("Basic Selections")
st.write("Using the slider inputs, set the number of Pass Catchers (offensive players) and the number of Coverage Players (defensive players) for the play.")
num_pass_catchers = st.slider("Number of Pass Catchers:", 1, 10)
num_coverage_players = st.slider("Number of Coverage Players:", 1, 10)



# configure speed and route selection for offense
st.subheader("Pass Catchers - Configure")
st.write("Input the offensive player's speed rating using the slider bar below. Then select the player's route. Repeat these steps for each offensive player.")

offensive_speeds = {}

for i in range(num_pass_catchers):
    speed = st.slider(f"Speed rating (yards per 0.1 seconds) for offensive player {i+1}:", min_value=0.5, max_value=1.0, step=0.1)
    offensive_speeds[f"Player {i+1}"] = speed

routes = {}
for i in range(num_pass_catchers):
    route = st.text_input(f"Route for receiver {i+1}:")
    routes[f"Player {i+1}"] = route


# configure speed and reaction time for defense
st.subheader("Coverage Players - Configure")
st.write("Input the defensive player's speed rating using the slider bar below. Then set the player's reaction time. Repeat these steps for each offensive player.")

defensive_speeds = {}
for i in range(num_coverage_players):
    speed = st.slider(f"Speed rating (yards per 0.1 seconds) for defensive player {i+1}:", min_value=0.5, max_value=1.0, step=0.1)
    defensive_speeds[f"Defender {i+1}"] = speed

# Weight assignment for defensive positioning
weight = st.slider("Weight for defensive player positioning:", 0, 100)

# Button to run the simulation
if st.button("Run Simulation"):
    st.write("Running the simulation... (this is a placeholder)")

# Display the results (GIF and play art form)
st.subheader("Simulation Results")
st.write("GIF result (placeholder)")
st.image("https://via.placeholder.com/300")  # Placeholder, replace with actual GIF
st.write("Play art result (placeholder)")
st.image("https://via.placeholder.com/300")  # Placeholder, replace with actual play art

# Interface for analyzing NFL play-by-play data
left_column.subheader("NFL Play-by-Play Analysis")
team = left_column.selectbox("Select NFL Team:", ["Team A", "Team B", "Team C"], index=0)  # Placeholder team names
week = left_column.selectbox("Select Week:", list(range(1, 18)))

if st.button("Fetch and Analyze Data"):
    st.write(f"Fetching data for {team} for week {week}... (this is a placeholder)")


