from dotenv import load_dotenv
load_dotenv()

import os
import shutil
import uuid
import threading
import json
import re
import traceback
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List

# --- CrewAI Imports ---
from crewai import Crew, Process
from agents import (
    resume_extractor,
    resume_summarizer, # Your profile_builder_agent
    job_search_agent,
    job_match_agent,
    interview_search_agent,
    question_generator_agent,
    answer_generator_agent
)
from tasks import (
    resume_extraction_task,
    resume_summary_task,
    job_search_task,
    job_filter_task,
    find_urls_task,
    generate_questions_task,
    generate_answers_task
    # We will not use analyze_content_task
)

# --- LLM & PDF Imports ---
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm_gemini_pro = ChatGoogleGenerativeAI(
        model=os.getenv("MODEL_EVAL"),
        temperature=0.5,
        google_api_key=os.getenv("GEMINI_API_KEY_MINE")
    )
    print("Gemini Pro LLM for evaluation initialized.")
except Exception as e:
    print(f"ERROR: Failed to initialize Gemini Pro LLM: {e}")
    llm_gemini_pro = None

try:
    import pypdf
    print("pypdf imported successfully.")
except ImportError:
    print("ERROR: pypdf not installed. Run 'pip install pypdf'")
    pypdf = None

# --- App Configuration ---
app = FastAPI(title="PrepGuide Backend API")

# --- CORS (Allow all for development) ---
# --- CORS (Cross-Origin Resource Sharing) ---
origins = [
    "*"  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Session & File Configuration ---
session_status: Dict[str, str] = {}
SESSION_BASE_FOLDER = "sessions"
QUESTIONS_FOLDER = 'questions_folder'
ANSWERS_FOLDER = 'answers_folder'
RECOMMENDED_JOBS_FILE = 'recommended_jobs.md'
CANDIDATE_SUMMARY_FILE = 'candidate_summary.md'
os.makedirs(SESSION_BASE_FOLDER, exist_ok=True)

# -----------------------------------------------------------------------------
# HELPER FUNCTION: Smart Career Crew
# (This is your crew.py logic, now inside main.py)
# -----------------------------------------------------------------------------
def run_smart_career_crew(pdf_path: str, role: str, company: str, session_folder: str) -> bool:
    """
    Runs the full 3-minute crew IN THIS PROCESS.
    """
    print(f"--- [FULL CREW] STARTING (3-min flow) ---")
    print(f"PDF: {pdf_path}, Role: {role}, Company: {company}, Session: {session_folder}")

    # --- THIS IS THE CRITICAL FIX ---
    # We are modifying the task objects that are IN MEMORY in *this* script.
    resume_summary_task.output_file = os.path.join(session_folder, "candidate_summary.md")
    job_filter_task.output_file = os.path.join(session_folder, "recommended_jobs.md")
    generate_questions_task.output_file = os.path.join(session_folder, "interview_questions.md")
    generate_answers_task.output_file = os.path.join(session_folder, "questions_and_answers.md")
    # We don't need to set output_file for find_urls_task as it's not saved

    optimized_crew = Crew(
        agents=[
            resume_extractor,
            resume_summarizer,
            #interview_search_agent,
            question_generator_agent,
            answer_generator_agent,
            job_search_agent,
            job_match_agent
        ],
        tasks=[
            resume_extraction_task,
            resume_summary_task,
            #find_urls_task, # The fast URL finding
            # analyze_content_task is SKIPPED
            generate_questions_task,
            generate_answers_task,
            job_search_task,
            job_filter_task
        ],
        process=Process.sequential,
        verbose=True
    )
    
    try:
        result = optimized_crew.kickoff(inputs={
            'target_pdf': pdf_path,
            'target_role': role,
            'target_company': company
        })
        print(f"--- [FULL CREW] FINISHED ---")
        return True
    except Exception as e:
        print(f"--- [FULL CREW] FAILED ---")
        print(f"Error: {e}")
        traceback.print_exc()
        return False

# -----------------------------------------------------------------------------
# HELPER FUNCTION: File Splitter
# (This is your files_split.py logic, now inside main.py)
# -----------------------------------------------------------------------------
def run_file_splitter(session_folder: str) -> bool:
    """
    Reads and splits the markdown files in the session folder.
    """
    print(f"--- [SPLITTER] STARTING for session: {session_folder} ---")
    
    section_mapping = {
        "resume-based questions": "resume_based.md",
        "technical questions": "technical.md",
        "behavioral questions": "behavioural.md",
        "technical scenario-based questions": "scenario_based.md"
    }

    def get_filename_from_heading(heading_line):
        heading_text = heading_line.strip().lstrip('#').strip().lower()
        for key, filename in section_mapping.items():
            if key in heading_text:
                return filename
        print(f"Warning: No mapping found for heading: {heading_text}")
        return None

    source_to_output_map = {
        os.path.join(session_folder, "interview_questions.md"): os.path.join(session_folder, "questions_folder"),
        os.path.join(session_folder, "questions_and_answers.md"): os.path.join(session_folder, "answers_folder")
    }
    
    heading_regex = re.compile(r'(^[ \t]*#+[ \t].*$)', re.MULTILINE)

    try:
        for source_file, output_dir in source_to_output_map.items():
            print(f"--- [SPLITTER] Processing: {source_file} ---")
            os.makedirs(output_dir, exist_ok=True)

            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                print(f"Error: Source file '{source_file}' not found. Skipping.")
                if "interview_questions.md" in source_file:
                    print("CRITICAL: interview_questions.md not found. Splitter failing.")
                    return False
                continue

            parts = heading_regex.split(content)
            if not parts: continue

            if parts[0].strip():
                intro_path = os.path.join(output_dir, "intro.md")
                with open(intro_path, 'w', encoding='utf-8') as f:
                    f.write(parts[0].strip())
                print(f"Created: {intro_path}")

            for i in range(1, len(parts), 2):
                heading = parts[i]
                section_content = parts[i+1] if (i + 1) < len(parts) else ""
                filename = get_filename_from_heading(heading)

                if filename:
                    output_path = os.path.join(output_dir, filename)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(heading.strip() + '\n\n')
                        f.write(section_content.strip())
                    print(f"Created: {output_path}")
        
        print("--- [SPLITTER] FINISHED ---")
        return True

    except Exception as e:
        print(f"--- [SPLITTER] FAILED ---")
        traceback.print_exc()
        return False

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS (PDF, Evaluation, etc. - No changes)
# -----------------------------------------------------------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    # ... (Same as the code I provided before)
    if not pypdf: return "Error: pypdf library not installed."
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        print(f"Extracted text from {pdf_path}")
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return f"Error: Could not read resume text - {e}"

# In main.py, replace the OLD parse_model_answers function with this NEW one

def parse_model_answers(file_content: str) -> Dict[str, str]:
    """
    Parses a 'questions_and_answers.md' file content.
    Returns a dictionary mapping {question_text: answer_text}
    """
    answers_map = {}
    try:
        # This regex finds a question (e.g., **1. ...**) and then captures
        # the answer text until it hits the *next* bolded question
        # or the end of the file (\Z).
        pattern = re.compile(r"\*\*(?P<question>.+?)\*\*\s*\*Model Answer:\*(?P<answer>.+?)(?=\n\n\*\*|\Z)", re.DOTALL)

        for match in pattern.finditer(file_content):
            # Clean the question text
            question_text = re.sub(r"^\d+\.\s*", "", match.group("question").strip()).strip().lstrip('[').rstrip(']')
            answer_text = match.group("answer").strip()

            if question_text and answer_text:
                answers_map[question_text] = answer_text

        print(f"Parsed {len(answers_map)} model answers from content.")
        return answers_map
    except Exception as e:
        print(f"Error parsing model answers: {e}")
        traceback.print_exc()
        return {}

def evaluate_answers(questions_list: List[str], answers_list: List[str], model_answers_list: List[str], resume_text: str) -> List[Dict]:
    # ... (Same as the code I provided before)
    if llm_gemini_pro is None: raise Exception("Evaluation LLM not initialized.")
    evaluation_results = []
    print("\n--- Starting Evaluation ---")
    for i, question in enumerate(questions_list):
        user_answer = answers_list[i] if i < len(answers_list) and answers_list[i] else "No answer provided."
        model_answer = model_answers_list[i] if i < len(model_answers_list) else "No model answer available."
        prompt = f"""
        **Context:**
        ---
        {resume_text}
        ---
        **Interview Question:**
        "{question}"
        **A Model Answer to this question is:**
        "{model_answer}"
        **The Candidate's actual Answer was:**
        "{user_answer}"

        **Evaluation Task:**
        Evaluate the Candidate's Answer based on: Relevance, Completeness (vs Model Answer), Clarity, and Contextual Accuracy (vs Resume).
        Provide scores (1-5), explanations, and suggestions.
        **Output Format (Strict JSON):**
        {{
          "scores": {{"relevance": ..., "completeness": ..., "clarity": ..., "contextual_accuracy": ...}},
          "explanations": {{"relevance": "...", "completeness": "...", "clarity": "...", "contextual_accuracy": "..."}},
          "suggestions": "..."
        }}
        """
        try:
            print(f"Evaluating Q{i+1}: {question[:50]}...")
            response = llm_gemini_pro.invoke(prompt)
            llm_output_text = response.content
            cleaned_json_text = llm_output_text.strip().lstrip('```json').rstrip('```').strip()
            evaluation_data = json.loads(cleaned_json_text)
            evaluation_results.append({
                "question": question,
                "answer": user_answer,
                "scores": evaluation_data.get("scores", {}),
                "explanations": evaluation_data.get("explanations", {}),
                "suggestions": evaluation_data.get("suggestions", "No suggestions provided.")
            })
        except Exception as e:
            print(f"Error evaluating Q{i+1}: {e}")
            evaluation_results.append({"question": question, "answer": user_answer, "error": f"Failed to evaluate: {e}"})
    print("--- Evaluation Finished ---")
    return evaluation_results

# -----------------------------------------------------------------------------
# HELPER FUNCTION: Run Background Tasks
# -----------------------------------------------------------------------------
# In main.py
# In main.py, replace your existing run_background_tasks function with this one.
# (The rest of main.py stays the same)

def run_background_tasks(session_id: str, pdf_path: str, role: str, company: str):
    """
    This function runs the full 3-minute crew + splitter in a 
    separate thread.
    """
    session_folder = os.path.join(SESSION_BASE_FOLDER, session_id)
    try:
        # Step 1: Run the full 3-minute crew
        crew_success = run_smart_career_crew(pdf_path, role, company, session_folder)
        
        if not crew_success:
            # This catches if crew.kickoff() itself crashed
            raise Exception("CrewAI process failed. Check crew.py logs.")
        
        # --- *** NEW VALIDATION STEP (THIS IS THE FIX) *** ---
        # We must check if the files were *actually* created.
        print("--- [VALIDATION] Checking for critical crew output files... ---")
        q_file = os.path.join(session_folder, "interview_questions.md")
        a_file = os.path.join(session_folder, "questions_and_answers.md")
        s_file = os.path.join(session_folder, "candidate_summary.md")
        
        # Check if all 3 critical files exist
        if not all(os.path.exists(f) for f in [q_file, a_file, s_file]):
            print(f"CRITICAL: Crew finished but output files are missing.")
            print(f"File {q_file} exists: {os.path.exists(q_file)}")
            print(f"File {a_file} exists: {os.path.exists(a_file)}")
            print(f"File {s_file} exists: {os.path.exists(s_file)}")
            raise Exception("CrewAI finished but failed to generate critical output files.")
        else:
            print("--- [VALIDATION] All critical files found. Proceeding to splitter. ---")
        # --- *** END VALIDATION *** ---

        # Step 2: Run the file splitter
        split_success = run_file_splitter(session_folder)
        
        if not split_success:
            raise Exception("File splitting process failed. Check splitter logs.")
            
        # Step 3: Mark session as ready
        session_status[session_id] = "ready"
        print(f"Session {session_id} is READY.")

    except Exception as e:
        print(f"--- BACKGROUND TASK FAILED for session {session_id} ---")
        print(f"Error: {e}")
        traceback.print_exc()
        session_status[session_id] = "error"

# -----------------------------------------------------------------------------
# --- Pydantic Models for Request Bodies ---
# -----------------------------------------------------------------------------
class EvaluateRequest(BaseModel):
    user_answers: List[str]
    questions_asked: List[str]
    model_answers: List[str]

# -----------------------------------------------------------------------------
# --- API Endpoints ---
# -----------------------------------------------------------------------------

@app.post("/start-session")
async def start_session_endpoint(
    resume: UploadFile = File(...),
    target_role: str = Form(...),
    target_company: str = Form(...)
):
    """
    Starts the 3-minute crew process in the background and returns
    a session_id immediately.
    """
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(SESSION_BASE_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    pdf_path = os.path.join(session_folder, "resume.pdf")
    try:
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        print(f"Resume saved to: {pdf_path}")
    except Exception as e:
         print(f"Error saving file: {e}")
         raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        await resume.close()
    
    session_status[session_id] = "processing"
    
    # Start the 3-minute background task
    thread = threading.Thread(
        target=run_background_tasks,
        args=(session_id, pdf_path, target_role, target_company)
    )
    thread.start()
    
    print(f"Session {session_id} started. Returning to user.")
    return {"session_id": session_id}


@app.get("/get-session-status/{session_id}")
def get_status_endpoint(session_id: str):
    """
    Frontend polls this endpoint to check if the 3-minute
    crew is finished.
    """
    status = session_status.get(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"session_id": session_id, "status": status}


# In main.py, replace the OLD get_interview_data_endpoint with this NEW one

@app.get("/get-interview-data/{session_id}")
def get_interview_data_endpoint(session_id: str, round_type: str = "General (Mixed)"):
    """
    Once status is 'ready', frontend calls this to get
    the 5 questions, 5 model answers, and candidate summary.
    """
    session_folder = os.path.join(SESSION_BASE_FOLDER, session_id)
    if not os.path.exists(session_folder) or session_status.get(session_id) != "ready":
        raise HTTPException(status_code=404, detail="Session not ready or not found.")

    # --- 1. Load Candidate Summary ---
    try:
        summary_path = os.path.join(session_folder, CANDIDATE_SUMMARY_FILE)
        with open(summary_path, 'r', encoding='utf-8') as f:
            candidate_summary = f.read()
    except Exception as e:
        print(f"Error reading summary: {e}")
        candidate_summary = "Could not load candidate summary."

    # --- 2. Load Questions based on Round Type ---
    all_questions = []
    files_to_load = []
    round_type_lower = round_type.lower()

    q_folder = os.path.join(session_folder, QUESTIONS_FOLDER)
    if "technical" in round_type_lower:
        files_to_load.extend(["technical.md", "scenario_based.md", "resume_based.md"])
    elif "behavioral" in round_type_lower:
        files_to_load.append("behavioural.md")
    else:
        files_to_load.extend(["technical.md", "scenario_based.md", "resume_based.md", "behavioural.md"])

    for filename in files_to_load:
        filepath = os.path.join(q_folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

                # --- NEW ROBUST REGEX ---
                # This captures multi-line questions.
                # It finds "1. " and captures everything until the *next* "2. " or end of file.
                pattern = re.compile(r"^\d+\.\s*(.+?)(?=\n\s*\d+\.|\Z)", re.DOTALL | re.MULTILINE)
                q_list = pattern.findall(content)
                # --- END NEW REGEX ---

                cleaned_q_list = [q.strip().lstrip('[').rstrip(']') for q in q_list if q.strip()]
                all_questions.extend(cleaned_q_list)
                print(f"Loaded {len(cleaned_q_list)} questions from {filename}")
        except Exception as e:
            print(f"Warning: Could not read question file {filepath}: {e}")

    # --- 3. Load ALL Model Answers into a map (No change here) ---
    all_model_answers_map = {}
    a_folder = os.path.join(session_folder, ANSWERS_FOLDER)
    for filename in os.listdir(a_folder):
        filepath = os.path.join(a_folder, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # This now uses your new, fixed parser
                answers_map = parse_model_answers(content) 
                all_model_answers_map.update(answers_map)
        except Exception as e:
            print(f"Warning: Could not read answer file {filepath}: {e}")

    # --- 4. Select 5 questions AND their matching answers (Improved matching) ---
    import random
    random.shuffle(all_questions)

    selected_questions = []
    selected_model_answers = []

    # Create a cleaned map for robust matching
    cleaned_model_answers_map = {
        key.strip().replace("\n", " "): value 
        for key, value in all_model_answers_map.items()
    }

    for q_text in all_questions:
        if len(selected_questions) >= 5:
            break

        # Clean the question from the questions_folder
        q_clean = q_text.strip().replace("\n", " ")

        # Try to find an exact match in the cleaned map
        if q_clean in cleaned_model_answers_map:
            selected_questions.append(q_text) # Append the original multi-line question
            selected_model_answers.append(cleaned_model_answers_map[q_clean])
        else:
            # This warning is now more useful
            print(f"--- MATCHING WARNING ---")
            print(f"Could not find exact match for question: '{q_clean}'")
            print(f"Available answer keys: {list(cleaned_model_answers_map.keys())}")
            print(f"--- END WARNING ---")

    if not selected_questions:
         raise HTTPException(status_code=500, detail="No questions could be loaded or matched with answers.")

    return {
        "questions": selected_questions,
        "model_answers": selected_model_answers,
        "candidate_summary": candidate_summary
    }

@app.post("/evaluate-answers/{session_id}")
def evaluate_answers_endpoint(session_id: str, request_data: EvaluateRequest):
    """
    Receives the user's answers and evaluates them.
    """
    session_folder = os.path.join(SESSION_BASE_FOLDER, session_id)
    pdf_path = os.path.join(session_folder, "resume.pdf")
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Session not found or resume file missing.")

    resume_text = extract_text_from_pdf(pdf_path)
    if "Error:" in resume_text:
        raise HTTPException(status_code=500, detail=resume_text)

    results = evaluate_answers(
        questions_list=request_data.questions_asked,
        answers_list=request_data.user_answers,
        model_answers_list=request_data.model_answers,
        resume_text=resume_text
    )
    
    return {"evaluation_results": results}


@app.get("/get-job-recommendations/{session_id}")
def get_job_recommendations_endpoint(session_id: str):
    """
    On-demand endpoint to retrieve the job recommendations.
    """
    session_folder = os.path.join(SESSION_BASE_FOLDER, session_id)
    jobs_file_path = os.path.join(session_folder, RECOMMENDED_JOBS_FILE)
    
    if not os.path.exists(jobs_file_path) or session_status.get(session_id) != "ready":
         raise HTTPException(status_code=404, detail="Job recommendations not ready or session not found.")
         
    try:
        with open(jobs_file_path, 'r', encoding='utf-8') as f:
            jobs_content = f.read()
        return {"jobs_markdown": jobs_content}
    except Exception as e:
        print(f"Error reading jobs file: {e}")
        raise HTTPException(status_code=500, detail="Could not read job recommendations file.")

# --- How to Run ---
# 1. Save this code as main.py
# 2. Make sure crew.py and files_split.py are in the same folder
# 3. Run: uvicorn main:app --host 0.0.0.0 --port 5001 --reload

