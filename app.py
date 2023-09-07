import streamlit as st
import cv2
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.spatial import distance
from PIL import Image, ImageDraw
import io
import base64

# Read the HTML, CSS, and JS files
with open('website.html', 'r') as f:
    html_content = f.read()

with open('website.css', 'r') as f:
    css_content = f.read()

with open('website.js', 'r') as f:
    js_content = f.read()

# Inline the CSS and JS within the HTML
html_content_with_css_and_js = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
    {css_content}
    </style>
</head>
<body>
{html_content}
<script>
{js_content}
</script>
</body>
</html>
"""

# Display the HTML content in Streamlit
st.markdown(html_content_with_css_and_js, unsafe_allow_html=True)

def compute_edge_intensity(img, point, neighborhood_size):
    x, y = point
    x_min, x_max = max(0, x - neighborhood_size), min(img.shape[1], x + neighborhood_size)
    y_min, y_max = max(0, y - neighborhood_size), min(img.shape[0], y + neighborhood_size)
    return np.sum(img[y_min:y_max, x_min:x_max])

def get_starting_point(image_shape):
    st.sidebar.title("Starting Point Selection")
    start_x = st.sidebar.slider('Select the X coordinate', 0, image_shape[1]-1, 0)
    start_y = st.sidebar.slider('Select the Y coordinate', 0, image_shape[0]-1, 0)
    return (start_x, start_y)

uploaded_file = st.file_uploader("Choose an image...", type="jpg")
if uploaded_file is not None:
    img = Image.open(uploaded_file)
    img = np.array(img)
    st.image(img, caption='Uploaded Image.', use_column_width=True)

    desired_size = (img.shape[1]*2, img.shape[0]*2)  # Double the width and height
    img = cv2.resize(img, desired_size)

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (7,7), 1)

    st.sidebar.title("Settings")
    thresLower = st.sidebar.slider('Lower Threshold', 0, 255, 100)
    thresUpper = st.sidebar.slider('Upper Threshold', 0, 255, 150)

    img_canny = cv2.Canny(img_blur, thresLower, thresUpper)

    indices = np.where(img_canny == 255)
    endpoints = list(zip(indices[1], indices[0]))

    starting_point = get_starting_point(img.shape)

    distances = distance.cdist([starting_point], endpoints)
    closest_index = np.argmin(distances)
    starting_point = endpoints[closest_index]
    endpoints.pop(closest_index)

    spline_points = [starting_point]

    progress_bar = st.progress(0)

    distance_threshold = 10
    max_iterations_without_point_within_threshold = 10
    iterations_without_point_within_threshold = 0
    while endpoints:
        current_point = spline_points[-1]
        distances = distance.cdist([current_point], endpoints)
        closest_index = np.argmin(distances)

        if distances[0, closest_index] < distance_threshold:
            closest_point = endpoints[closest_index]
            spline_points.append(closest_point)
            endpoints.pop(closest_index)
            iterations_without_point_within_threshold = 0
        else:
            iterations_without_point_within_threshold += 1

        if iterations_without_point_within_threshold > max_iterations_without_point_within_threshold:
            closest_point = endpoints[closest_index]
            spline_points.append(closest_point)
            endpoints.pop(closest_index)
            iterations_without_point_within_threshold = 0

        progress_bar.progress(len(spline_points) / (len(endpoints) + len(spline_points)))

    spline_points = np.array(spline_points)
    tck, u = splprep([spline_points[:, 0], spline_points[:, 1]], s=1.0)
    u_new = np.linspace(u.min(), u.max(), len(spline_points))
    x_new, y_new = splev(u_new, tck)

    drawing = Image.new('RGB', (img_canny.shape[1], img_canny.shape[0]), color=(0,0,0))
    draw = ImageDraw.Draw(drawing)

    video_frames = []

    line_thickness = st.sidebar.slider('Line Thickness', 1, 10, 2)
    drawing_speed = st.sidebar.slider('Drawing Speed', 1, 100, 10)
    average_distance = np.average(distance.cdist(spline_points[:-1], spline_points[1:]))
    for i in range(1, len(x_new)):
        if i == len(x_new) - 1 and distance.euclidean((x_new[i-1], y_new[i-1]), (x_new[i], y_new[i])) > average_distance:
            break

        thickness = compute_edge_intensity(img_canny, (int(x_new[i]), int(y_new[i])), neighborhood_size=5)
        thickness = np.clip(thickness / 255.0, 1, line_thickness)

        x_coord = min(max(int(x_new[i]), 0), img.shape[1] - 1)
        y_coord = min(max(int(y_new[i]), 0), img.shape[0] - 1)

        color = tuple(map(int, img[y_coord, x_coord]))

        draw.line([(x_new[i-1], y_new[i-1]), (x_new[i], y_new[i])], fill=color, width=int(thickness))

        if i % drawing_speed == 0:  # Now uses the slider value
            bio = io.BytesIO()
            drawing.save(bio, format='PNG')
            video_frames.append(Image.open(bio))

    # Create a GIF animation
    gif_data = io.BytesIO()
    if video_frames:
        video_frames[0].save(
            gif_data,
            append_images=video_frames[1:],
            format='GIF',
            save_all=True,
            duration=100,  # Duration for each frame
            loop=0  # Loop forever
        )

        gif_data.seek(0)  # Move the pointer back to the start of the data

        # Display the GIF
        st.image(gif_data)

        # Add a download button for the GIF
        gif_data.seek(0)  # Move the pointer back to the start of the data
        st.download_button(
            label="Download GIF",
            data=gif_data,
            file_name="drawing.gif",
            mime="image/gif",
        )
    else:
        st.write("No frames were generated. Try reducing the drawing speed.")
