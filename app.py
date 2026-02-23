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

# Calculate exact grades directly from marks (VTU 2022 Scheme)
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
    best_subjects = {} # Stores highest marks for each subject
    master_usn = None  # Security lock for Student USN

    for file in files:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if not text:
                    text = page.extract_text()
                
                if not text:
                    continue

                # SECURITY UPGRADE: The USN Lock
                # Looks for VTU format USNs (e.g., 1AA21EC001)
                usn_match = re.search(r'\b[1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3}\b', text.upper())
                if usn_match:
                    found_usn = usn_match.group(0)
                    if master_usn is None:
                        master_usn = found_usn # Lock onto the first student
                    elif found_usn != master_usn:
                        # Stop everything if a friend's result is mixed in!
                        return {"error": f"Security Alert: You uploaded results for two different students ({master_usn} and {found_usn})!"}
                    
                lines = text.split('\n')
                for line in lines:
                    for code, c in CREDIT_MAP.items():
                        if code in line:
                            # Grabs Total Marks sitting next to P or F
                            grade_match = re.search(r'\b(\d{1,3})\s+(P|F)\b', line)
                            
                            if grade_match:
                                marks = int(grade_match.group(1))
                                result_status = grade_match.group(2)
                                
                                grade_letter, gp = calculate_vtu_grade(marks, result_status)
                                sem_match = re.search(r'\D+(\d)', code)
                                sem_num = int(sem_match.group(1)) if sem_match else 1
                                
                                # BACKLOG UPGRADE: Highest Marks Win!
                                if code not in best_subjects:
                                    best_subjects[code] = {
                                        "marks": marks, "grade": grade_letter, "gp": gp, "credits": c, "sem": sem_num
                                    }
                                else:
                                    # If student failed before but passed later, this overwrites it!
                                    if marks > best_subjects[code]["marks"]:
                                        best_subjects[code] = {
                                            "marks": marks, "grade": grade_letter, "gp": gp, "credits": c, "sem": sem_num
                                        }

    if not best_subjects:
        return {"error": "Invalid PDF: Could not extract marks. Please try again!"}

    # Now calculate the final SGPA & CGPA using only the best grades
    sem_dict = {}
    overall_credits = 0
    overall_earned = 0

    for code, data in best_subjects.items():
        sem_num = data["sem"]
        if sem_num not in sem_dict:
            sem_dict[sem_num] = {"credits": 0, "earned": 0, "subjects": []}
            
        sem_dict[sem_num]["credits"] += data["credits"]
        sem_dict[sem_num]["earned"] += (data["gp"] * data["credits"])
        sem_dict[sem_num]["subjects"].append({
            "code": code, "marks": data["marks"], "grade": data["grade"], "credits": data["credits"]
        })
        overall_credits += data["credits"]
        overall_earned += (data["gp"] * data["credits"])

    semesters_data = []
    for sem_num in sorted(sem_dict.keys()):
        s_data = sem_dict[sem_num]
        sgpa = s_data["earned"] / s_data["credits"] if s_data["credits"] > 0 else 0
        semesters_data.append({
            "semester": sem_num,
            "sgpa": round(sgpa, 2),
            "credits": s_data["credits"],
            "subjects": s_data["subjects"]
        })

    cgpa = overall_earned / overall_credits if overall_credits > 0 else 0
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
        return render_template('error.html', error_msg="No file uploaded.")
    
    files = request.files.getlist('result_pdfs')
    if not files or files[0].filename == '':
        return render_template('error.html', error_msg="No selected file.")

    try:
        result_data = process_pdf(files)
    except Exception as e:
        return render_template('error.html', error_msg=f"Error reading PDF: {str(e)}")
    
    if "error" in result_data:
        return render_template('error.html', error_msg=result_data['error'])

    return render_template('result.html', data=result_data)
    
    @app.route('/feedback', methods=['POST'])
    def feedback():
        user_issue = request.form.get('issue_text')
    # This prints directly to your Render Logs so you can read it!
    print(f"\n🚨 NEW BUG REPORT RECEIVED: {user_issue}\n", flush=True)
    return render_template('error.html', error_msg="Thank you! Your feedback has been sent to the developer.", success=True)
    
    import os
    
    if __name__ == '__main__':
    # Grab the port Render gives us, or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Force Python to broadcast to the entire internet!
    app.run(host='0.0.0.0', port=port, debug=False)

