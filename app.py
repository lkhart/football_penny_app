import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Initialize session state
if 'player_positions' not in st.session_state:
    st.session_state.player_positions = {'offensive': [], 'defensive': []}
if 'current_player' not in st.session_state:
    st.session_state.current_player = ('offensive', 0)

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

# Main app
def main():
    st.title('Football Defensive Strategy Optimization')

    with st.sidebar:
        num_offensive_players = st.slider('Number of Offensive Players', 2, 5, 3)
        num_defensive_players = st.slider('Number of Defensive Players', 3, 8, 5)
        
        # Check if the number of players has changed, and reset the current player
        if ('num_offensive_players' not in st.session_state or 
            'num_defensive_players' not in st.session_state or 
            st.session_state.num_offensive_players != num_offensive_players or 
            st.session_state.num_defensive_players != num_defensive_players):
            
            # Reset the current player
            st.session_state.current_player = ('offensive', 0)
            st.session_state.player_positions['offensive'] = [[] for _ in range(num_offensive_players)]
            st.session_state.player_positions['defensive'] = [[] for _ in range(num_defensive_players)]
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

    # Create the football field
    field_fig = create_football_field()

    # Plot the field and players
    for p_type in st.session_state.player_positions:
        for player_data in st.session_state.player_positions[p_type]:
            # Check if player_data is not empty
            if player_data:
                field_fig.add_trace(go.Scatter(
                    x=[player_data['x_position']],
                    y=[player_data['y_position']],
                    mode='markers',
                    marker=dict(color='red' if p_type == 'offensive' else 'blue'),
                    text=f"Speed: {player_data['speed_rating']}",  # Display speed rating on hover
                    hoverinfo='text'
                ))

    # Display the field with players
    st.plotly_chart(field_fig)

    # Display the summary table below the plot
    # Create a DataFrame for the summary table
    summary_data = {
        'Player Type': [],
        'Player Number': [],
        'Speed Rating': [],
        'Sideline Position': [],
        'Yardline Position': []
    }
    
    for p_type, players in st.session_state.player_positions.items():
        for index, player_data in enumerate(players):
            summary_data['Player Type'].append(p_type.capitalize())
            summary_data['Player Number'].append(index + 1)
            summary_data['Speed Rating'].append(player_data['speed_rating'])
            summary_data['Sideline Position'].append(player_data['x_position'])
            summary_data['Yardline Position'].append(player_data['y_position'])

    summary_df = pd.DataFrame(summary_data)
    st.table(summary_df)

if __name__ == "__main__":
    main()