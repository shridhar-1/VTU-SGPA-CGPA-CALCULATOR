from flask import Flask, render_template, request
import pdfplumber
import re
import os

app = Flask(__name__)

# 💥 The Bulletproof Dictionary: 100% Accurate for ECE!
# Add 5th to 8th sem here later by just following the 
# Master VTU Credit Dictionary (1st to 8th Sem ECE - 2022 Scheme)
CREDIT_MAP = {
    # 1st Semester
    "BMATE101": 4, "BCHEE102": 4, "BCEDK103": 3, "BENGK106": 1,
    "BICOK107": 1, "BIDTK158": 1, "BESCK104E": 3, "BETCK105J": 3,
    
    # 2nd Semester
    "BMATE201": 4, "BPHYE202": 4, "BBEE203": 3, "BPWSK206": 1,
    "BKSKK207": 1, "BSFHK258": 1, "BPLCK205B": 3, "BESCK204B": 3,
    
    # 3rd Semester ECE
    "BMATE301": 4, "BEC302": 4, "BEC303": 3, "BEC304": 3, "BECL305": 1,
    "BSCK306B": 1, "BKSKK307": 1, "BNSAK358": 1,
    
    # 4th Semester ECE 
    "BEC401": 3, "BEC402": 4, "BEC403": 3, "BEC404": 3, "BECL405": 1,
    "BUHVK406": 1, "BKSKK407": 1, "BBOK408": 1, "BAECK409": 1,

    # 5th Semester ECE
    "BEC501": 3, "BEC502": 4, "BEC503": 3, "BEC504": 3, "BECL505": 1,
    "BEC506A": 3, "BEC506B": 3, "BEC506C": 3, "BEC506D": 3, 
    "BKSKK507": 1, "BAECK508": 1,
    
    # 6th Semester ECE
    "BEC601": 3, "BEC602": 4, "BEC603": 3, "BECL604": 1, 
    "BEC605A": 3, "BEC605B": 3, "BEC605C": 3, "BEC605D": 3,
    "BEC606A": 3, "BEC606B": 3, "BEC606C": 3, "BEC606D": 3,
    "BAECK608": 1,
    
    # 7th Semester ECE
    "BEC701": 3, "BEC702": 3, "BEC703": 3, 
    "BEC704A": 3, "BEC704B": 3, "BEC704C": 3, "BEC704D": 3, 
    "BEC705A": 3, "BEC705B": 3, "BEC705C": 3, "BEC705D": 3,
    
    # 8th Semester ECE (Major Project / Internship)
    "BEC801": 1, "BEC802": 1, "BEC803": 8, "BEC804": 1
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
                
                # Scan line by line safely using ONLY the dictionary
                lines = text.split('\n')
                for line in lines:
                    for code, credits in CREDIT_MAP.items():
                        if re.search(rf'\b{code}\b', line):
                            grade_match = re.search(r'\b(\d{1,3})\s+(P|F)\b', line)
                            if grade_match:
                                marks = int(grade_match.group(1))
                                p_f = grade_match.group(2)
                                grade_letter, gp = calculate_vtu_grade(marks, p_f)
                                
                                # Extract Semester from code (e.g. BEC302 -> 3)
                                sem_match = re.search(r'\d', code)
                                sem = int(sem_match.group()) if sem_match else 0
                                
                                # Backlog handling (keep highest marks)
                                if code not in best_subjects or marks > best_subjects[code]["marks"]:
                                    best_subjects[code] = {
                                        "marks": marks, "grade": grade_letter, 
                                        "gp": gp, "credits": credits, "sem": sem
                                    }

    if not best_subjects: 
        return {"error": "Could not extract marks. Make sure it is a valid ECE PDF."}
    
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

