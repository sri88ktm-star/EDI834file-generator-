import streamlit as st
import io
import datetime
import json
from src.parse_xlsx import parse_xlsx

# 1. GENERATOR LOGIC (Internal to prevent import errors)
def generate_834_edi(rows):
    if not rows: return ""
    now = datetime.datetime.now()
    d_isa, d_gs, t_edi = now.strftime("%y%m%d"), now.strftime("%Y%m%d"), now.strftime("%H%M")
    c_num = "894135"
    f = rows[0]
    
    # Header Envelope
    segments = [
        f"ISA*00* *00* *ZZ*{f.get('Sender ID', 'SENDER01'):<15}*ZZ*{f.get('Receiver ID', 'RECEIVER01'):<15}*{d_isa}*{t_edi}*^*00501*000{c_num}*0*P*:~",
        f"GS*BE*{f.get('Sender ID')}*{f.get('Receiver ID')}*{d_gs}*{t_edi}*{c_num}*X*005010X220A1~",
        f"ST*834*{c_num}*005010X220A1~",
        f"BGN*00*0*{d_gs}*{t_edi}****4~"
    ]
    # Member Loops
    for r in rows:
        segments.append(f"INS*Y*{r.get('Relationship Code','18')}*21**A***FT**N**~")
        segments.append(f"NM1*IL*1*{r.get('Last Name')}*{r.get('First Name')}***34*{r.get('Member ID')}~")
    
    segments.append(f"SE*{len(segments)-2}*{c_num}~")
    segments.append(f"GE*1*{c_num}~")
    segments.append(f"IEA*1*000{c_num}~")
    return "\n".join(segments)

# 2. UI LOGIC (Must come after function definitions)
st.set_page_config(page_title="EDI File Creator", layout="centered")
st.title("📂 EDI File Creator Test")

# Define the variable HERE first
uploaded_file = st.file_uploader("Upload your Excel input (.xlsx)", type=['xlsx'])

if uploaded_file is not None:
    try:
        # Wrap in BytesIO to solve "File is not a zip file" error
        input_buffer = io.BytesIO(uploaded_file.read())
        data = parse_xlsx(input_buffer)
        
        if data:
            st.success("File Processed!")
            edi_out = generate_834_edi(data)
            st.text_area("X12 Preview", edi_out, height=300)
            st.download_button("Download EDI", edi_out, "output.edi")
    except Exception as e:
        st.error(f"Error: {e}")
        