import os
from crewai import Task
from agents import (
    resume_summarizer, # Your resume_summarizer
    resume_extractor,
    job_search_agent,
    job_match_agent,
    interview_search_agent,
    content_analysis_agent,
    question_generator_agent,
    answer_generator_agent
)

# --- Task 1: Resume Extraction (No Change) ---
resume_extraction_task = Task(
    name="Resume Extraction Task",
    description=(
        "Task to extract and summarize resume data into structured JSON format "
        "from the given PDF resume {target_pdf}."
    ),
    expected_output=(
        "A structured JSON object containing: "
        "1) Personal details (name, contact, email), "
        "2) Education history, "
        "3) Work experience, "
        "4) Skills and Projects, "
        "5) Certifications, "
        "6) LinkedIn link and GitHub link if available."
    ),
    agent=resume_extractor,
    verbose=True
)

# --- Task 2: Resume Summary (No Change) ---
resume_summary_task = Task(
    name="Resume Summary Task",
    description = "Task to create a concise and compelling career summary for the candidate based on the structured resume data." \
    "Task to synthesize all structured resume data into a detailed, multi-section Executive Profile. " \
    "This output serves as high-signal metadata extracting Core Specialization, " \
    "Technical Stack, Quantifiable Impact, and Key Leadership/Challenge Areas."
    " and also optionally **Attempt** to scrape the `linkedin_url` and `github_url` (if they exist "
        "in the JSON and they are in correct url format otherwise skip) to find supplemental details optionally.",

    expected_output = "A single, well-crafted career summary text in detailed based on the structured resume data with detailed," \
        "mutli-section executive profile." \
        " If scraping was successful, also integrate key findings from their "
        "LinkedIn profile or GitHub.",
    agent=resume_summarizer,
    context=[resume_extraction_task],
    output_file="candidate_summary.txt",
    verbose=True
)

# --- Task 3: Job Search (No Change) ---
job_search_task = Task(
    name="LinkedIn Fresher Job Search",
    description=(
        "Use LinkedIn to search for the most recent job postings in India "
        "for the role '{target_role}' suitable for freshers with no prior experience. "
        "Return a structured list containing job title, link, snippet/description, and posting details."
    ),
    expected_output="A list (upto 20) of recent LinkedIn fresher job postings matching the target role.",
    agent=job_search_agent,
    verbose=True
)

# --- Task 4: Job Filter (MODIFIED) ---
job_filter_task = Task(
    name="Filter, Rank, and Format Relevant Jobs",
    description=(
        "**CRITICAL STEPS:**\n"
        "1. You will receive two pieces of context: a candidate profile summary as an input variable '{candidate_summary}' AND a list of job postings from the previous step.\n"
        "2. **Analyze the {candidate_summary}** to understand their key skills, technologies, and experience level.\n"
        "3. **For EACH job posting** in the provided list:\n"
        "    a. Extract the Job Title, Company, Location, Description/Snippet, Apply Link, and Posting Date (if available).\n"
        "    b. **Compare** the job's requirements with the candidate's skills and summary.\n"
        "    c. Assign a relevance score (e.g., high, medium, low) based on the match, focusing on fresher/entry-level suitability.\n"
        "4. **Select only the jobs** scored as 'high' relevance. If more than 10, select the top 10.\n"
        "5. **GENERATE FINAL OUTPUT:** Construct the final output string. This string must contain **ONLY** a numbered list of the selected jobs (up to 10). For EACH job, use this EXACT multi-line format:\n"
        "   ```\n" # EXAMPLE ONLY
        "   1. Job Title: [Extracted Job Title]\n"
        "      Company: [Extracted Company Name]\n"
        "      Location: [Extracted Location]\n"
        "      Description: [Extracted Brief Snippet/Description]\n"
        "      Apply Link: [Extracted Apply Link]\n"
        "   \n" 
        "   2. Job Title: [Extracted Job Title]\n"
        "      ...\n"
        "   ```\n" # END EXAMPLE
        "6. **IMPORTANT:** Ensure the final output contains **absolutely nothing** besides the complete numbered list."
    ),
    expected_output=(
        "A markdown file ('recommended_jobs.md') containing ONLY a numbered list of the top (up to 10) relevant jobs. "
        "Each numbered item MUST follow the multi-line format: Job Title:, Company:, Location:, Description:, Apply Link:, followed by a blank line."
    ),
    agent=job_match_agent,
    context=[job_search_task], # This link is FINE (it's inside the same crew)
    output_file="recommended_jobs.md"
)



# --- Task 7: Generate Questions (MODIFIED) ---
# We are REMOVING the context from analyze_content_task.
generate_questions_task = Task(
    name="Generate Tailored Interview Questions",
    description=(
        "**CRITICAL:** Based *ONLY* on the candidate's resume summary (provided as input variable '{candidate_summary}'), generate exactly:\n"
        "- 5 Resume-Based Questions (using the resume summary)\n"
        "- 5 Technical Questions (based on skills in the resume summary)\n"
        "- 5 Behavioral Questions\n"
        "- 5 Technical Scenario-Based Questions (based on projects/skills in the resume summary)\n"
        "Format the output strictly as a markdown file."
    ),
    expected_output=(
        "A markdown file ('interview_questions.md') containing exactly 20 questions, categorized under clear headings. The structure must be:\n\n"
        "## Resume-Based Questions\n"
        "1. [Question 1]\n"
        "2. [Question 2]\n"
        "3. [Question 3]\n"
        "4. [Question 4]\n"
        "5. [Question 5]\n\n"
        "## Technical Questions\n"
        "1. [Question 1]\n"
        "...\n"
        "5. [Question 5]\n\n"
        "## Behavioral Questions\n"
        "1. [Question 1]\n"
        "...\n"
        "5. [Question 5]\n\n"
        "## Technical Scenario-Based Questions\n"
        "1. [Scenario Question 1]\n"
        "...\n"
        "5. [Scenario Question 5]\n\n"
        "**The output file must contain ONLY these sections and questions, with no extra text and without markdown tags.**"
    ),
    agent=question_generator_agent,
    # REMOVED CONTEXT: context=[analyze_content_task, resume_summary_task],
    output_file="interview_questions.md"
)

# --- Task 8: Generate Answers (MODIFIED) ---
generate_answers_task = Task(
    name="Generate Model Answers for Interview Questions",
    description=(
        "You will receive a markdown-formatted list of interview questions "
        "(categorized as Resume-Based, Technical, Behavioral, and Technical Scenario) "
        "and a candidate summary (as input variable '{candidate_summary}').\n"
        "**Your Job:** For **each** question in the list:\n"
        "1. Understand the question's category and intent.\n"
        "2. Formulate a concise, accurate, and relevant model answer.\n"
        "3. For Resume-Based questions, refer to the candidate summary.\n"
        "4. For Technical/Scenario questions, refer to the interview process summary context for expected topics/approaches.\n"
        "5. For Behavioral questions, provide a structured answer (e.g., using STAR method briefly).\n\n"
        "**Format** the final output as a markdown file, interleaving the questions and answers."
    ),
    expected_output=(
        "A markdown file ('questions_and_answers.md') containing all the original questions, each followed by its generated model answer. Use clear formatting:\n\n"
        "## Resume-Based Questions\n\n"
        "**1. [Question 1]**\n"
        "*Model Answer:* [Generated answer for Q1]\n\n"
        "**2. [Question 2]**\n"
        "*Model Answer:* [Generated answer for Q2]\n"
        "...\n\n"
        "## Technical Questions\n\n"
        "**1. [Question 1]**\n"
        "*Model Answer:* [Generated answer for Q1]\n"
        "...\n\n"
        "## Behavioral Questions\n\n"
        "**1. [Question 1]**\n"
        "*Model Answer:* [Generated answer using STAR principles briefly]\n"
        "...\n\n"
        "## Technical Scenario-Based Questions\n\n"
        "**1. [Scenario Question 1]**\n"
        "*Model Answer:* [Generated answer outlining approach/solution]\n"
        "...\n\n"
        "**The output file must contain ONLY this structure.**"
    ),
    agent=answer_generator_agent,
    context=[generate_questions_task], # <-- MODIFIED: Only depends on questions
    output_file="questions_and_answers.md"
)

