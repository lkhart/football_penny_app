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
    scaled_x = round((x / image_width) * field_width, 1)
    scaled_y = round((inverted_y / image_height) * field_length, 1)

    # Calculate positions
    side_line_position = scaled_x
    yard_line_position = scaled_y

    return yard_line_position, side_line_position

def get_click_coordinates():
    img_url = 'https://private-user-images.githubusercontent.com/97354054/286713241-4db94f3b-bfd4-4c92-b03d-fae25ecf83e8.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTEiLCJleHAiOjE3MDEyODYwNzQsIm5iZiI6MTcwMTI4NTc3NCwicGF0aCI6Ii85NzM1NDA1NC8yODY3MTMyNDEtNGRiOTRmM2ItYmZkNC00YzkyLWIwM2QtZmFlMjVlY2Y4M2U4LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFJV05KWUFYNENTVkVINTNBJTJGMjAyMzExMjklMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjMxMTI5VDE5MjI1NFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTRiZjgyYzgyY2RiNmVkYzViNTcyN2RjNjliYmE4NGJhNjI4YjIxYzc2M2ZkMmUzOTU3NjcwZjllZTk0MjE4MGQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JmFjdG9yX2lkPTAma2V5X2lkPTAmcmVwb19pZD0wIn0.DgFViY4qjZkTJDmVrGvIuEECROKZz20rEzK_KpzCmPg'

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
    x = round((side_line / field_width) * image_width)
    y = round((yard_line / field_length) * image_height)

    # Invert y-axis to get the correct image coordinate
    inverted_y = image_height - y

    return x, inverted_y