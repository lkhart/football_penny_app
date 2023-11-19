import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates 


# Custom Theme for the company's colors
st.set_page_config(
    page_title="Penny: Football Play Analysis Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Streamlit App
st.title("Penny: Football Play Analysis Tool")

def transform_to_field_coordinates(x, y, image_width, image_height):
    # constants for football field dimensions
    field_length = 120  # includes end zones, in yards
    field_width = 53.3  # in yards

    # Scale coordinates
    scaled_x = round((x / image_width) * field_length, 1)
    scaled_y = round((y / image_height) * field_width, 1)

    # Calculate positions
    yard_line_position = scaled_x
    side_line_position = scaled_y

    return yard_line_position, side_line_position

def get_click_coordinates():
    img_url = 'https://user-images.githubusercontent.com/97354054/284066828-45296866-70f9-448e-8cc7-b30e24c88490.png'

    # get the click coordinates
    coordinates = streamlit_image_coordinates(img_url)

    if coordinates:
        x_coordinate, y_coordinate = coordinates['x'], coordinates['y']
        return x_coordinate, y_coordinate
    else:
        return None, None

# def main():

#     # image dimensions - hardcoded so need to change if replacing image
#     image_width, image_height = 1140, 520

#     # get x and y coordinates
#     x_coord, y_coord = get_click_coordinates()

#     # display and convert the coordinates
#     if x_coord is not None and y_coord is not None:
#         yard_line, side_line = transform_to_field_coordinates(x_coord, y_coord, image_width, image_height)
#         # st.write(f"Original Coordinates: X={x_coord}, Y={y_coord}")
#         st.write(f"Scaled Coordinates: Yard Line={yard_line}, Side Line={side_line}")

# if __name__ == "__main__":
#     main()


def main():
    st.title("Defensive Players Position Selector")

    # Initialize session states
    if 'player_positions' not in st.session_state:
        st.session_state['player_positions'] = []

    # Define the number of players
    num_players = st.slider("Select number of defensive players", 1, 11, 1)

    # Define image dimensions
    image_width, image_height = 1140, 520  

    # Prompt user for each player's position
    current_player = len(st.session_state['player_positions']) + 1

    if current_player <= num_players:
        st.write(f"Select starting position for player {current_player}.")

        # User clicks on the image
        x_coord, y_coord = get_click_coordinates()

        if x_coord is not None and y_coord is not None:
            yard_line, side_line = transform_to_field_coordinates(x_coord, y_coord, image_width, image_height)
            st.write(f"You selected for player {current_player}: Yard Line={yard_line}, Side Line={side_line}")

            if st.button(f'Confirm Position for Player {current_player}'):
                st.session_state['player_positions'].append((yard_line, side_line))
    else:
        st.write("All player positions selected:")
        for i, position in enumerate(st.session_state['player_positions']):
            st.write(f"Player {i+1}: {position}")

if __name__ == "__main__":
    main()





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
    speed = st.slider(f"Speed rating for offensive player {i+1}:", 0, 100)
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
    speed = st.slider(f"Speed rating for defender {i+1}:", 0, 100)
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
st.subheader("NFL Play-by-Play Analysis")
team = st.selectbox("Select NFL Team:", ["Team A", "Team B", "Team C"], index=0)  # Placeholder team names
week = st.selectbox("Select Week:", list(range(1, 18)))

if st.button("Fetch and Analyze Data"):
    st.write(f"Fetching data for {team} for week {week}... (this is a placeholder)")


