import os
import re

# 1. DEFINE YOUR SOURCE FILES AND OUTPUT FOLDERS
#    (The script assumes 'questions.md' and 'questions_with_answers.md' 
#     are in the same directory as this script)
source_to_output_map = {
    "interview_questions.md": "questions_folder",
    "questions_and_answers.md": "answers_folder"
}

# 2. DEFINE YOUR SECTION MAPPING
#    This maps a keyword in the heading (lowercase) to a filename.
#    This is the most important part to get right.
section_mapping = {
    "resume-based questions": "resume_based.md",
    "technical questions": "technical.md",
    "behavioral questions": "behavioural.md",
    "technical scenario-based questions": "scenario_based.md"
}

def get_filename_from_heading(heading_line):
    """Finds the matching filename for a given heading line."""
    # Cleans the heading: "## Technical Questions" -> "technical questions"
    heading_text = heading_line.strip().lstrip('#').strip().lower()
    
    for key, filename in section_mapping.items():
        if key in heading_text:
            return filename
    return None



def run_file_splitter() -> bool:
    """
    Reads source markdown files, splits them by headings, and saves
    the content to new files. Returns True on success, False on failure.
    """
    try:
        heading_regex = re.compile(r'(^[ \t]*#+[ \t].*$)', re.MULTILINE)

        for source_file, output_dir in source_to_output_map.items():
            print(f"\n--- Processing: {source_file} ---")

            # 3. Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # 4. Read the source file
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                print(f"Error: Source file '{source_file}' not found. Skipping.")
                continue

            # 5. Split the content by the headings
            # This creates a list like: ['(intro content)', '## Heading 1', '(content 1)', '## Heading 2', '(content 2)', ...]
            parts = heading_regex.split(content)

            if not parts:
                print("No content found.")
                continue

            # Handle any content *before* the first heading
            if parts[0].strip():
                print(f"Found content before first heading, saving as intro.md")
                intro_path = os.path.join(output_dir, "intro.md")
                with open(intro_path, 'w', encoding='utf-8') as f:
                    f.write(parts[0].strip())

            # 6. Process the rest of the parts in pairs (heading, content)
            for i in range(1, len(parts), 2):
                heading = parts[i]
                
                # Check if there's content after this heading
                if (i + 1) < len(parts):
                    section_content = parts[i+1]
                else:
                    section_content = "" # No content after the last heading

                # 7. Find the target filename from our mapping
                filename = get_filename_from_heading(heading)

                if filename:
                    output_path = os.path.join(output_dir, filename)
                    
                    # 8. Write the new file
                    try:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(heading.strip() + '\n\n') # Write the heading
                            f.write(section_content.strip())     # Write the content
                        print(f"Created: {output_path}")
                    except Exception as e:
                        print(f"Error writing file {output_path}: {e}")
                else:
                    print(f"Warning: Skipping section '{heading.strip()}' (no matching filename in section_mapping)")
            print("File splitting completed successfully.")
            return True
    except Exception as e:
        print(f"Error during file splitting: {e}")
        import traceback
        traceback.print_exc()
        return False



# Keep this block if you want to run split_files.py directly
if __name__ == "__main__":
    run_file_splitter()