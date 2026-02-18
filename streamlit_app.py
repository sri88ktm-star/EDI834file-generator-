import datetime

def format_edi_date(val):
    """Converts Excel serial dates or strings to YYYYMMDD/MMDDYYYY as needed."""
    if not val: return ""
    # Basic cleanup; for Excel serials (e.g. 45292), you may need:
    # datetime.fromordinal(datetime(1899,12,30).toordinal() + int(val)).strftime('%Y%m%d')
    return str(val).replace("-", "").replace("/", "")

def generate_834_edi(rows):
    if not rows:
        return ""
    
    # --- 1. SET UP METADATA ---
    now = datetime.datetime.now()
    date_isa = now.strftime("%y%m%d") # YYMMDD
    date_gs = now.strftime("%Y%m%d")  # YYYYMMDD
    time_edi = now.strftime("%H%M")   # HHMM
    control_num = "894135"            # Standard matching control number
    
    first = rows[0]
    sender = f"{first.get('Sender ID', 'SENDER01'):<15}"
    receiver = f"{first.get('Receiver ID', 'RECEIVER01'):<15}"

    # --- 2. HEADER ENVELOPE (ISA, GS, ST, BGN) ---
    segments = [
        f"ISA*00* *00* *ZZ*{sender}*ZZ*{receiver}*{date_isa}*{time_edi}*^*00501*000{control_num}*0*P*:~",
        f"GS*BE*{first.get('Sender ID')}*{first.get('Receiver ID')}*{date_gs}*{time_edi}*{control_num}*X*005010X220A1~",
        f"ST*834*{control_num}*005010X220A1~",
        f"BGN*00*0*{date_gs}*{time_edi}****{first.get('Transaction Set Purpose Code', '4')}~"
    ]

    # --- 3. SPONSOR & PAYER (N1) ---
    segments.append(f"REF*38*{first.get('Policy Number', 'POL12345')}~")
    segments.append(f"DTP*007*D8*{date_gs}~")
    segments.append(f"N1*P5*{first.get('Sponsor Name', 'SRI HEALTH')}*FI*{first.get('Sponsor Tax ID', '123456789')}~")
    segments.append(f"N1*IN*{first_row.get('Payer Name', 'NATIONAL PAYER')}*FI*{first_row.get('Payer ID', '987654321')}~")

    # --- 4. MEMBER LOOPS (INS, REF, NM1, PER, N3, N4, DMG, DTP, HD) ---
    for row in rows:
        rel_code = row.get('Relationship Code', '18')
        ins_ind = "Y" if rel_code == "18" else "N" # Y for Subscriber
        
        segments.append(f"INS*{ins_ind}*{rel_code}*{row.get('Maintenance Type Code', '21')}**A***FT**N**~")
        segments.append(f"REF*0F*{row.get('Member ID')}~")
        segments.append(f"REF*1L*{row.get('Group')}~")
        segments.append(f"REF*17*{row.get('Sub Group ID')}~")
        segments.append(f"REF*QQ*{row.get('Class Plan ID')}~")
        
        segments.append(f"DTP*356*D8*{format_edi_date(row.get('Eligibility Begin Date'))}~")
        segments.append(f"NM1*IL*1*{row.get('Last Name')}*{row.get('First Name')}*{row.get('Middle Name')}***34*{row.get('Member ID')}~")
        
        if row.get('Contact Name'):
            segments.append(f"PER*IP*{row.get('Contact Name')}*TE*{row.get('Phone')}*EM*{row.get('Email')}~")
            
        segments.append(f"N3*{row.get('Address 1')}*~")
        segments.append(f"N4*{row.get('City')}*{row.get('State')}*{row.get('Zip')}~")
        segments.append(f"DMG*D8*{format_edi_date(row.get('Date of Birth'))}*{row.get('Gender')}~")
        segments.append(f"DTP*348*D8*{format_edi_date(row.get('Eligibility Date'))}~")
        segments.append(f"HD*21*{row.get('Maintenance Reason Code', 'XN')}*HLT*{row.get('Plan')}*EMP~")

    # --- 5. FOOTER ENVELOPE (SE, GE, IEA) ---
    segments.append(f"SE*{len(segments) - 2}*{control_num}~") # Exclude ISA/GS
    segments.append(f"GE*1*{control_num}~")
    segments.append(f"IEA*1*000{control_num}~")

    return "\n".join(segments)
