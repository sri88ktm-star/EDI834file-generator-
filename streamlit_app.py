import streamlit as st
import io
import json
from src.parse_xlsx import parse_xlsx

def generate_834_edi(rows):
    """Formats JSON rows into X12 834 segments based on your test specs."""
    segments = []
    for row in rows:
        # INS Segment - Member Level
        # Format: INS*Subscriber Indicator*Relationship*MaintenanceType*ReasonCode*BenefitStatus
        ins = f"INS*Y*{row.get('Relationship Code', '18')}*{row.get('Maintenance Type Code', '21')}**{row.get('Benefit Status Code', 'A')}***FT**N**~"
        segments.append(ins)
        
        # REF Segments - Group & Plan Identifiers
        if row.get('Sub Group ID'):
            segments.append(f"REF*17*{row.get('Sub Group ID')}~")
        if row.get('Class Plan ID'):
            segments.append(f"REF*QQ*{row.get('Class Plan ID')}~")
            
        # NM1 Segment - Member Name
        # Format: NM1*Entity*Type*LastName*FirstName*MiddleName***IdCodeQualifier*IdCode
        nm1 = f"NM1*IL*1*{row.get('Last Name', '')}*{row.get('First Name', '')}*{row.get('Middle Name', '')}***34*{row.get('Member ID', '')}~"
        segments.append(nm1)
        
        # DMG Segment - Demographics
        # Format: DMG*D8*BirthDate*Gender
        segments.append(f"DMG*D8*{row.get('Date of Birth', '')}*{row.get('Gender', '')}~")
    
    return "\n".join(segments)

st.title("📂 EDI File Creator Test")
uploaded_file = st.file_uploader("Upload your Excel input (.xlsx)", type=['xlsx'])

if uploaded_file:
    try:
        # Read file into buffer to avoid 'File is not a zip file' error
        input_buffer = io.BytesIO(uploaded_file.read())
        result_data = parse_xlsx(input_buffer) 
        
        if result_data:
            # Generate EDI content instead of showing JSON
            edi_content = generate_834_edi(result_data)
            
            st.success("EDI 834 Generated Successfully!")
            st.text_area("X12 Preview", edi_content, height=300)
            
            st.download_button(
                label="Download .EDI File",
                data=edi_content,
                file_name="enrollment_export.edi",
                mime="text/plain"
            )
    except Exception as e:
        st.error(f"Error: {e}")
        