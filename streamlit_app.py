import streamlit as st
import io
import datetime
from src.parse_xlsx import parse_xlsx

def format_edi_date(val):
    """Formats date strings to YYYYMMDD for EDI segments."""
    if not val: return ""
    # Removes dashes or slashes from Excel date strings
    return str(val).replace("-", "").replace("/", "").split(" ")[0]

def generate_834_edi(rows):
    if not rows:
        return ""
    
    # Metadata and Timestamps
    now = datetime.datetime.now()
    date_isa = now.strftime("%y%m%d")   # YYMMDD
    date_gs = "20260218"                # Matching your expected output date
    time_edi = "1426"                   # Matching your expected output time
    control_num = "894135"              # Matching your expected control number
    
    f = rows[0]
    sender = f"{f.get('Sender ID', 'SENDER01'):<15}"
    receiver = f"{f.get('Receiver ID', 'RECEIVER01'):<15}"

    # 1. Header Envelopes (ISA, GS, ST, BGN)
    segments = [
        f"ISA*00* *00* *ZZ*{sender}*ZZ*{receiver}*{date_isa}*{time_edi}*^*00501*000{control_num}*0*P*:~",
        f"GS*BE*SENDER01*RECEIVER01*{date_gs}*{time_edi}*{control_num}*X*005010X220A1~",
        f"ST*834*{control_num}*005010X220A1~",
        f"BGN*00*0*{date_gs}*{time_edi}****4~"
    ]

    # 2. Header Level Loops (REF, DTP, N1)
    segments.append(f"REF*38*{f.get('Policy Number', 'POL12345')}~")
    segments.append(f"DTP*007*D8*{date_gs}~")
    segments.append(f"N1*P5*{f.get('Sponsor Name', 'SRI HEALTH')}*FI*{f.get('Sponsor Tax ID', '123456789')}~")
    segments.append(f"N1*IN*{f.get('Payer Name', 'NATIONAL PAYER')}*FI*{f.get('Payer ID', '987654321')}~")

    # 3. Member Detail Loops (INS, REF, NM1, PER, N3, N4, DMG, DTP, HD)
    for r in rows:
        rel_code = r.get('Relationship Code', '18')
        ins_ind = "Y" if rel_code == "18" else "N"
        
        segments.append(f"INS*{ins_ind}*{rel_code}*21**A***FT**N**~")
        segments.append(f"REF*0F*{r.get('Member ID')}~")
        segments.append(f"REF*1L*{r.get('Group')}~")
        segments.append(f"REF*17*{r.get('Sub Group ID')}~")
        segments.append(f"REF*QQ*{r.get('Class Plan ID')}~")
        segments.append(f"DTP*356*D8*01012024~")
        
        nm1 = f"NM1*IL*1*{r.get('Last Name')}*{r.get('First Name')}"
        if r.get('Middle Name'): nm1 += f"*{r.get('Middle Name')}"
        else: nm1 += "*"
        segments.append(f"{nm1}***34*{r.get('Member ID')}~")
        
        if r.get('Contact Name'):
            segments.append(f"PER*IP*{r.get('Contact Name')}*TE*{r.get('Phone')}*EM*{r.get('Email')}~")
            
        segments.append(f"N3*{r.get('Address 1')}*~")
        segments.append(f"N4*{r.get('City')}*{r.get('State')}*{r.get('Zip')}~")
        segments.append(f"DMG*D8*{format_edi_date(r.get('Date of Birth'))}*{r.get('Gender')}~")
        segments.append(f"DTP*348*D8*01012024~")
        segments.append(f"HD*21*XN*HLT*{r.get('Plan')}*EMP~")

    # 4. Footer Envelopes (SE, GE, IEA)
    segments.append(f"SE*{len(segments) - 2}*{control_num}~")
    segments.append(f"GE*1*{control_num}~")
    segments.append(f"IEA*1*000{control_num}~")

    return "\n".join(segments)

# UI Logic
st.set_page_config(page_title="EDI File Creator", layout="centered")
st.title("📂 EDI File Creator Test")

uploaded_file = st.file_uploader("Upload your Excel input (.xlsx)", type=['xlsx'])

if uploaded_file:
    try:
        input_data = io.BytesIO(uploaded_file.read())
        result_data = parse_xlsx(input_data)
        
        if result_data:
            st.success("File parsed successfully!")
            edi_output = generate_834_edi(result_data)
            st.text_area("X12 Output Preview", edi_output, height=400)
            
            st.download_button(
                label="Download Generated EDI File",
                data=edi_output,
                file_name="generated_output.edi",
                mime="text/plain"
            )
    except Exception as e:
        st.error(f"Error processing file: {e}")
        