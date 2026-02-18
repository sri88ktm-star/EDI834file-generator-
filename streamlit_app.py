import streamlit as st
import json
import io
from src.parse_xlsx import parse_xlsx

st.set_page_config(page_title="EDI File Creator", layout="centered")
st.title("📂 EDI File Creator Test")

# File Uploader
uploaded_file = st.file_uploader("Upload your Excel input (.xlsx)", type=['xlsx'])

if uploaded_file is not None:
    with st.spinner('Parsing Excel data...'):
        try:
            # Re-reading the bytes to ensure a fresh buffer for the parser
            file_bytes = uploaded_file.getvalue()
            input_buffer = io.BytesIO(file_bytes)
            
            # Call your function with the buffer
            result_data = parse_xlsx(input_buffer) 
            
            if result_data:
                st.success("File parsed successfully!")
                
                # Preview top 2 entries
                st.write("### Data Preview:")
                st.json(result_data[:2])

                # Convert Python object to JSON string for download
                output_string = json.dumps(result_data, indent=4)
                
                st.download_button(
                    label="Download Generated EDI File",
                    data=output_string,
                    file_name="generated_output.edi",
                    mime="text/plain"
                )
            else:
                st.warning("The parser returned no data. Check your Excel formatting.")
                
        except Exception as e:
            # This will show you exactly where the parser is failing
            st.error(f"Error processing file: {e}")
            