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
    semesters_data = []

    parts = re.split(r'Semester\s+(\d+)', text, flags=re.IGNORECASE)
    
    # Standard VTU Regex Pattern
   pattern = r'([A-Z0-9]+)\s+(.*?)\s+(\d+)\s+(\d+)\s+([A-Z\+]+)'

    for i in range(1, len(parts), 2):
        try:
            sem_num = int(parts[i])
            sem_text = parts[i+1]
        except (IndexError, ValueError):
            continue

        sem_credits = 0
        sem_earned = 0
        subjects_data = []

        matches = re.findall(pattern, sem_text)
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
                
                sem_credits += c
                sem_earned += (gp * c)
                subjects_data.append({"code": code, "marks": marks, "grade": res, "credits": c})

        if sem_credits > 0:
            sgpa = sem_earned / sem_credits
            overall_credits += sem_credits
            overall_earned += sem_earned
            semesters_data.append({
                "semester": sem_num,
                "sgpa": round(sgpa, 2),
                "credits": sem_credits,
                "subjects": subjects_data
            })

    if overall_credits == 0:
        return {"error": "Invalid PDF: Could not find any VTU subjects or credits."}

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

