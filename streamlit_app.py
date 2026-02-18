import streamlit as st
import json
import io  # Required to handle the file in memory
from src.parse_xlsx import parse_xlsx

st.set_page_config(page_title="EDI File Creator", layout="centered")
st.title("📂 EDI File Creator Test")

uploaded_file = st.file_uploader("Upload your Excel input (.xlsx)", type=['xlsx'])

if uploaded_file:
    with st.spinner('Parsing Excel data...'):
        try:
            # FIX: Wrap the uploaded file in BytesIO so zipfile can read it
            # This converts the upload into a "virtual file" in memory
            input_data = io.BytesIO(uploaded_file.read())
            
            # Call your actual function from src/parse_xlsx.py
            result_data = parse_xlsx(input_data) 
            
            if result_data:
                st.success("File parsed successfully!")
                st.write("### Preview of Parsed Data:")
                st.json(result_data[:2]) # Preview first 2 records

                # Convert the Python result to a string for download
                output_string = json.dumps(result_data, indent=4)
                
                st.download_button(
                    label="Download Generated EDI File",
                    data=output_string,
                    file_name="generated_output.edi",
                    mime="text/plain"
                )
            else:
                st.warning("No data found in the file.")
                
        except Exception as e:
            st.error(f"Error processing file: {e}")
            