import streamlit as st
import io
import datetime
from src.parse_xlsx import parse_xlsx

# --- 1. THE GENERATOR LOGIC ---
def format_edi_date(val):
    if not val: return ""
    return str(val).replace("-", "").replace("/", "")

def generate_834_edi(rows):
    if not rows: return ""
    now = datetime.datetime.now()
    date_isa, date_gs, time_edi = now.strftime("%y%m%d"), now.strftime("%Y%m%d"), now.strftime("%H%M")
    control_num = "894135"
    first = rows[0]
    
    segments = [
        f"ISA*00* *00* *ZZ*{first.get('Sender ID', 'SENDER01'):<15}*ZZ*{first.get('Receiver ID', 'RECEIVER01'):<15}*{date_isa}*{time_edi}*^*00501*000{control_num}*0*P*:~",
        f"GS*BE*{first.get('Sender ID')}*{first.get('Receiver ID')}*{date_gs}*{time_edi}*{control_num}*X*005010X220A1~",
        f"ST*834*{control_num}*005010X220A1~",
        f"BGN*00*0*{date_gs}*{time_edi}****{first.get('Transaction Set Purpose Code', '4')}~"
    ]

    for row in rows:
        rel = row.get('Relationship Code', '18')
        segments.append(f"INS*{'Y' if rel == '18' else 'N'}*{rel}*21**A***FT**N**~")
        segments.append(f"REF*0F*{row.get('Member ID')}~")
        segments.append(f"NM1*IL*1*{row.get('Last Name')}*{row.get('First Name')}***34*{row.get('Member ID')}~")
        segments.append(f"DMG*D8*{format_edi_date(row.get('Date of Birth'))}*{row.get('Gender')}~")

    segments.append(f"SE*{len(segments)-2}*{control_num}~")
    segments.append(f"GE*1*{control_num}~")
    segments.append(f"IEA*1*000{control_num}~")
    return "\n".join(segments)

# --- 2. THE UI LOGIC ---
st.set_page_config(page_title="EDI File Creator", layout="centered")
st.title("📂 EDI File Creator Test")

uploaded_file = st.file_uploader("Upload your Excel input (.xlsx)", type=['xlsx'])

if uploaded_file is not None:
    try:
        # Wrap in BytesIO to solve "File is not a zip file" error
        input_buffer = io.BytesIO(uploaded_file.read())
        data = parse_xlsx(input_buffer)
        
        if data:
            st.success("Excel data parsed successfully!")
            edi_content = generate_834_edi(data)
            
            st.text_area("X12 Preview", edi_content, height=300)
            st.download_button("Download .EDI File", edi_content, "output.edi", "text/plain")
    except Exception as e:
        st.error(f"Error: {e}")
        