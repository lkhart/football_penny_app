from io import StringIO
import requests
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates 


# function to load data from GitHub
def load_data_from_github(url):
    download = requests.get(url).content
    data = pd.read_csv(StringIO(download.decode('utf-8')))
    return data


def transform_to_field_coordinates(x, y, image_width, image_height):
    # constants for football field dimensions
    field_length = 120  # includes end zones, in yards
    field_width = 53.3  # in yards

    inverted_y = image_height - y


    # Scale coordinates
    scaled_x = round((x / image_width) * field_length, 1)
    scaled_y = round((inverted_y / image_height) * field_width, 1)

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
    

def transform_back_to_image_coordinates(yard_line, side_line, image_width, image_height):
    # Constants for football field dimensions
    field_length = 120  # includes end zones, in yards
    field_width = 53.3  # in yards

    # Reverse Scale coordinates
    x = round((yard_line / field_length) * image_width)
    y = round((side_line / field_width) * image_height)

    # Invert y-axis to get the correct image coordinate
    inverted_y = image_height - y

    return x, inverted_y