import re
import pdfplumber
from flask import Flask, request, render_template

app = Flask(__name__)

# Master VTU Credit Dictionary
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

def get_grade_point(marks, grade):
    grade = str(grade).strip().upper()
    if grade == 'O': return 10
    elif grade == 'A+': return 9
    elif grade == 'A': return 8
    elif grade == 'B+': return 7
    elif grade == 'B': return 6
    elif grade == 'C': return 5
    elif grade == 'P': return 4
    else: return 0

def calculate_cgpa_from_text(text):
    overall_credits = 0
    overall_earned = 0
    sem_dict = {}

    # Scan the ENTIRE document at once! No more splitting by "Semester"
    pattern = r'([A-Z0-9]+)\s+(.*?)\s+(\d+)\s+(\d+)\s+([A-Z\+]+)'
    matches = re.findall(pattern, text)

    for match in matches:
        code = match[0]
        marks = match[3]
        res = match[4]
        
        try:
            marks = int(marks)
        except ValueError:
            continue
            
        if code in CREDIT_MAP:
            c = CREDIT_MAP[code]
            gp = get_grade_point(marks, res)
            
            # Auto-detect semester from subject code! (e.g. BMATE201 -> 2)
            sem_match = re.search(r'\D+(\d)', code)
            sem_num = int(sem_match.group(1)) if sem_match else 1
            
            if sem_num not in sem_dict:
                sem_dict[sem_num] = {"credits": 0, "earned": 0, "subjects": []}
            
            sem_dict[sem_num]["credits"] += c
            sem_dict[sem_num]["earned"] += (gp * c)
            sem_dict[sem_num]["subjects"].append({
                "code": code, "marks": marks, "grade": res, "credits": c
            })
            
            overall_credits += c
            overall_earned += (gp * c)

    if overall_credits == 0:
        return {"error": "Invalid PDF: Could not find VTU subjects. Check if your subject codes are correctly added to the CREDIT_MAP at the top of app.py!"}

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

    if overall_credits == 0:
        return {"error": f"DEBUG X-RAY - HERE IS WHAT THE APP SEES:<br><pre>{text[:2000]}</pre>"}
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

    full_text = ""
    for file in files:
        if file.filename.endswith('.pdf'):
            try:
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += page_text + "\n"
            except Exception as e:
                return f"Error reading PDF: {str(e)}", 500

    result_data = calculate_cgpa_from_text(full_text)
    
    if "error" in result_data:
        return f"<h3>{result_data['error']}</h3><br><a href='/'>Go Back</a>", 400

    return render_template('result.html', data=result_data)

if __name__ == '__main__':
    app.run(debug=True)





