import gradio as gr
import os
import time
import shutil
import json
import threading # To run CrewAI without freezing GUI
import traceback
import re

# --- Library Imports for Features ---
from gtts import gTTS              # For Text-to-Speech
import speech_recognition as sr  # For Speech-to-Text (using CMU Sphinx offline)
import pypdf                   # For reading PDF text for evaluation context
import plotly.graph_objects as go # For plotting
import pandas as pd             # For data manipulation for plots


# --- Import your refactored functions ---
try:
    from crew import run_smart_career_crew
    print("Successfully imported run_smart_career_crew from crew.py")
except ImportError:
    print("ERROR: Could not import run_smart_career_crew from crew.py. Make sure crew.py is refactored.")
    # Define a dummy function to allow Gradio to load
    def run_smart_career_crew(pdf_path: str, role: str, company: str) -> bool:
        print("ERROR: DUMMY run_smart_career_crew called. Refactor crew.py!")
        return False

try:
    from split_files import run_file_splitter
    print("Successfully imported run_file_splitter from split_files.py")
except ImportError:
    print("ERROR: Could not import run_file_splitter from split_files.py. Make sure split_files.py is refactored.")
    def run_file_splitter() -> bool:
        print("ERROR: DUMMY run_file_splitter called. Refactor split_files.py!")
        return False

# --- LLM Configuration (for Evaluation) ---
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm_gemini_pro = ChatGoogleGenerativeAI(
        model=os.getenv("MODEL_EVAL"), # Default model if env var not set
        google_api_key=os.getenv("GEMINI_API_KEY_1"),
        temperature=0.5,
    )
    print("Gemini Pro LLM for evaluation initialized.")
except ImportError:
    print("ERROR: Could not import ChatGoogleGenerativeAI. Run 'pip install langchain-google-genai'")
    llm_gemini_pro = None # App will fail later if LLM is needed
except Exception as e:
    print(f"ERROR: Failed to initialize Gemini Pro LLM: {e}")
    llm_gemini_pro = None


# --- Configuration ---
UPLOAD_FOLDER = 'uploads_gradio'
QUESTIONS_FOLDER = 'questions_folder'
ANSWERS_FOLDER = 'answers_folder' # Contains Q&A pairs
RECOMMENDED_JOBS_FILE = 'recommended_jobs.md'
TTS_AUDIO_FILE = "question_audio.mp3" # Temp file for TTS output

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Helper Functions ---

def extract_text_from_pdf(pdf_path):
    """Extracts raw text content from a PDF file."""
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or "" # Add fallback for empty pages
        print(f"Extracted text from {pdf_path}")
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return f"Error: Could not read resume text - {e}"

def load_questions_for_round(round_type):
    """Loads appropriate questions from the questions_folder."""
    print(f"Loading questions for round: {round_type}")
    questions = []
    files_to_load = []
    # Use lowercase for reliable matching
    round_type_lower = round_type.lower()
    if "technical" in round_type_lower:
        files_to_load = ["technical.md", "scenario_based.md", "resume_based.md"]
    elif "behavioral" in round_type_lower:
        files_to_load = ["behavioural.md"] # Corrected spelling
    elif "general" in round_type_lower or "mixed" in round_type_lower:
        files_to_load = ["technical.md", "scenario_based.md", "resume_based.md", "behavioural.md"] # Corrected spelling

    if not files_to_load:
        print(f"Warning: No files determined for round type '{round_type}'")
        return []

    for filename in files_to_load:
        filepath = os.path.join(QUESTIONS_FOLDER, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find questions assuming format "## Heading\n\n1. Question\n2. Question..."
                # More robust parsing might be needed
                potential_questions = re.findall(r"^\d+\.\s*(.*)", content, re.MULTILINE)
                if not potential_questions: # Fallback for bullet points maybe?
                     potential_questions = re.findall(r"^\*\s*(.*)", content, re.MULTILINE)

                if potential_questions:
                    # Remove the heading itself if captured accidentally
                    cleaned_questions = [q.strip() for q in potential_questions if not q.strip().startswith("#")]
                    questions.extend(cleaned_questions)
                    print(f"Loaded {len(cleaned_questions)} questions from {filename}")
                else:
                    print(f"Warning: No numbered/bulleted questions found in {filename}")

        except FileNotFoundError:
            print(f"Warning: Question file not found: {filepath}")
        except Exception as e:
            print(f"Error reading or parsing {filepath}: {e}")

    # Select ~5 questions (simple shuffle and take 5)
    import random
    random.shuffle(questions)
    selected_questions = questions[:5]
    print(f"Selected {len(selected_questions)} questions: {selected_questions}")
    return selected_questions

# --- TTS Function ---
def read_question_aloud(question_text):
    """Generates audio file from text and returns its path."""
    if not question_text:
        return None
    try:
        tts = gTTS(text=question_text, lang='en')
        tts.save(TTS_AUDIO_FILE)
        print(f"Generated TTS audio for: {question_text[:30]}...")
        return TTS_AUDIO_FILE
    except Exception as e:
        print(f"Error generating TTS: {e}")
        return None

# --- STT Function ---
# Option 1: Using SpeechRecognition (offline with CMU Sphinx - requires setup)
# Needs: pip install SpeechRecognition pocketsphinx
# NOTE: Accuracy might be limited, especially with accents/noise.
recognizer = sr.Recognizer()
def transcribe_audio_sphinx(audio_filepath):
    """Transcribes audio file to text using CMU Sphinx (offline)."""
    if not audio_filepath:
        return ""
    try:
        with sr.AudioFile(audio_filepath) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_sphinx(audio_data)
            print(f"STT (Sphinx) result: {text}")
            return text
    except sr.UnknownValueError:
        print("Sphinx could not understand audio")
        return "Audio unclear or silent."
    except sr.RequestError as e:
        print(f"Sphinx error; {e}")
        return f"Error during speech recognition: {e}"
    except Exception as e:
        print(f"Error during STT: {e}")
        return f"Error processing audio: {e}"


# --- Choose ONE STT function ---
transcribe_audio = transcribe_audio_sphinx # Defaulting to Sphinx (offline)


# --- Evaluation Function (Modified Context) ---
def evaluate_answers(questions_list, answers_list, resume_text): # Takes resume_text now
    """Evaluates each answer against its question using Gemini Pro."""
    if llm_gemini_pro is None:
        return [{"question": q, "answer": a, "error": "LLM not initialized"} for q, a in zip(questions_list, answers_list)]

    evaluation_results = []
    # Use only resume text as primary context
    full_context = f"Candidate Resume Information:\n```\n{resume_text}\n```"

    print("\n--- Starting Evaluation ---")
    for i, question in enumerate(questions_list):
        answer = answers_list[i] if i < len(answers_list) and answers_list[i] else "No answer provided." # Handle empty answers

        prompt = f"""
        **Context:**
        {full_context}

        **Interview Question:**
        "{question}"

        **Candidate's Answer:**
        "{answer}"

        **Evaluation Task:**
        Evaluate the candidate's answer based ONLY on the provided context and the question asked. Provide scores (1-5), brief explanations for each score, and 1-2 actionable improvement suggestions based on these criteria:
        1.  **Relevance:** How directly does the answer address the question using relevant information from the resume context if applicable?
        2.  **Technical Depth (if applicable):** How accurate and detailed is the technical information, considering standard expectations for the role mentioned in the context (if any)? (Score null if not a technical question).
        3.  **Clarity:** How clear, concise, and well-structured is the answer?
        4.  **Confidence:** Does the language used project confidence?

        **Output Format (Strict JSON):**
        {{
          "scores": {{
            "relevance": <score_int>,
            "technical_depth": <score_int_or_null>,
            "clarity": <score_int>,
            "confidence": <score_int>
          }},
          "explanations": {{
            "relevance": "<explanation_string>",
            "technical_depth": "<explanation_string_or_null>",
            "clarity": "<explanation_string>",
            "confidence": "<explanation_string>"
          }},
          "suggestions": "<overall_suggestions_string>"
        }}
        """

        try:
            print(f"Evaluating Q{i+1}: {question[:50]}...")
            response = llm_gemini_pro.invoke(prompt)
            llm_output_text = response.content
            # Clean potential markdown/code block formatting
            cleaned_json_text = llm_output_text.strip().lstrip('```json').rstrip('```').strip()

            evaluation_data = json.loads(cleaned_json_text)

            evaluation_results.append({
                "question": question,
                "answer": answer,
                "scores": evaluation_data.get("scores", {}),
                "explanations": evaluation_data.get("explanations", {}),
                "suggestions": evaluation_data.get("suggestions", "No suggestions provided.")
            })
            print(f"-> Evaluation for Q{i+1} successful.")

        except json.JSONDecodeError as json_err:
             print(f"Error decoding LLM JSON response for Q{i+1}: {json_err}")
             print(f"LLM Raw Output:\n{llm_output_text}\n")
             evaluation_results.append({
                "question": question, "answer": answer,
                "error": f"Failed to parse evaluation from LLM. Raw output logged to console."})
        except Exception as e:
            print(f"Error calling LLM for Q{i+1}: {e}")
            traceback.print_exc() # Print full traceback
            evaluation_results.append({
                "question": question, "answer": answer,
                "error": f"Failed to evaluate: {e}"})

    print("--- Evaluation Finished ---")
    return evaluation_results

# --- Dashboard Creation Function ---
def create_dashboard_ui(eval_results):
    """Generates Gradio components for the dashboard based on evaluation results."""
    # This function now returns a list of components to update the dashboard area
    components_to_update = []

    if not eval_results:
        components_to_update.append(gr.Markdown("Evaluation failed or no results available."))
        return components_to_update

    # --- Calculate Overall Stats ---
    # (Same calculation logic as before)
    avg_scores = {'relevance': 0, 'technical_depth': 0, 'clarity': 0, 'confidence': 0}
    valid_counts = {'relevance': 0, 'technical_depth': 0, 'clarity': 0, 'confidence': 0}
    all_suggestions = []
    num_questions = len(eval_results)
    successful_evals = 0

    for result in eval_results:
        if "scores" in result and isinstance(result["scores"], dict): # Check scores exist and is dict
            successful_evals += 1
            for key, score in result["scores"].items():
                if key in avg_scores and isinstance(score, (int, float)): # Check key exists and score is valid
                    avg_scores[key] += score
                    valid_counts[key] += 1
            if result.get("suggestions"):
                # Use markdown list for suggestions
                all_suggestions.append(f"* **For Q: \"{result['question'][:60]}...\"**\n    * {result['suggestions']}")

    for key in avg_scores:
        if valid_counts[key] > 0:
            avg_scores[key] /= valid_counts[key]

    overall_average = sum(v for k, v in avg_scores.items() if valid_counts[k] > 0) / sum(1 for k, v in avg_scores.items() if valid_counts[k] > 0) if sum(valid_counts.values()) > 0 else 0


    # --- Create UI Components ---
    components_to_update.append(gr.Markdown(f"## Evaluation Summary ({successful_evals}/{num_questions} Questions Evaluated)"))
    components_to_update.append(gr.Number(value=round(overall_average, 1), label="Overall Average Score (out of 5)"))

    # Plotly Donut Chart
    try:
        labels = [k.replace('_', ' ').title() for k, v in avg_scores.items() if valid_counts[k] > 0] # Only plot valid criteria
        values = [round(avg_scores[k], 1) for k, v in avg_scores.items() if valid_counts[k] > 0]
        if labels and values: # Only plot if there's data
            fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4,
                                            textinfo='label+value', pull=[0.05] * len(labels))])
            fig_donut.update_layout(title_text='Average Scores by Criteria', showlegend=False, margin=dict(t=50, b=0, l=0, r=0))
            components_to_update.append(gr.Plot(figure=fig_donut, label="Average Score Distribution"))
        else:
            components_to_update.append(gr.Markdown("*Not enough valid scores to generate chart.*"))
    except Exception as plot_err:
        print(f"Error creating donut chart: {plot_err}")
        components_to_update.append(gr.Markdown(f"*Error generating score chart: {plot_err}*"))


    # Accordion for Detailed Feedback
    detailed_feedback = []
    for i, result in enumerate(eval_results):
        feedback_md = f"### Question {i+1}\n**Question:** {result['question']}\n\n"
        feedback_md += f"**Your Answer:**\n```\n{result.get('answer', 'N/A')}\n```\n\n"
        if "scores" in result and isinstance(result["scores"], dict):
            feedback_md += "**Scores:**\n"
            for k, v in result["scores"].items():
                 feedback_md += f"* {k.replace('_', ' ').title()}: {v if v is not None else 'N/A'}\n"
            feedback_md += "\n**Explanations:**\n"
            for k, v in result.get("explanations", {}).items():
                 feedback_md += f"* {k.replace('_', ' ').title()}: {v if v is not None else 'N/A'}\n"
            feedback_md += f"\n**Suggestions:** {result.get('suggestions', 'N/A')}\n"
        else:
            feedback_md += f"**Error:** {result.get('error', 'Unknown evaluation error.')}\n"
        detailed_feedback.append(gr.Markdown(feedback_md))

    components_to_update.append(gr.Accordion("Detailed Feedback per Question", open=False))
    # This is tricky in Gradio - dynamically adding tabs isn't straightforward.
    # We'll just put all markdown inside the accordion for now.
    # To put components inside, they need to be defined within a 'with Accordion:' block,
    # which we can't easily do dynamically after the fact.
    # A simpler approach: create one large markdown string.
    detailed_md_string = "\n\n---\n\n".join([md.value for md in detailed_feedback]) # .value gets the markdown content
    components_to_update.append(gr.Markdown(value=detailed_md_string))


    # Consolidated Suggestions
    components_to_update.append(gr.Markdown("## Consolidated Improvement Suggestions"))
    suggestions_md = "\n".join(all_suggestions) if all_suggestions else "No specific improvement suggestions generated."
    components_to_update.append(gr.Markdown(suggestions_md))

    # Recommended Jobs
    components_to_update.append(gr.Markdown("---"))
    jobs_button = gr.Button("View Recommended Jobs")
    jobs_display = gr.Markdown(visible=False) # Hidden initially
    components_to_update.append(jobs_button)
    components_to_update.append(jobs_display)

    return components_to_update # Return list of components/updates


# --- Main Gradio App Structure (incorporating components) ---
with gr.Blocks(theme=gr.themes.Glass(), title="AI Interview Practice") as demo:
    gr.Markdown("# AI Interview Practice Session")

    # --- State Management ---
    shared_state = gr.State({
        "questions": [],
        "current_q_index": 0,
        "answers": [],
        "resume_text": "", # Store raw resume text
        "job_role": "",
        "company": "",
        "eval_results": None,
        "pdf_path": None # Store path to saved PDF
    })

    # --- UI Sections ---
    with gr.Column(visible=True) as setup_ui:
        gr.Markdown("## Your Details")
        # ... (role_input, company_input, resume_input, round_type_input as before) ...
        role_input = gr.Textbox(label="Job Role", placeholder="e.g., Software Engineer")
        company_input = gr.Textbox(label="Company", placeholder="e.g., Google")
        resume_input = gr.File(label="Upload Resume (PDF only)", file_types=[".pdf"])
        round_type_input = gr.Radio(["Technical", "Behavioral", "General (Mixed)"], label="Select Round Type", value="General (Mixed)")
        start_button = gr.Button("Start Interview Practice", variant="primary")
        setup_error_output = gr.Markdown(value="", visible=False)

    with gr.Column(visible=False) as interview_ui:
        gr.Markdown("## Interview Session")
        interview_progress = gr.Markdown("Question 1 of X") # Moved up
        question_display = gr.Textbox(label="Question", interactive=False, lines=3)
        with gr.Row():
            read_question_btn = gr.Button("🔊 Read Question")
            audio_output_display = gr.Audio(label="Listen", type="filepath", interactive=False, autoplay=True) # Autoplay TTS
        gr.Markdown("### Your Answer")
        with gr.Row():
            audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Record Answer (Optional)")
            text_input = gr.Textbox(label="Or Type Answer Here", lines=5, placeholder="Type your answer or record using the microphone above.")
        with gr.Row():
            next_button = gr.Button("Submit & Next Question", variant="primary")
            end_button = gr.Button("End Interview & Evaluate")

    with gr.Column(visible=False) as dashboard_ui:
        gr.Markdown("## Evaluation Dashboard")
        # This will hold the dynamically generated dashboard components
        dashboard_components_list = [] # We will update this list


    # --- Event Handling Logic ---

    # Start Interview Flow (mostly same, but adds resume text extraction)
    def start_interview_flow(role, company, resume_file_obj, round_type, current_state):
        # ... (validation as before) ...
        if not all([role, company, resume_file_obj, round_type]):
             return {setup_error_output: gr.update(value="## Error\nPlease fill in all fields and upload a resume.", visible=True)}

        # 1. Save uploaded file locally
        pdf_path = os.path.join(UPLOAD_FOLDER, f"resume_{int(time.time())}.pdf")
        try:
            shutil.copyfile(resume_file_obj.name, pdf_path)
            print(f"Resume copied to: {pdf_path}")
            current_state["pdf_path"] = pdf_path # Store path in state
        except Exception as e:
            # ... (error handling) ...
             return {setup_error_output: gr.update(value=f"## Error\nCould not save resume: {e}", visible=True)}

        # 1b. Extract Resume Text for evaluation context
        current_state["resume_text"] = extract_text_from_pdf(pdf_path)
        if "Error:" in current_state["resume_text"]:
             # Handle error - maybe warn user but continue?
             print(f"Warning: Could not extract resume text: {current_state['resume_text']}")
             # Decide if this is critical - for evaluation, it likely is.
             return {setup_error_output: gr.update(value=f"## Error\n{current_state['resume_text']}", visible=True)}


        current_state["job_role"] = role
        current_state["company"] = company

        # --- Show loading ---
        yield { # Yield updates to show progress before long task
            setup_error_output: gr.update(value="Processing resume and generating questions... Please wait.", visible=True),
            start_button: gr.update(interactive=False) # Disable button
        }

        # 2. Run CrewAI in a thread
        crew_success = False
        def crew_task():
            nonlocal crew_success
            crew_success = run_smart_career_crew(pdf_path, role, company)
        crew_thread = threading.Thread(target=crew_task)
        crew_thread.start()
        crew_thread.join() # Wait for crew to finish

        if not crew_success:
             # ... (error handling) ...
             yield {
                 setup_error_output: gr.update(value="## Error\nFailed to run backend processing (CrewAI). Check server logs.", visible=True),
                 start_button: gr.update(interactive=True) # Re-enable button
             }
             return # Stop execution


        # 3. Run File Splitter
        split_success = run_file_splitter()
        if not split_success:
             # ... (error handling) ...
              yield {
                 setup_error_output: gr.update(value="## Error\nFailed to run backend processing (File Splitter). Check server logs.", visible=True),
                 start_button: gr.update(interactive=True)
             }
              return


        # 4. Load questions
        selected_questions = load_questions_for_round(round_type)
        if not selected_questions:
             # ... (error handling) ...
              yield {
                 setup_error_output: gr.update(value=f"## Error\nCould not load questions for round type '{round_type}'. Check '{QUESTIONS_FOLDER}'.", visible=True),
                 start_button: gr.update(interactive=True)
             }
              return


        # 5. Update state
        current_state["questions"] = selected_questions
        current_state["current_q_index"] = 0
        current_state["answers"] = [""] * len(selected_questions)

        # 6. Update UI
        first_q = selected_questions[0]
        total_q = len(selected_questions)
        yield {
            setup_ui: gr.update(visible=False),
            interview_ui: gr.update(visible=True),
            dashboard_ui: gr.update(visible=False),
            question_display: gr.update(value=first_q),
            interview_progress: gr.update(value=f"Question 1 of {total_q}"),
            start_button: gr.update(interactive=True), # Re-enable button
            shared_state: current_state
        }

    # TTS Handler
    def handle_read_question(question_text):
        audio_path = read_question_aloud(question_text)
        # Update the audio component to play the generated file
        # Use None if generation failed to clear previous audio
        return gr.update(value=audio_path, label="Listen" if audio_path else "Error generating audio")

    # Submit & Next Handler
    def process_answer_and_next(audio_answer_path, text_answer, current_state):
        answer_text = text_answer
        if audio_answer_path:
             print(f"Attempting STT for: {audio_answer_path}")
             try:
                 # Use the chosen STT function
                 stt_result = transcribe_audio(audio_answer_path)
                 print(f"STT Result: {stt_result}")
                 # Prioritize STT result if available, otherwise use text input
                 answer_text = stt_result if stt_result and stt_result != "Audio unclear or silent." else text_answer
             except Exception as e:
                  print(f"STT Error: {e}")
                  answer_text = f"(Error processing audio) {text_answer}" # Combine with text

        q_index = current_state["current_q_index"]
        current_state["answers"][q_index] = answer_text.strip() # Store cleaned answer
        print(f"Stored answer for Q{q_index+1}: {answer_text[:100]}...")

        current_state["current_q_index"] += 1
        next_q_index = current_state["current_q_index"]
        total_q = len(current_state["questions"])

        updates = { # Prepare updates dictionary
             audio_input: gr.update(value=None), # Clear audio input
             text_input: gr.update(value=""),     # Clear text input
             shared_state: current_state
        }

        if next_q_index >= total_q:
            print("Last question answered. Triggering evaluation...")
            # --- Trigger Evaluation ---
            yield {**updates, interview_progress: gr.update(value="Generating Evaluation...")} # Show progress

            eval_results = evaluate_answers(
                current_state["questions"],
                current_state["answers"],
                current_state["resume_text"] # Pass raw resume text
            )
            current_state["eval_results"] = eval_results

            # --- Generate and Show Dashboard ---
            # IMPORTANT: Gradio's way to dynamically update layout is limited.
            # Instead of returning components, we'll return updates for specific placeholders.
            # We need placeholders in the dashboard_ui definition. Let's redefine it slightly.

            # We can't easily return a whole new layout. We return updates for predefined components.
            # Let's try updating a single Markdown component with the whole dashboard content.

            dashboard_md = generate_dashboard_markdown(eval_results, current_state) # New helper function

            updates.update({
                interview_ui: gr.update(visible=False),
                dashboard_ui: gr.update(visible=True),
                # We update the *value* of the placeholder markdown, not the structure
                dashboard_placeholder_md: gr.update(value=dashboard_md)
            })

        else:
            # Load next question
            next_q = current_state["questions"][next_q_index]
            updates.update({
                question_display: gr.update(value=next_q),
                interview_progress: gr.update(value=f"Question {next_q_index + 1} of {total_q}")
            })

        yield updates # Use yield for Gradio updates

    # End Interview Early Handler
    def end_interview_early(current_state):
         print("Ending interview early. Triggering evaluation...")
         yield {interview_progress: gr.update(value="Generating Evaluation...")} # Show progress

         eval_results = evaluate_answers(
             current_state["questions"],
             current_state["answers"], # Evaluate based on answers given so far
             current_state["resume_text"]
         )
         current_state["eval_results"] = eval_results

         dashboard_md = generate_dashboard_markdown(eval_results, current_state) # New helper function

         yield {
             interview_ui: gr.update(visible=False),
             dashboard_ui: gr.update(visible=True),
             dashboard_placeholder_md: gr.update(value=dashboard_md),
             shared_state: current_state
         }

    # Helper function to generate dashboard markdown (simpler dynamic update)
    def generate_dashboard_markdown(eval_results, current_state):
        if not eval_results: return "## Evaluation Dashboard\nEvaluation failed or no results available."

        # --- Calculate Stats (same as before) ---
        avg_scores = {'relevance': 0, 'technical_depth': 0, 'clarity': 0, 'confidence': 0}
        valid_counts = {'relevance': 0, 'technical_depth': 0, 'clarity': 0, 'confidence': 0}
        all_suggestions = []
        num_questions = len(eval_results)
        successful_evals = 0
        # ... (rest of calculation logic) ...
        for result in eval_results:
            if "scores" in result and isinstance(result["scores"], dict):
                successful_evals += 1
                for key, score in result["scores"].items():
                    if key in avg_scores and isinstance(score, (int, float)):
                        avg_scores[key] += score
                        valid_counts[key] += 1
                if result.get("suggestions"):
                    all_suggestions.append(f"* **For Q: \"{result['question'][:60]}...\"**\n    * {result['suggestions']}")

        for key in avg_scores:
            if valid_counts[key] > 0: avg_scores[key] /= valid_counts[key]
        overall_average = sum(v for k, v in avg_scores.items() if valid_counts[k] > 0) / sum(1 for k, v in avg_scores.items() if valid_counts[k] > 0) if sum(valid_counts.values()) > 0 else 0


        # --- Build Markdown String ---
        md = f"## Evaluation Summary ({successful_evals}/{num_questions} Questions Evaluated)\n\n"
        md += f"**Overall Average Score:** {overall_average:.1f} / 5\n\n"

        # Note: Can't embed interactive plots directly in Markdown easily.
        # We can show average scores as text.
        md += "**Average Scores by Criteria:**\n"
        for k, v in avg_scores.items():
            if valid_counts[k] > 0:
                 md += f"* {k.replace('_', ' ').title()}: {v:.1f}\n"
        md += "\n---\n" # Separator

        md += "### Detailed Feedback per Question\n"
        for i, result in enumerate(eval_results):
            md += f"\n**Question {i+1}:** {result['question']}\n\n"
            md += f"**Your Answer:**\n```\n{result.get('answer', 'N/A')}\n```\n\n"
            if "scores" in result and isinstance(result["scores"], dict):
                md += "**Scores:**\n"
                for k, v in result["scores"].items():
                    md += f"* {k.replace('_', ' ').title()}: {v if v is not None else 'N/A'}\n"
                md += "\n**Explanations:**\n"
                for k, v in result.get("explanations", {}).items():
                    md += f"* {k.replace('_', ' ').title()}: {v if v is not None else 'N/A'}\n"
                md += f"\n**Suggestions:** {result.get('suggestions', 'N/A')}\n"
            else:
                md += f"**Error:** {result.get('error', 'Unknown evaluation error.')}\n"
            md += "\n---\n"

        md += "\n## Consolidated Improvement Suggestions\n\n"
        suggestions_text = "\n".join(all_suggestions) if all_suggestions else "No specific improvement suggestions generated."
        md += suggestions_text + "\n\n"

        # Add Recommended Jobs Content
        md += "---\n## Recommended Jobs\n"
        try:
            with open(RECOMMENDED_JOBS_FILE, 'r', encoding='utf-8') as f:
                jobs_content = f.read()
            md += jobs_content if jobs_content.strip() else "*No recommended jobs found.*"
        except FileNotFoundError:
            md += "*Recommended jobs file not found.*"
        except Exception as e:
            md += f"*Error loading recommended jobs: {e}*"

        return md


    # --- Redefine Dashboard UI with Placeholder ---
    with gr.Column(visible=False) as dashboard_ui:
         dashboard_placeholder_md = gr.Markdown("Evaluation results will appear here.") # Single placeholder


    # --- Wire Buttons ---
    start_button.click(
        fn=start_interview_flow,
        inputs=[role_input, company_input, resume_input, round_type_input, shared_state],
        outputs=[
            setup_ui, interview_ui, dashboard_ui, question_display, interview_progress,
            start_button, # Keep button interactive state update
            setup_error_output, shared_state
        ],
        show_progress="full" # Show Gradio's progress indicator
    )

    read_question_btn.click(
        fn=handle_read_question,
        inputs=[question_display],
        outputs=[audio_output_display]
    )

    next_button.click(
        fn=process_answer_and_next,
        inputs=[audio_input, text_input, shared_state],
        outputs=[
            question_display, interview_progress, audio_input, text_input,
            interview_ui, dashboard_ui, # For potential UI switch on last question
            dashboard_placeholder_md, # For potential update on last question
            shared_state
        ],
         show_progress="minimal"
    )

    end_button.click(
        fn=end_interview_early,
        inputs=[shared_state],
        outputs=[
            interview_ui, dashboard_ui, dashboard_placeholder_md, shared_state
        ],
         show_progress="full"
    )

# --- Launch the App ---
if __name__ == "__main__":
    demo.launch(debug=True, share=False) # share=False keeps it local