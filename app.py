import re
import pdfplumber
from flask import Flask, request, render_template

app = Flask(__name__)

# Master VTU Credit Dictionary (1st, 2nd, & 3rd Sem ECE)
CREDIT_MAP = {
    # 1st & 2nd Semester
    "BMATE101": 4, "BCHEE102": 4, "BCEDK103": 3, "BENGK106": 1,
    "BICOK107": 1, "BIDTK158": 1, "BESCK104E": 3, "BETCK105J": 3,
    "BMATE201": 4, "BPHYE202": 4, "BBEE203": 3, "BPWSK206": 1,
    "BKSKK207": 1, "BSFHK258": 1, "BPLCK205B": 3, "BESCK204B": 3,
    
    # 3rd Semester (ECE)
    "BMATE301": 4, "BEC302": 4, "BEC303": 3, "BEC304": 3, "BECL305": 1,
    
    # 4th Semester
    "BEC401": 4, "BEC402": 4
}

# GOD MODE: Calculate exact grades directly from marks (VTU 2022 Scheme)
def calculate_vtu_grade(marks, result_status):
    if result_status == 'F': 
        return 'F', 0
        
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
    overall_credits = 0
    overall_earned = 0
    sem_dict = {}

    for file in files:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if not text:
                    text = page.extract_text()
                
                if not text:
                    continue
                    
                lines = text.split('\n')
                for line in lines:
                    for code, c in CREDIT_MAP.items():
                        if code in line:
                            # NEW REGEX: Grabs Total Marks sitting right next to the 'P' (Pass) or 'F' (Fail)
                            grade_match = re.search(r'\b(\d{1,3})\s+(P|F)\b', line)
                            
                            if grade_match:
                                marks = grade_match.group(1)
                                result_status = grade_match.group(2)
                                
                                # Let Python calculate the perfect grade!
                                grade_letter, gp = calculate_vtu_grade(marks, result_status)
                                
                                sem_match = re.search(r'\D+(\d)', code)
                                sem_num = int(sem_match.group(1)) if sem_match else 1
                                
                                if sem_num not in sem_dict:
                                    sem_dict[sem_num] = {"credits": 0, "earned": 0, "subjects": []}
                                    
                                existing_codes = [s['code'] for s in sem_dict[sem_num]["subjects"]]
                                if code not in existing_codes:
                                    sem_dict[sem_num]["credits"] += c
                                    sem_dict[sem_num]["earned"] += (gp * c)
                                    sem_dict[sem_num]["subjects"].append({
                                        "code": code, "marks": marks, "grade": grade_letter, "credits": c
                                    })
                                    overall_credits += c
                                    overall_earned += (gp * c)

    if overall_credits == 0:
        return {"error": "Invalid PDF: Could not extract marks. Please try again!"}

    semesters_data = []
    for sem_num in sorted(sem_dict.keys()):
        s_data = sem_dict[sem_num]
        sgpa = s_data["earned"] / s_data["credits"]
        semesters_data.append({
            "semester": sem_num,
            "sgpa": round(sgpa, 2),
            "credits": s_data["credits"],
            "subjects": s_data["subjects"]
        })

    cgpa = overall_earned / overall_credits
    return {
        "cgpa": round(cgpa, 2),
        "total_credits": overall_credits,
        "semesters": semesters_data
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'result_pdfs' not in request.files:
        return "No file part", 400
    
    files = request.files.getlist('result_pdfs')
    if not files or files[0].filename == '':
        return "No selected file", 400

    try:
        result_data = process_pdf(files)
    except Exception as e:
        return f"Error reading PDF: {str(e)}", 500
    
    if "error" in result_data:
        return f"<h3>{result_data['error']}</h3><br><a href='/'>Go Back</a>", 400

    return render_template('result.html', data=result_data)

if __name__ == '__main__':
    app.run(debug=True)
