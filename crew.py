import os
import sys
import traceback
from crewai import Crew, Process

# Import all agents
from agents import (
    resume_extractor,
    resume_summarizer, # Make sure this is your 'profile_builder_agent'
    job_search_agent,
    job_match_agent,
    interview_search_agent, # Defined, but not used in task list
    # content_analysis_agent, # SKIPPED
    question_generator_agent,
    answer_generator_agent
)

# Import all tasks from your tasks.py file
from tasks import (
    resume_extraction_task,
    resume_summary_task,
    job_search_task,
    job_filter_task,
    find_urls_task, # SKIPPED
    # analyze_content_task, # SKIPPED
    generate_questions_task,
    generate_answers_task
)

# -----------------------------------------------------------------------------
# SINGLE CREW FUNCTION (Your 3-Minute Flow)
# -----------------------------------------------------------------------------
def run_smart_career_crew(pdf_path: str, role: str, company: str, session_folder: str) -> bool:
    """
    Runs the full 3-minute crew, skipping the slow scraping.
    """
    print(f"--- [FULL CREW] STARTING (3-min flow) ---")
    print(f"PDF: {pdf_path}, Role: {role}, Company: {company}, Session: {session_folder}")

    # --- Dynamically update file paths to save in the session folder ---
    resume_summary_task.output_file = os.path.join(session_folder, "candidate_summary.md")
    job_filter_task.output_file = os.path.join(session_folder, "recommended_jobs.md")
    generate_questions_task.output_file = os.path.join(session_folder, "interview_questions.md")
    generate_answers_task.output_file = os.path.join(session_folder, "questions_and_answers.md")

    # --- Define the single, optimized crew ---
    optimized_crew = Crew(
        agents=[
            resume_extractor,
            resume_summarizer,
            interview_search_agent, # This agent is in the list
            question_generator_agent,
            answer_generator_agent,
            job_search_agent,
            job_match_agent
        ],
        tasks=[
            resume_extraction_task,
            resume_summary_task,
            find_urls_task, # This task is in the list (it's fast)
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
        # --- Pass all inputs to kickoff() ---
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
        traceback.print_exc() # Print full error
        return False

# -----------------------------------------------------------------------------
# MAIN BLOCK (for direct testing only)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        from files_split import run_file_splitter
    except ImportError:
        print("Could not import run_file_splitter. Create files_split.py and refactor it.")
        run_file_splitter = None

    print("--- RUNNING crew.py DIRECTLY FOR TESTING ---")
    
    TEST_SESSION_FOLDER = "test_session"
    os.makedirs(TEST_SESSION_FOLDER, exist_ok=True)
    
    pdf = "resume_naveen_1.pdf" 
    role = "Software Engineer"
    company = "Google"
    
    crew_success = run_smart_career_crew(pdf, role, company, TEST_SESSION_FOLDER)
            
    if crew_success and run_file_splitter:
        print("\n--- RUNNING files_split.py FOR TESTING ---")
        run_file_splitter(TEST_SESSION_FOLDER)
    elif not crew_success:
        print("Crew failed, skipping file splitter.")
    
    print("--- DIRECT TEST RUN COMPLETE. Check 'test_session' folder. ---")