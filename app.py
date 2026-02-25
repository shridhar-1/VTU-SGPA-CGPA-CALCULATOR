from flask import Flask, render_template, request
import pdfplumber
import re
import os

app = Flask(__name__)

# 💥 THE UNBREAKABLE DICTIONARY: Explicitly written, zero loops, zero crashes!
CREDIT_MAP = {
    # --- COMMON 1ST & 2ND YEAR SUBJECTS ---
    "BCEDK103": 3, "BENGK106": 1, "BICOK107": 1, "BIDTK158": 1,
    "BBEE203": 3, "BPWSK206": 1, "BKSKK207": 1, "BSFHK258": 1,
    "BMATE301": 4, "BKSKK307": 1, "BNSAK358": 1, "BSCK306B": 1,
    "BUHVK406": 1, "BKSKK407": 1, "BBOK408": 1, "BAECK409": 1,
    "BKSKK507": 1, "BAECK508": 1, "BAECK608": 1,

    # --- 1st Year Stream specific (Math, Physics, Chem) ---
    "BMATE101": 4, "BPHYE102": 4, "BCHEE102": 4, "BMATE201": 4, "BPHYE202": 4, "BCHEE202": 4, 
    "BMATS101": 4, "BPHYS102": 4, "BCHES102": 4, "BMATS201": 4, "BPHYS202": 4, "BCHES202": 4, 
    "BMATM101": 4, "BPHYM102": 4, "BCHEM102": 4, "BMATM201": 4, "BPHYM202": 4, "BCHEM202": 4, 
    "BMATV101": 4, "BPHYV102": 4, "BCHEV102": 4, "BMATV201": 4, "BPHYV202": 4, "BCHEV202": 4, 

    # --- 1st Year Intro Subjects (A to J) ---
    "BESCK104A": 3, "BESCK104B": 3, "BESCK104C": 3, "BESCK104D": 3, "BESCK104E": 3,
    "BETCK105A": 3, "BETCK105B": 3, "BETCK105C": 3, "BETCK105D": 3, "BETCK105E": 3, "BETCK105J": 3,
    "BESCK204A": 3, "BESCK204B": 3, "BESCK204C": 3, "BESCK204D": 3, "BESCK204E": 3,
    "BPLCK205A": 3, "BPLCK205B": 3, "BPLCK205C": 3, "BPLCK205D": 3, "BPLCK205E": 3,

    # --- ELECTRONICS & COMMUNICATION (EC) ---
    "BEC302": 4, "BEC303": 3, "BEC304": 3, "BECL305": 1,
    "BEC401": 3, "BEC402": 4, "BEC403": 3, "BEC404": 3, "BECL405": 1,
    "BEC501": 3, "BEC502": 4, "BEC503": 3, "BEC504": 3, "BECL505": 1,
    "BEC506A": 3, "BEC506B": 3, "BEC506C": 3, "BEC506D": 3,
    "BEC601": 3, "BEC602": 4, "BEC603": 3, "BECL604": 1,
    "BEC605A": 3, "BEC605B": 3, "BEC605C": 3, "BEC605D": 3,
    "BEC606A": 3, "BEC606B": 3, "BEC606C": 3, "BEC606D": 3,
    "BEC701": 3, "BEC702": 3, "BEC703": 3,
    "BEC704A": 3, "BEC704B": 3, "BEC704C": 3, "BEC704D": 3,
    "BEC705A": 3, "BEC705B": 3, "BEC705C": 3, "BEC705D": 3,
    "BEC801": 1, "BEC802": 1, "BEC803": 8, "BEC804": 1,

    # --- COMPUTER SCIENCE (CS) ---
    "BCS302": 4, "BCS303": 3, "BCS304": 3, "BCSL305": 1,
    "BCS401": 3, "BCS402": 4, "BCS403": 3, "BCS404": 3, "BCSL405": 1,
    "BCS501": 3, "BCS502": 4, "BCS503": 3, "BCS504": 3, "BCSL505": 1,
    "BCS506A": 3, "BCS506B": 3, "BCS506C": 3, "BCS506D": 3,
    "BCS601": 3, "BCS602": 4, "BCS603": 3, "BCSL604": 1,
    "BCS605A": 3, "BCS605B": 3, "BCS605C": 3, "BCS605D": 3,
    "BCS606A": 3, "BCS606B": 3, "BCS606C": 3, "BCS606D": 3,
    "BCS701": 3, "BCS702": 3, "BCS703": 3,
    "BCS704A": 3, "BCS704B": 3, "BCS704C": 3, "BCS704D": 3,
    "BCS705A": 3, "BCS705B": 3, "BCS705C": 3, "BCS705D": 3,
    "BCS801": 1, "BCS802": 1, "BCS803": 8, "BCS804": 1,

    # --- INFORMATION SCIENCE (IS) ---
    "BIS302": 4, "BIS303": 3, "BIS304": 3, "BISL305": 1,
    "BIS401": 3, "BIS402": 4, "BIS403": 3, "BIS404": 3, "BISL405": 1,
    "BIS501": 3, "BIS502": 4, "BIS503": 3, "BIS504": 3, "BISL505": 1,
    "BIS506A": 3, "BIS506B": 3, "BIS506C": 3, "BIS506D": 3,
    "BIS601": 3, "BIS602": 4, "BIS603": 3, "BISL604": 1,
    "BIS605A": 3, "BIS605B": 3, "BIS605C": 3, "BIS605D": 3,
    "BIS606A": 3, "BIS606B": 3, "BIS606C": 3, "BIS606D": 3,
    "BIS701": 3, "BIS702": 3, "BIS703": 3,
    "BIS704A": 3, "BIS704B": 3, "BIS704C": 3, "BIS704D": 3,
    "BIS705A": 3, "BIS705B": 3, "BIS705C": 3, "BIS705D": 3,
    "BIS801": 1, "BIS802": 1, "BIS803": 8, "BIS804": 1,

    # --- ELECTRICAL & ELECTRONICS (EE) ---
    "BEE302": 4, "BEE303": 3, "BEE304": 3, "BEEL305": 1,
    "BEE401": 3, "BEE402": 4, "BEE403": 3, "BEE404": 3, "BEEL405": 1,
    "BEE501": 3, "BEE502": 4, "BEE503": 3, "BEE504": 3, "BEEL505": 1,
    "BEE506A": 3, "BEE506B": 3, "BEE506C": 3, "BEE506D": 3,
    "BEE601": 3, "BEE602": 4, "BEE603": 3, "BEEL604": 1,
    "BEE605A": 3, "BEE605B": 3, "BEE605C": 3, "BEE605D": 3,
    "BEE606A": 3, "BEE606B": 3, "BEE606C": 3, "BEE606D": 3,
    "BEE701": 3, "BEE702": 3, "BEE703": 3,
    "BEE704A": 3, "BEE704B": 3, "BEE704C": 3, "BEE704D": 3,
    "BEE705A": 3, "BEE705B": 3, "BEE705C": 3, "BEE705D": 3,
    "BEE801": 1, "BEE802": 1, "BEE803": 8, "BEE804": 1,

    # --- MECHANICAL (ME) ---
    "BME302": 4, "BME303": 3, "BME304": 3, "BMEL305": 1,
    "BME401": 3, "BME402": 4, "BME403": 3, "BME404": 3, "BMEL405": 1,
    "BME501": 3, "BME502": 4, "BME503": 3, "BME504": 3, "BMEL505": 1,
    "BME506A": 3, "BME506B": 3, "BME506C": 3, "BME506D": 3,
    "BME601": 3, "BME602": 4, "BME603": 3, "BMEL604": 1,
    "BME605A": 3, "BME605B": 3, "BME605C": 3, "BME605D": 3,
    "BME606A": 3, "BME606B": 3, "BME606C": 3, "BME606D": 3,
    "BME701": 3, "BME702": 3, "BME703": 3,
    "BME704A": 3, "BME704B": 3, "BME704C": 3, "BME704D": 3,
    "BME705A": 3, "BME705B": 3, "BME705C": 3, "BME705D": 3,
    "BME801": 1, "BME802": 1, "BME803": 8, "BME804": 1,

    # --- CIVIL (CV) ---
    "BCV302": 4, "BCV303": 3, "BCV304": 3, "BCVL305": 1,
    "BCV401": 3, "BCV402": 4, "BCV403": 3, "BCV404": 3, "BCVL405": 1,
    "BCV501": 3, "BCV502": 4, "BCV503": 3, "BCV504": 3, "BCVL505": 1,
    "BCV506A": 3, "BCV506B": 3, "BCV506C": 3, "BCV506D": 3,
    "BCV601": 3, "BCV602": 4, "BCV603": 3, "BCVL604": 1,
    "BCV605A": 3, "BCV605B": 3, "BCV605C": 3, "BCV605D": 3,
    "BCV606A": 3, "BCV606B": 3, "BCV606C": 3, "BCV606D": 3,
    "BCV701": 3, "BCV702": 3, "BCV703": 3,
    "BCV704A": 3, "BCV704B": 3, "BCV704C": 3, "BCV704D": 3,
    "BCV705A": 3, "BCV705B": 3, "BCV705C": 3, "BCV705D": 3,
    "BCV801": 1, "BCV802": 1, "BCV803": 8, "BCV804": 1
}

def calculate_vtu_grade(marks, p_f):
    if p_f == 'F': return 'F', 0
    if marks >= 90: return 'O', 10
    elif marks >= 80: return 'A+', 9
    elif marks >= 70: return 'A', 8
    elif marks >= 60: return 'B+', 7
    elif marks >= 55: return 'B', 6
    elif marks >= 50: return 'C', 5
    elif marks >= 40: return 'P', 4
    else: return 'F', 0

def process_pdf(files):
    best_subjects = {}
    master_usn = None
    
    for file in files:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True) or ""
                
                # USN Security Lock
                usn_match = re.search(r'\b[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}\b', text.upper())
                if usn_match:
                    found_usn = usn_match.group(0)
                    if master_usn is None: 
                        master_usn = found_usn
                    elif found_usn != master_usn:
                        return {"error": "Security Alert: Multiple USNs detected!"}
                
                lines = text.split('\n')
                for line in lines:
                    
                    # 💥 THE HYBRID RADAR: Finds ANY VTU Code, including Open Electives!
                    code_match = re.search(r'\bB[A-Z]{2,4}\d{3}[A-Z]?\b', line)
                    
                    if code_match:
                        code = code_match.group(0)
                        
                        # 💥 THE SMART FALLBACK: If not in dictionary, guess safely!
                        if code in CREDIT_MAP:
                            credits = CREDIT_MAP[code]
                        else:
                            if "786" in code: credits = 2 # Project Phase II
                            elif "803" in code: credits = 8 # Major Project
                            elif re.search(r'(05|06|07|08|09|L)[A-Z]?$', code): credits = 1
                            else: credits = 3 # Default for Open/Professional Electives
                        
                        # Extract ALL numbers on the line ignoring missing P/F letters
                        numbers = [int(n) for n in re.findall(r'\b\d{1,3}\b', line)]
                        valid_marks = [n for n in numbers if n <= 200] # Safe limit
                        
                        if valid_marks:
                            # VTU Format is usually: [Internal, External, Total]
                            if len(valid_marks) >= 3:
                                marks = valid_marks[-1] # Total is the last number
                            elif len(valid_marks) == 2:
                                marks = valid_marks[0] + valid_marks[1] # Sum Int + Ext
                            else:
                                marks = valid_marks[0]
                                
                            # SCALING FIX: Subjects like BEC786 are out of 200 marks!
                            percentage = marks
                            if ("786" in code or "803" in code) or marks > 100:
                                percentage = (marks / 200) * 100 if marks <= 200 else 100
                            
                            p_f = 'F' if re.search(r'\b(F|FAIL)\b', line.upper()) or percentage < 40 else 'P'
                            
                            grade_letter, gp = calculate_vtu_grade(percentage, p_f)
                            
                            sem_match = re.search(r'\d', code)
                            sem = int(sem_match.group()) if sem_match else 0
                            
                            if code not in best_subjects or marks > best_subjects[code].get("raw_marks", 0):
                                best_subjects[code] = {
                                    "code": code, "marks": marks, "raw_marks": marks,
                                    "grade": grade_letter, "gp": gp, 
                                    "credits": credits, "sem": sem
                                }

    if not best_subjects: 
        return {"error": "Could not extract marks. Make sure it is a valid PDF."}
    
    # Math Engine
    sem_dict = {}
    total_credits = 0
    total_earned = 0
    
    for code, data in best_subjects.items():
        s = data["sem"]
        if s not in sem_dict: 
            sem_dict[s] = {"credits": 0, "earned": 0, "subjects": []}
        
        sem_dict[s]["credits"] += data["credits"]
        sem_dict[s]["earned"] += (data["gp"] * data["credits"])
        sem_dict[s]["subjects"].append({
            "code": code, "marks": data["marks"], 
            "grade": data["grade"], "credits": data["credits"]
        })
        
        total_credits += data["credits"]
        total_earned += (data["gp"] * data["credits"])

    semesters_data = []
    for s in sorted(sem_dict.keys()):
        sgpa = round(sem_dict[s]["earned"] / sem_dict[s]["credits"], 2) if sem_dict[s]["credits"] > 0 else 0
        semesters_data.append({
            "semester": s, "sgpa": sgpa, 
            "credits": sem_dict[s]["credits"], "subjects": sem_dict[s]["subjects"]
        })
        
    cgpa = round(total_earned / total_credits, 2) if total_credits > 0 else 0
    return {"cgpa": cgpa, "semesters": semesters_data}
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'result_pdfs' not in request.files:
        return "Error: No files uploaded", 400
    
    files = request.files.getlist('result_pdfs')
    if not files or files[0].filename == '':
        return "Error: No selected files", 400

    result_data = process_pdf(files)
    
    if "error" in result_data:
        return result_data["error"], 400

    return render_template('result.html', data=result_data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


