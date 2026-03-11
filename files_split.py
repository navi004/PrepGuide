import os
import re

# --- DEFINE YOUR SECTION MAPPING ---
section_mapping = {
    "resume-based questions": "resume_based.md",
    "technical questions": "technical.md",
    "behavioral questions": "behavioural.md", # Corrected spelling
    "technical scenario-based questions": "scenario_based.md"
}

def get_filename_from_heading(heading_line):
    """Finds the matching filename for a given heading line."""
    heading_text = heading_line.strip().lstrip('#').strip().lower()
    
    for key, filename in section_mapping.items():
        if key in heading_text:
            return filename
    print(f"Warning: No mapping found for heading: {heading_text}")
    return None

# -----------------------------------------------------------------------------
# FUNCTION 1: RUNS THE FILE SPLITTER
# -----------------------------------------------------------------------------
def run_file_splitter(session_folder):
    """
    Reads source markdown files from a session folder, splits them by 
    headings, and saves the content to new files in corresponding 
    output directories within that session folder.
    
    Args:
        session_folder (str): The unique path to the user's session.
        
    Returns:
        bool: True on success, False on failure.
    """
    
    print(f"--- [SPLITTER] STARTING for session: {session_folder} ---")
    
    # Define source files and output folders (relative to session folder)
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
                continue

            parts = heading_regex.split(content)

            if not parts:
                print("No content found.")
                continue

            if parts[0].strip():
                intro_path = os.path.join(output_dir, "intro.md")
                with open(intro_path, 'w', encoding='utf-8') as f:
                    f.write(parts[0].strip())
                print(f"Created: {intro_path}")

            for i in range(1, len(parts), 2):
                heading = parts[i]
                
                if (i + 1) < len(parts):
                    section_content = parts[i+1]
                else:
                    section_content = ""

                filename = get_filename_from_heading(heading)

                if filename:
                    output_path = os.path.join(output_dir, filename)
                    try:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(heading.strip() + '\n\n')
                            f.write(section_content.strip())
                        print(f"Created: {output_path}")
                    except Exception as e:
                        print(f"Error writing file {output_path}: {e}")
                else:
                    print(f"Warning: Skipping section '{heading.strip()}' (no matching filename)")
        
        print("--- [SPLITTER] FINISHED ---")
        return True

    except Exception as e:
        print(f"--- [SPLITTER] FAILED ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# -----------------------------------------------------------------------------
# MAIN BLOCK (for direct testing only)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("--- RUNNING files_split.py DIRECTLY FOR TESTING ---")
    
    TEST_SESSION_FOLDER = "test_session"
    if os.path.exists(TEST_SESSION_FOLDER):
        run_file_splitter(TEST_SESSION_FOLDER)
    else:
        print(f"Test folder '{TEST_SESSION_FOLDER}' not found.")
        print("Run 'crew_logic.py' first to generate test files.")
