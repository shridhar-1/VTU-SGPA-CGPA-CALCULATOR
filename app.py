from flask import Flask, render_template, request
import pdfplumber
import re
import os

app = Flask(__name__)

# Master Dictionary
CREDIT_MAP = {
    "BCEDK103": 3, "BENGK106": 1, "BICOK107": 1, "BIDTK158": 1,
    "BBEE203": 3, "BPWSK206": 1, "BKSKK207": 1, "BSFHK258": 1,
    "BMATEC301": 4, "BKSKK307": 1, "BNSAK358": 1, "BSCK306B": 1,
    "BUHVK406": 1, "BKSKK407": 1, "BBOK408": 1, "BAECK409": 1,
    "BKSKK507": 1, "BAECK508": 1, "BAECK608": 1,
    "BMATE101": 4, "BPHYE102": 4, "BCHEE102": 4, "BMATE201": 4, "BPHYE202": 4, "BCHEE202": 4,
    "BEC302": 4, "BEC303": 3, "BEC304": 3, "BECL305": 1,
    "BEC401": 3, "BEC402": 4, "BEC403": 3, "BEC404": 3, "BECL405": 1,
    "BEC701": 3, "BEC702": 3, "BEC703": 3, "BEC801": 1, "BEC802": 1, "BEC803": 8, "BEC804": 1
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
    master_usn = None 
    
    for file in files:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                
                # 💥 WATERMARK FIX: Removed layout=True so background text doesn't break the lines!
                text = page.extract_text() or ""
                
                # USN Security Lock
                usn_match = re.search(r'\b[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}\b', text.upper())
                if usn_match:
                    found_usn = usn_match.group(0)
                    if master_usn is None: 
                        master_usn = found_usn 
                    elif found_usn != master_usn:
                        return {"error": f"Security Alert: Multiple USNs detected ({master_usn} and {found_usn}). Please upload PDFs of the same student!"}
                
                lines = text.split('\n')
                for line in lines:
                    code_match = re.search(r'\bB[A-Z]{2,4}\d{3}[A-Z]?\b', line)
                    if code_match:
                        code = code_match.group(0)
                        
                        # 💥 BULLETPROOF PE FIX: Explicitly check for 0-credit course codes
                        if any(x in code for x in ["PE", "YOG", "NSS", "NSA"]):
                            credits = 0
                        elif code in CREDIT_MAP:
                            credits = CREDIT_MAP[code]
                        else:
                            if "786" in code: credits = 2 
                            elif "803" in code: credits = 8 
                            elif re.search(r'(06|07|08|09|58)[A-Z]?$', code) or 'L' in code: credits = 1
                            else: credits = 3 
                        
                        nums = [int(n) for n in re.findall(r'\b\d{1,3}\b', line) if int(n) <= 200]
                        
                        if nums:
                            marks = max(nums) 
                            perc = (marks / 2) if marks > 100 else marks
                            
                            has_f_grade = bool(re.search(r'\b(F|FAIL)\b', line.upper()))
                            p_f = 'F' if perc < 35 or has_f_grade else 'P'
                            
                            grade, gp = calculate_vtu_grade(perc, p_f)
                            sem = int(re.search(r'\d', code).group()) if re.search(r'\d', code) else 0
                            
                            if code not in best_subjects or marks > best_subjects[code]['marks']:
                                best_subjects[code] = {"marks": marks, "grade": grade, "gp": gp, "credits": credits, "sem": sem}
    
    if not best_subjects: return {"error": "Could not extract marks. The VTU watermark might be too heavy, or the PDF is invalid."}
    
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

    sems = [{"semester": s, "sgpa": round(sem_dict[s]["earned"]/sem_dict[s]["credits"], 2) if sem_dict[s]["credits"] > 0 else 0, "subjects": sem_dict[s]["subjects"]} for s in sorted(sem_dict.keys())]
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

