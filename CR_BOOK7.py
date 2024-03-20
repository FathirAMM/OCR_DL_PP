import streamlit as st
from paddleocr import PaddleOCR
from PIL import Image
from fuzzywuzzy import fuzz
import numpy as np

st.set_page_config(
    page_icon="📄👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize OCR
ocr = PaddleOCR(lang='en', use_gpu=False)

# Define OCR logic to extract key-value pairs
def extract_key_value(ocr_results, key_name, line_param, value_index, fuzz_score_threshold=80, threshold=10):
    mid_height_results = []
    for coordinates, (text, _) in ocr_results:
        mid_height = (coordinates[0][1] + coordinates[3][1]) / 2
        mid_height_results.append(((coordinates[0], coordinates[3]), (text, _), mid_height))
    sorted_results = sorted(mid_height_results, key=lambda x: x[2])
    key_match = None
    for (_, _), (text, _), mid_height in sorted_results:
        if fuzz.partial_ratio(key_name.replace(" ", ""), text) >= fuzz_score_threshold:
            key_match = text
            break

    if key_match is None:
        return None

    key_mid_height = None

    for (_, _), (text, _), mid_height in sorted_results:
        if text == key_match:
            key_mid_height = mid_height
            break

    if key_mid_height is None:
        return None

    values = []

    for (_, _), (text, _), mid_height in sorted_results:
        if line_param == 'same_line' and abs(mid_height - key_mid_height) <= threshold:
            values.append(text)

        elif line_param == 'next_line' and mid_height > key_mid_height + threshold:
            values.append(text)

    if 0 <= value_index < len(values):
        return values[value_index]
    else:
        return None

# Define function to extract details from image using OCR
def extract_details_from_image(image):
    image_array = np.array(image)  # Convert to NumPy array
    result = ocr.ocr(image_array, rec=True)
    ocr_results = result[0] 

    # Define key-value pairs
    key_value_pairs = [
        ("Registration No.", "next_line", 0),
        ("Chassis No.", "next_line", 1),
        ("Current Owner/Address/ID.No.", "next_line", [0, 1]),
        ("Conditions/Special Notes", "next_line", 0),
        ("Absolute Owner", "next_line", [0, 1, 2]),
        ("Engine No", "next_line", 0),
        ("Cylinder Capacity (cc)", "next_line", 1),
        ("Class of Vehicle", "next_line", 0),
        ("Taxation Class", "next_line", 1),
        ("Status when Registered", "next_line", 0),
        ("Make", "next_line", 0),
        #("Country of Origin", "next_line", 1),
        ("Model", "next_line", 1),
        ("Wheel Base", "next_line", 0),
        ("Type of Body", "next_line", 0)
    ]

    extracted_details = {}

    # Iterate over key-value pairs and extract details
    for key_name, value_in, value_at in key_value_pairs:
        if isinstance(value_at, list):  # If value_at is a list, iterate over each value_at position
            details = []
            for pos in value_at:
                result = extract_key_value(ocr_results, key_name, value_in, pos)
                details.append(result)
            extracted_details[key_name] = details
        else:
            result = extract_key_value(ocr_results, key_name, value_in, value_at)
            extracted_details[key_name] = result

    return extracted_details

# Streamlit interface
st.title("Vehicle Registration Information extractor 🚗📋")
col1, col2 = st.columns([2, 3])

with col1:
    st.write("Upload an image of a vehicle CR book : ")
    uploaded_image = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

    if uploaded_image is not None:
        image = Image.open(uploaded_image)
        st.image(image, caption='Uploaded Image', use_column_width=True)

with col2:
    st.write("Extracted Details")
    form = st.form(key='extracted_details_form')

    labels = [
        "Registration No.",
        "Chassis No.",
        "Current Owner/Address/ID.No.",
        "Conditions/Special Notes",
        "Absolute Owner",
        "Engine No",
        "Cylinder Capacity (cc)",
        "Class of Vehicle",
        "Taxation Class",
        "Status when Registered",
        "Make",
        "Country of Origin",
        "Model",
        "Wheel Base",
        "Type of Body"
    ]

    # Use session state to store default values
    if 'field_values' not in st.session_state:
        st.session_state['field_values'] = {label: '' for label in labels}

    # Create fields in the form
    for label in labels:
        st.session_state['field_values'][label] = form.text_input(label, st.session_state['field_values'][label])

    submit_button = form.form_submit_button('Submit')

# Image Processing Logic
if uploaded_image is not None:
    with st.spinner("Processing image..."):  # Add a loading indicator
        image = Image.open(uploaded_image)
        extracted_details = extract_details_from_image(image)
        print("Extracted Details:", extracted_details)

        # Update session state with extracted values
        for label, value in extracted_details.items():
            if isinstance(value, list):
                st.session_state['field_values'][label] = '\n'.join(value) if value else ''
            else:
                st.session_state['field_values'][label] = value if value else ''

        st.experimental_rerun()  # Force a re-render to update the form




