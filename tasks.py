from crewai import Task
from tools import pdftool, serper_tool, job_search_tool
from agents import (resume_summarizer,
                    resume_extractor,
                    job_search_agent,
                    job_match_agent,
                    interview_search_agent,
                    content_analysis_agent,
                    question_generator_agent,
                    answer_generator_agent
                    )

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

job_search_task = Task(
    name="LinkedIn Fresher Job Search",
    description=(
        "Use LinkedIn to search for the most recent job postings in India "
        "for the role '{target_role}' suitable for freshers with no prior experience. "
        "Return a structured list containing job title, link, snippet/description, and posting details."
    ),
    expected_output="A list (upto 20) of recent LinkedIn fresher job postings matching the target role.",
    agent=job_search_agent,
    tools=[job_search_tool]
)

"""
job_filter_task = Task(
    name="Filter and Rank Jobs",
    description=(
        "From the provided job listings and the candidate's profile summary, "
        "identify and rank most relevant LinkedIn fresher jobs "
        "based on skill and role match. Format the final output as a markdown file "
        "containing job title, company, location, brief description, and apply link and no extra information should be saved in the markdownfile"
        "except the list of job title, company, location, brief description, and apply link."
    ),
    expected_output="A markdown file ('recommended_jobs.md') with job posts from the provided listings with numbering, " \
        "containing job title, company, location, brief description, and apply link as clean markdown file without markdown tags and no other information otherthan job lists in the markdown files.",
    agent=job_match_agent,
    context=[job_search_task,resume_summary_task],
    output_file="recommended_jobs.md"
)
"""

from crewai import Task


job_filter_task = Task(
    name="Filter, Rank, and Format Relevant Jobs",
    description=(
        "**CRITICAL STEPS:**\n"
        "1. Receive context: candidate summary and job postings list.\n"
        "2. Analyze candidate summary for skills/experience.\n"
        "3. For EACH job posting: Extract details (Title, Company, Location, Description, Link) and internally assess relevance (high/medium/low) for a fresher based on skills/role match.\n"
        "4. Select ONLY the jobs assessed as 'high' relevance (max 10).\n"
        "5. **GENERATE FINAL OUTPUT:** Construct the final output string. This string must contain **ONLY** a numbered list of the selected jobs (up to 10). For EACH job in the list, use this EXACT multi-line format:\n"
        "   ```\n" # EXAMPLE ONLY - DO NOT INCLUDE ``` IN OUTPUT
        "   1. Job Title: [Extracted Job Title]\n"
        "      Company: [Extracted Company Name]\n"
        "      Location: [Extracted Location]\n"
        "      Description: [Extracted Brief Snippet/Description]\n"
        "      Apply Link: [Extracted Apply Link]\n"
        "   \n" # Blank line REQUIRED between entries
        "   2. Job Title: [Extracted Job Title]\n"
        "      Company: [Extracted Company Name]\n"
        "      ...\n"
        "   ```\n" # END EXAMPLE
        "6. **IMPORTANT:** Ensure the final output contains **absolutely nothing** besides the complete numbered list formatted as described above. Do not include any introductory sentences, concluding remarks, explanations, 'Thought:' sections, or markdown code block formatting (like ```) surrounding the list." # Relaxed this instruction slightly
    ),
    expected_output=(
        "A markdown file ('recommended_jobs.md') containing ONLY a numbered list of the top (upto 10) relevant jobs. "
        "Each numbered item MUST follow the multi-line format: Job Title:, Company:, Location:, Description:, Apply Link:, followed by a blank line. "
        "The file must contain absolutely nothing else before or after the numbered list entries." # Slightly rephrased
    ),
    agent=job_match_agent,
    context=[job_search_task, resume_summary_task],
    output_file="recommended_jobs.md"
)

find_urls_task = Task(
    name="Find Protected-Site Interview URLs",
    description=(
        "Use the search tool to find the most relevant interview experience "
        "pages for {target_company} and {target_role} "
        "from 'GeeksforGeeks', 'Glassdoor', and 'InterviewBit'."
    ),
    expected_output=(
        "A list of 3-5 high-quality, relevant URLs from the target sites "
        "(GeeksforGeeks, Glassdoor, InterviewBit)."
    ),
    agent=interview_search_agent,
)


analyze_content_task = Task(
    name="Scrape and Analyze Interview Content",
    description=(
        "Scrape and analyze interview experience pages for {target_role} at {target_company}. "
        "Take only the first 2 URLs from the provided list. After scraping, remove HTML tags, ads, and irrelevant links. "
        "Combine the meaningful text and identify:\n"
        "- Key technical and behavioral question categories.\n"
        "- Common topics or repeated questions.\n"
        "- At least 5–10 actual example questions.\n"
        "Summarize everything into a detailed markdown output."
    ),
    expected_output=(
        "A structured markdown summary including:\n"
        "### Technical Topics\n"
        "- topic1\n"
        "- topic2\n"
        "### Behavioral Questions\n"
        "- question1\n"
        "### Example Questions\n"
        "- example1\n"
        "- example2\n"
        "The summary should be clear, detailed, and usable as context for generating mock interviews and should contain the stuctured multi-section summary."
    ),
    agent=content_analysis_agent,
    context=[find_urls_task],
    output_file="interview_info_summary.md"
)




generate_questions_task = Task(
    name="Generate Tailored Interview Questions",
    description=(
        "**CRITICAL:** Based on the provided context (interview process summary for {target_company} {target_role} AND the candidate's resume summary), generate exactly:\n"
        "1.  **5 Resume-Based Questions:** Directly probe details, projects, or experiences mentioned in the candidate's summary.\n"
        "2.  **5 Technical Questions:** Cover key technical topics identified in the interview process summary (e.g., specific data structures, algorithms, system design concepts relevant to {target_role}).\n"
        "3.  **5 Behavioral Questions:** Address common behavioral competencies mentioned (e.g., teamwork, problem-solving, leadership).\n"
        "4.  **5 Technical Scenario-Based Questions:** Present realistic technical problems or situations related to the {target_role} and topics from the summary, requiring the candidate to outline an approach or solution.\n\n"
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
    # Provide context from both the interview analysis and the candidate summary
    context=[#analyze_content_task, 
            resume_summary_task],
    output_file="interview_questions.md" # Specify the output file name
)


# In tasks.py
from crewai import Task

generate_answers_task = Task(
    name="Generate Model Answers for Interview Questions",
    description=(
        "You will receive a markdown-formatted list of interview questions "
        "(categorized as Resume-Based, Technical, Behavioral, and Technical Scenario) "
        "and the original context used to create them (interview process summary and candidate summary).\n\n"
        "**Your Job:** For **each** question in the list:\n"
        "1. Understand the question's category and intent.\n"
        "2. Formulate a concise, accurate, and relevant model answer.\n"
        "3. For Resume-Based questions, refer to the candidate summary context.\n"
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
    # Context: Questions from previous task + original summaries
    context=[generate_questions_task, 
            #analyze_content_task, 
            resume_summary_task],
    output_file="questions_and_answers.md" # Specify the output file name
)