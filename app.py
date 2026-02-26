from flask import Flask, render_template, request
import pdfplumber
import re
import os

app = Flask(__name__)

# Master Dictionary - Explicitly defined to prevent memory crashes
CREDIT_MAP = {
    "BCEDK103": 3, "BENGK106": 1, "BICOK107": 1, "BIDTK158": 1,
    "BBEE203": 3, "BPWSK206": 1, "BKSKK207": 1, "BSFHK258": 1,
    "BMATE301": 4, "BKSKK307": 1, "BNSAK358": 1, "BSCK306B": 1,
    "BUHVK406": 1, "BKSKK407": 1, "BBOK408": 1, "BAECK409": 1,
    "BKSKK507": 1, "BAECK508": 1, "BAECK608": 1,
    "BMATE101": 4, "BPHYE102": 4, "BCHEE102": 4, "BMATE201": 4, "BPHYE202": 4, "BCHEE202": 4,
    "BEC302": 4, "BEC303": 3, "BEC304": 3, "BECL305": 1,
    "BEC401": 3, "BEC402": 4, "BEC403": 3, "BEC404": 3, "BECL405": 1,
    "BEC701": 3, "BEC702": 3, "BEC703": 3, "BEC801": 1, "BEC802": 1, "BEC803": 8, "BEC804": 1
}

def calculate_vtu_grade(marks, p_f):
    if p_f == 'F' or marks < 40: return 'F', 0
    if marks >= 90: return 'O', 10
    elif marks >= 80: return 'A+', 9
    elif marks >= 70: return 'A', 8
    elif marks >= 60: return 'B+', 7
    elif marks >= 55: return 'B', 6
    elif marks >= 50: return 'C', 5
    else: return 'P', 4

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
