import re
import os
import pdfplumber
from flask import Flask, request, render_template

app = Flask(__name__)

# Master VTU Credit Dictionary (1st, 2nd, & 3rd Sem ECE)
def get_smart_credits(code):
    # 1. Extract the semester (the first number in the subject code, e.g., BEC401 -> 4)
    sem_match = re.search(r'\d', code)
    sem = int(sem_match.group()) if sem_match else 0
    
    # 2. Hardcode the tricky 1st/2nd Sem subjects that don't follow the rules perfectly
    exact_credits = {
        "BMATE101": 4, "BCHEE102": 4, "BMATE201": 4, "BPHYE202": 4,
        "BCEDK103": 3, "BESCK104E": 3, "BETCK105J": 3, "BBEE203": 3, 
        "BPLCK205B": 3, "BESCK204B": 3
    }
    if code in exact_credits:
        return exact_credits[code], sem

    # 3. YOUR LOGIC: The "Wildcard" rule for 3rd to 8th Sem (All Branches!)
    # Labs, AEC, and UHV usually end in 5, 6, 7, 8, 9, or L -> 1 Credit
    if re.search(r'(05|06|07|08|09|58|L)[A-Z]?$', code):
        return 1, sem
        
    # The second core subject (02) is almost always 4 credits in the VTU 2022 scheme
    if re.search(r'02[A-Z]?$', code): 
        return 4, sem 
        
    # All other core subjects (01, 03, 04, etc.) default to 3 credits
    return 3, sem

def process_pdf(files):
    best_subjects = {}
    master_usn = None
    for file in files:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True) or ""
                
                # Security USN Lock
                usn_match = re.search(r'\b[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}\b', text.upper())
                if usn_match:
                    found_usn = usn_match.group(0)
                    if master_usn is None: master_usn = found_usn
                    elif found_usn != master_usn:
                        return {"error": "Security Alert: Multiple USNs detected!"}
                
                lines = text.split('\n')
                for line in lines:
                    # 💥 THE MAGIC RADAR: Finds ANY VTU Subject Code automatically!
                    code_match = re.search(r'\bB[A-Z]{2,4}\d{3}[A-Z]?\b', line)
                    if code_match:
                        code = code_match.group(0)
                        
                        # Find the marks and the P/F result
                        grade_match = re.search(r'\b(\d{1,3})\s+(P|F)\b', line)
                        if grade_match:
                            marks = int(grade_match.group(1))
                            grade_letter, gp = calculate_vtu_grade(marks, grade_match.group(2))
                            
                            # Automatically calculate credits and semester using your wildcard rule!
                            c, sem = get_smart_credits(code)
                            
                            # Backlog handling
                            if code not in best_subjects or marks > best_subjects[code]["marks"]:
                                best_subjects[code] = {
                                    "marks": marks, "grade": grade_letter, "gp": gp, 
                                    "credits": c, "sem": sem
                                }

    if not best_subjects: return {"error": "Could not extract marks from the PDF."}
    
    sem_dict = {}
    total_credits = total_earned = 0
    for code, data in best_subjects.items():
        s = data["sem"]
        if s not in sem_dict: sem_dict[s] = {"credits": 0, "earned": 0, "subjects": []}
        sem_dict[s]["credits"] += data["credits"]
        sem_dict[s]["earned"] += (data["gp"] * data["credits"])
        sem_dict[s]["subjects"].append({"code": code, "marks": data["marks"], "grade": data["grade"], "credits": data["credits"]})
        total_credits += data["credits"]
        total_earned += (data["gp"] * data["credits"])

    semesters_data = [{"semester": s, "sgpa": round(sem_dict[s]["earned"]/sem_dict[s]["credits"], 2), "credits": sem_dict[s]["credits"], "subjects": sem_dict[s]["subjects"]} for s in sorted(sem_dict.keys())]
    return {"cgpa": round(total_earned/total_credits, 2), "semesters": semesters_data}

def calculate_vtu_grade(marks, result_status):
    if result_status == 'F': return 'F', 0
    marks = int(marks)
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
                # Security USN Lock
                usn_match = re.search(r'\b[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}\b', text.upper())
                if usn_match:
                    found_usn = usn_match.group(0)
                    if master_usn is None: master_usn = found_usn
                    elif found_usn != master_usn:
                        return {"error": f"Security Alert: Multiple USNs detected!"}
                
                lines = text.split('\n')
                for line in lines:
                    for code, c in CREDIT_MAP.items():
                        if code in line:
                            grade_match = re.search(r'\b(\d{1,3})\s+(P|F)\b', line)
                            if grade_match:
                                marks = int(grade_match.group(1))
                                grade_letter, gp = calculate_vtu_grade(marks, grade_match.group(2))
                                # Backlog handling: Only keep the best marks
                                if code not in best_subjects or marks > best_subjects[code]["marks"]:
                                    best_subjects[code] = {
                                        "marks": marks, "grade": grade_letter, "gp": gp, "credits": c, 
                                        "sem": int(re.search(r'\d', code).group())
                                    }

    if not best_subjects: return {"error": "Could not extract marks from the PDF."}
    
    sem_dict = {}
    total_credits = total_earned = 0
    for code, data in best_subjects.items():
        s = data["sem"]
        if s not in sem_dict: sem_dict[s] = {"credits": 0, "earned": 0, "subjects": []}
        sem_dict[s]["credits"] += data["credits"]
        sem_dict[s]["earned"] += (data["gp"] * data["credits"])
        sem_dict[s]["subjects"].append({"code": code, "marks": data["marks"], "grade": data["grade"], "credits": data["credits"]})
        total_credits += data["credits"]
        total_earned += (data["gp"] * data["credits"])

    semesters_data = [{"semester": s, "sgpa": round(sem_dict[s]["earned"]/sem_dict[s]["credits"], 2), "credits": sem_dict[s]["credits"], "subjects": sem_dict[s]["subjects"]} for s in sorted(sem_dict.keys())]
    return {"cgpa": round(total_earned/total_credits, 2), "semesters": semesters_data}

@app.route('/')
def home(): return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('result_pdfs')
    if not files or files[0].filename == '': return render_template('error.html', error_msg="No file selected.")
    result_data = process_pdf(files)
    if "error" in result_data: return render_template('error.html', error_msg=result_data['error'])
    return render_template('result.html', data=result_data)

@app.route('/feedback', methods=['POST'])
def feedback():
    user_issue = request.form.get('issue_text')
    print(f"\n🚨 BUG REPORT: {user_issue}\n", flush=True)
    return render_template('error.html', error_msg="Thank you! Feedback received.", success=True)

if __name__ == '__main__':
    # This line tells Python to use the port Render provides (10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

