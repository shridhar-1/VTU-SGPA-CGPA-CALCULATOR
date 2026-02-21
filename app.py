import os
import re
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import pdfplumber

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Master VTU 2022 Scheme Credit Dictionary
CREDIT_MAP = {
    "BMATE101": 4, "BCHEE102": 4, "BCEDK103": 3, "BENGK106": 1,
    "BICOK107": 1, "BIDTK158": 1, "BESCK104E": 3, "BETCK105J": 3,
    "BMATE201": 4, "BPHYE202": 4, "BBEE203": 3, "BPWSK206": 1,
    "BKSKK207": 1, "BSFHK258": 1, "BPLCK205B": 3, "BESCK204B": 3
}

def get_grade_point(marks, result):
    if result == 'F': return 0
    elif marks >= 90: return 10
    elif marks >= 80: return 9
    elif marks >= 70: return 8
    elif marks >= 60: return 7
    elif marks >= 55: return 6
    elif marks >= 50: return 5
    elif marks >= 40: return 4
    else: return 0

def calculate_cgpa_from_text(text):
    overall_credits = 0
    overall_earned = 0
    semesters_data = []
    
    parts = re.split(r'Semester\s*:\s*(\d+)', text)
    pattern = r"([A-Z]{4,7}\d{3}[A-Z]?)\s+.*?\s+(\d+)\s+(\d+)\s+(\d+)\s+([PF])\s+\d{4}-\d{2}-\d{2}"
    
    if len(parts) > 1:
        for i in range(1, len(parts), 2):
            sem_num = parts[i]
            sem_text = parts[i+1]
            
            sem_credits = 0
            sem_earned = 0
            subjects_data = []
            
            matches = re.findall(pattern, sem_text)
            for match in matches:
                code, _, _, marks, res = match
                marks = int(marks)
                if code in CREDIT_MAP:
                    c = CREDIT_MAP[code]
                    gp = get_grade_point(marks, res)
                    
                    sem_credits += c
                    sem_earned += (gp * c)
                    subjects_data.append({"code": code, "marks": marks, "grade": gp, "credits": c})
            # --- SAFETY NET FOR INVALID PDFs ---
    if total_credits == 0:
        return {"error": "Invalid PDF. No VTU grades or credits were found in this document!"}
        
    # (Your existing math code continues here...)
    cgpa = total_points / total_credits
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
        return {"error": "Could not extract valid subjects or credits."}
        
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
    # Looking for result_pdfs (plural)
    if 'result_pdfs' not in request.files: 
        return "No files uploaded!"
    
    # 👇 THESE ARE THE TWO LINES YOU ARE MISSING! 👇
    files = request.files.getlist('result_pdfs')
    combined_text = ""
    
    try:
        for file in files:
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # --- NEW: Print exactly what the server is doing! ---
                print(f"⏳ Opening and reading: {filename}...")
                
                with pdfplumber.open(filepath) as pdf:
                    extracted = pdf.pages[0].extract_text()
                    combined_text += extracted + "\n"
                    
                print(f"✅ Successfully extracted text from: {filename}")
        
        print("🧠 All files read! Calculating grand total CGPA now...")
        result_data = calculate_cgpa_from_text(combined_text)
        
        if "error" in result_data:
            print(f"❌ Math Error: {result_data['error']}")
            return f"<h3>Error: {result_data['error']}</h3>"
            
        print("🎉 Math complete! Sending to browser.")
        return render_template('result.html', data=result_data)
        
    except Exception as e:
        print(f"🔥 CRASHED! The error is: {e}")
        return f"An error occurred: {e}"

if __name__ == '__main__':

    app.run(debug=True)
