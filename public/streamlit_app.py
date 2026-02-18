import sys
import os
import json
import streamlit as st

# 1. FIX THE PATH: Look one level up to find the 'src' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. IMPORT YOUR REAL FUNCTION
from src.parse_xlsx import parse_xlsx

st.set_page_config(page_title="EDI File Creator", layout="centered")
st.title("📂 EDI File Creator Test")

# 1. File Upload
uploaded_file = st.file_uploader("Upload your Excel input (.xlsx)", type=['xlsx'])

if uploaded_file:
    with st.spinner('Parsing Excel data...'):
        try:
            # your function needs a file path or file-like object
            # Streamlit's 'uploaded_file' works like a file path here
            result_data = parse_xlsx(uploaded_file) 
            
            if result_data:
                st.success("File parsed successfully!")
                
                # Show a preview of the JSON data
                st.write("### Preview of Parsed Data:")
                st.json(result_data[:2]) # Show first 2 records

                # 3. DOWNLOAD as JSON (or your EDI format)
                # Convert list to string for the download button
                json_string = json.dumps(result_data, indent=4)
                
                st.download_button(
                    label="Download Parsed JSON",
                    data=json_string,
                    file_name="parsed_data.json",
                    mime="application/json"
                )
            else:
                st.warning("The file was parsed but no data was found.")
                
        except Exception as e:
            st.error(f"Error processing file: {e}")
            