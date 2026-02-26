from flask import Flask, render_template, request
import pdfplumber
import re
import os

app = Flask(__name__)

# Master Dictionary - Explicitly defined to prevent memory crashes
CREDIT_MAP = {
    # --- COMMON 1ST & 2ND YEAR SUBJECTS ---
    "BKSKK507": 1, "BAECK508": 1, "BAECK608": 1,

    # --- 1st Year Stream specific (Math, Physics, Chem) ---
    "BMATE101": 4, "BPHYE102": 4, "BCHEE102": 4, "BMATE201": 4, "BPHYE202": 4, "BCHEE202": 4, # ECE/EEE
    "BMATS101": 4, "BPHYS102": 4, "BCHES102": 4, "BMATS201": 4, "BPHYS202": 4, "BCHES202": 4, # CSE/ISE
    "BMATM101": 4, "BPHYM102": 4, "BCHEM102": 4, "BMATM201": 4, "BPHYM202": 4, "BCHEM202": 4, # MECH
    "BMATV101": 4, "BPHYV102": 4, "BCHEV102": 4, "BMATV201": 4, "BPHYV202": 4, "BCHEV202": 4, # CIVIL
    "BMATE101": 4, "BPHYE102": 4, "BCHEE102": 4, "BMATE201": 4, "BPHYE202": 4, "BCHEE202": 4, 
    "BMATS101": 4, "BPHYS102": 4, "BCHES102": 4, "BMATS201": 4, "BPHYS202": 4, "BCHES202": 4, 
    "BMATM101": 4, "BPHYM102": 4, "BCHEM102": 4, "BMATM201": 4, "BPHYM202": 4, "BCHEM202": 4, 
    "BMATV101": 4, "BPHYV102": 4, "BCHEV102": 4, "BMATV201": 4, "BPHYV202": 4, "BCHEV202": 4, 

    # --- 1st Year Intro Subjects (A to J) ---
    "BESCK104A": 3, "BESCK104B": 3, "BESCK104C": 3, "BESCK104D": 3, "BESCK104E": 3,
    "BETCK105A": 3, "BETCK105B": 3, "BETCK105C": 3, "BETCK105D": 3, "BETCK105E": 3, "BETCK105J": 3,
    "BESCK204A": 3, "BESCK204B": 3, "BESCK204C": 3, "BESCK204D": 3, "BESCK204E": 3,
    "BPLCK205A": 3, "BPLCK205B": 3, "BPLCK205C": 3, "BPLCK205D": 3, "BPLCK205E": 3,

    # ==========================================
    # --- ELECTRONICS & COMMUNICATION (EC) ---
    # ==========================================
    "BEC302": 4, "BEC303": 3, "BEC304": 3, "BECL305": 1,
    "BEC401": 3, "BEC402": 4, "BEC403": 3, "BEC404": 3, "BECL405": 1,
    "BEC501": 3, "BEC502": 4, "BEC503": 3, "BEC504": 3, "BECL505": 1,
    "BEC705A": 3, "BEC705B": 3, "BEC705C": 3, "BEC705D": 3,
    "BEC801": 1, "BEC802": 1, "BEC803": 8, "BEC804": 1,

    # ==========================================
    # --- COMPUTER SCIENCE (CS) ---
    # ==========================================
    "BCS302": 4, "BCS303": 3, "BCS304": 3, "BCSL305": 1,
    "BCS401": 3, "BCS402": 4, "BCS403": 3, "BCS404": 3, "BCSL405": 1,
    "BCS501": 3, "BCS502": 4, "BCS503": 3, "BCS504": 3, "BCSL505": 1,
    "BCS705A": 3, "BCS705B": 3, "BCS705C": 3, "BCS705D": 3,
    "BCS801": 1, "BCS802": 1, "BCS803": 8, "BCS804": 1,

    # ==========================================
    # --- INFORMATION SCIENCE (IS) ---
    # ==========================================
    "BIS302": 4, "BIS303": 3, "BIS304": 3, "BISL305": 1,
    "BIS401": 3, "BIS402": 4, "BIS403": 3, "BIS404": 3, "BISL405": 1,
    "BIS501": 3, "BIS502": 4, "BIS503": 3, "BIS504": 3, "BISL505": 1,
    "BIS705A": 3, "BIS705B": 3, "BIS705C": 3, "BIS705D": 3,
    "BIS801": 1, "BIS802": 1, "BIS803": 8, "BIS804": 1,

    # ==========================================
    # --- ELECTRICAL & ELECTRONICS (EE) ---
    # ==========================================
    "BEE302": 4, "BEE303": 3, "BEE304": 3, "BEEL305": 1,
    "BEE401": 3, "BEE402": 4, "BEE403": 3, "BEE404": 3, "BEEL405": 1,
    "BEE501": 3, "BEE502": 4, "BEE503": 3, "BEE504": 3, "BEEL505": 1,
    "BEE705A": 3, "BEE705B": 3, "BEE705C": 3, "BEE705D": 3,
    "BEE801": 1, "BEE802": 1, "BEE803": 8, "BEE804": 1,

    # ==========================================
    # --- MECHANICAL (ME) ---
    # ==========================================
    "BME302": 4, "BME303": 3, "BME304": 3, "BMEL305": 1,
    "BME401": 3, "BME402": 4, "BME403": 3, "BME404": 3, "BMEL405": 1,
    "BME501": 3, "BME502": 4, "BME503": 3, "BME504": 3, "BMEL505": 1,
    "BME705A": 3, "BME705B": 3, "BME705C": 3, "BME705D": 3,
    "BME801": 1, "BME802": 1, "BME803": 8, "BME804": 1,

    # ==========================================
    # --- CIVIL (CV) ---
    # ==========================================
    "BCV302": 4, "BCV303": 3, "BCV304": 3, "BCVL305": 1,
    "BCV401": 3, "BCV402": 4, "BCV403": 3, "BCV404": 3, "BCVL405": 1,
    "BCV501": 3, "BCV502": 4, "BCV503": 3, "BCV504": 3, "BCVL505": 1,
    "BCV801": 1, "BCV802": 1, "BCV803": 8, "BCV804": 1
}

def calculate_vtu_grade(marks, p_f):
    if p_f == 'F' or marks < 35: return 'F', 0
    if marks >= 90: return 'O', 10
    elif marks >= 80: return 'A+', 9
    elif marks >= 70: return 'A', 8
    elif marks >= 60: return 'B+', 7
    elif marks >= 55: return 'B', 6
    elif marks >= 50: return 'C', 5
    elif marks >= 35: return 'P', 4
    else: return 'F', 0
    
def process_pdf(files):
    best_subjects = {}
    for file in files:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True) or ""
                lines = text.split('\n')
                for line in lines:
                    code_match = re.search(r'\bB[A-Z]{2,4}\d{3}[A-Z]?\b', line)
                    if code_match:
                        code = code_match.group(0)
                        credits = CREDIT_MAP.get(code, 3) 
                        
                        nums = [int(n) for n in re.findall(r'\b\d{1,3}\b', line) if int(n) <= 200]
                        
                        if nums:
                            # 💥 FIX 1: Safely grab the highest number (Total Marks). No more "last number" hack!
                            marks = max(nums) 
                            
                            perc = (marks / 2) if marks > 100 else marks
                            
                            # 💥 FIX 2: Only fail if the word is exactly "F" or "FAIL".
                            has_f_grade = bool(re.search(r'\b(F|FAIL)\b', line.upper()))
                            p_f = 'F' if perc < 40 or has_f_grade else 'P'
                            
                            grade, gp = calculate_vtu_grade(perc, p_f)
                            sem = int(re.search(r'\d', code).group()) if re.search(r'\d', code) else 0
                            
                            if code not in best_subjects or marks > best_subjects[code]['marks']:
                                best_subjects[code] = {"marks": marks, "grade": grade, "gp": gp, "credits": credits, "sem": sem}
    
    if not best_subjects: return {"error": "No data found"}
    sem_dict = {}
    total_cr = total_earn = 0
    for code, d in best_subjects.items():
        s = d["sem"]
        if s not in sem_dict: sem_dict[s] = {"credits": 0, "earned": 0, "subjects": []}
        sem_dict[s]["credits"] += d["credits"]
        sem_dict[s]["earned"] += (d["gp"] * d["credits"])
        sem_dict[s]["subjects"].append({"code": code, "marks": d["marks"], "grade": d["grade"], "credits": d["credits"]})
        total_cr += d["credits"]
        total_earn += (d["gp"] * d["credits"])

    sems = [{"semester": s, "sgpa": round(sem_dict[s]["earned"]/sem_dict[s]["credits"], 2), "subjects": sem_dict[s]["subjects"]} for s in sorted(sem_dict.keys())]
    return {"cgpa": round(total_earn/total_cr, 2) if total_cr > 0 else 0, "semesters": sems}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('result_pdfs')
    result = process_pdf(files)
    if "error" in result: return result["error"], 400
    return render_template('result.html', data=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))


