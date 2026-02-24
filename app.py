from flask import Flask, render_template, request
import pdfplumber
import re
import os

app = Flask(__name__)

# 💥 The Bulletproof Dictionary: 100% Accurate for ECE!
# Add 5th to 8th sem here later by just following the 
# Master VTU Credit Dictionary (1st to 8th Sem ECE - 2022 Scheme)
import string # Add this at the top with your other imports!

# 💥 1. The Common Subjects (Never Change)
CREDIT_MAP = {
    "BCEDK103": 3, "BENGK106": 1, "BICOK107": 1, "BIDTK158": 1,
    "BBEE203": 3, "BPWSK206": 1, "BKSKK207": 1, "BSFHK258": 1,
    "BMATE301": 4, "BKSKK307": 1, "BNSAK358": 1, "BSCK306B": 1,
    "BUHVK406": 1, "BKSKK407": 1, "BBOK408": 1, "BAECK409": 1,
    "BKSKK507": 1, "BAECK508": 1, "BAECK608": 1
}

# 💥 2. First Year Stream Codes (Maths, Physics, Chem)
# E=ECE/EE, S=CS/IS, M=Mech, V=Civil, C=Chemical
for stream in ["E", "S", "M", "V", "C"]:
    CREDIT_MAP[f"BMAT{stream}101"] = 4
    CREDIT_MAP[f"BPHY{stream}102"] = 4
    CREDIT_MAP[f"BCHE{stream}102"] = 4
    CREDIT_MAP[f"BMAT{stream}201"] = 4
    CREDIT_MAP[f"BPHY{stream}202"] = 4
    CREDIT_MAP[f"BCHE{stream}202"] = 4

# 💥 3. First Year Intro Subjects (Letters A to Z at the end)
# Automatically creates BESCK104A, BESCK104B, BESCK104C... all the way to Z!
for letter in string.ascii_uppercase:
    CREDIT_MAP[f"BESCK104{letter}"] = 3
    CREDIT_MAP[f"BETCK105{letter}"] = 3
    CREDIT_MAP[f"BESCK204{letter}"] = 3
    CREDIT_MAP[f"BPLCK205{letter}"] = 3

# 💥 4. Higher Semesters (3rd to 8th) for LITERALLY EVERY BRANCH
# This generates every 2-letter combination from AA to ZZ!
BRANCHES = [a + b for a in string.ascii_uppercase for b in string.ascii_uppercase]

GENERIC_CODES = {
    "302": 4, "303": 3, "304": 3, "L305": 1, 
    "401": 3, "402": 4, "403": 3, "404": 3, "L405": 1,
    "501": 3, "502": 4, "503": 3, "504": 3, "L505": 1,
    "506A": 3, "506B": 3, "506C": 3, "506D": 3, 
    "601": 3, "602": 4, "603": 3, "L604": 1, 
    "605A": 3, "605B": 3, "605C": 3, "605D": 3,
    "606A": 3, "606B": 3, "606C": 3, "606D": 3,
    "701": 3, "702": 3, "703": 3, 
    "704A": 3, "704B": 3, "704C": 3, "704D": 3, 
    "705A": 3, "705B": 3, "705C": 3, "705D": 3,
    "801": 1, "802": 1, "803": 8, "804": 1
}

for branch in BRANCHES:
    for suffix, credits in GENERIC_CODES.items():
        CREDIT_MAP[f"B{branch}{suffix}"] = credits
    

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



