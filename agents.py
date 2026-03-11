from dotenv import load_dotenv
load_dotenv()

from crewai import Agent,LLM
import os
from tools import serper_tool, pdftool,job_search_tool,interview_search_tool,seleniumscrapping_tool,scrape_website


# Example LLM setup (if needed)


# Ensure GOOGLE_API_KEY is set in your environment or .env file
llm_gemini_pro = LLM(
    model=os.getenv("MODEL_FOR_QGEN"),
    temperature=0.5,
    api_key=os.getenv("GEMINI_API_KEY_MINE"),
)
llm_gemini_flash = LLM(
    model=os.getenv("MODEL_4"),
    temperature=0.5,
    api_key=os.getenv("GEMINI_API_KEY_MINE"),
)

llm_1 = LLM(
    model=os.getenv("MODEL_1"),        
    api_key=os.getenv("GEMINI_API_KEY_MINE"),
    temperature=0.5,
    verbose=True
)

llm_2 = LLM(
    model=os.getenv("MODEL_2"),        
    api_key=os.getenv("GEMINI_API_KEY_MINE"),
    temperature=0.5,
    verbose=True
)

llm_3 = LLM(
    model=os.getenv("MODEL_3"),        
    api_key=os.getenv("GEMINI_API_KEY_MINE"),
    temperature=0.5,
    verbose=True
)

resume_extractor = Agent(
    role="Chief Data Ingestion and Validation Officer",
    goal="Extract, structure, and meticulously validate all core profile data (experience, skills, education) and "
         "associated online credibility links (GitHub, LinkedIn) from the raw resume pdf {target_pdf}",
    backstory=(
        "You are the foundation of the 'Smart Career Crew.' "
        "Your task is the most critical: turning messy, unstructured resume pdf into a pristine, validated, and structured JSON object. "
        "You use your specialized extraction tool and possess an auditor's eye to ensure no detail—from years of experience to public profile links—is missed or incorrectly formatted. "
        "You are the sole source of truth for the data flowing into the system."
    ),
    tools=[pdftool],
    llm=llm_1,
    allow_delegation=False,
    verbose=True
)


resume_summarizer = Agent(
    role="Lead Career Profile Summarization Specialist",
    goal="Craft a compelling and concise career summary for the candidate based on the structured resume data.give most priority to the resume data." \
    "**Optionally,** if that data "
        "contains `linkedin_url` or `github_url`, **try** to scrape them "
        "to find supplemental info (like a LinkedIn 'About' section or "
        "GitHub 'Pinned Repos'). **If scraping fails or no links exist or url link not correct skip and, "
        "proceed anyway,** using only the core resume data.",
    backstory=(
        "As the Lead Career Profile Summarization Specialist, your expertise lies in distilling complex career histories into clear, engaging narratives. "
        "You transform structured data into summaries that highlight key achievements, skills, and experiences, "
        "making them accessible and appealing to potential employers. "
    ),
    tools=[serper_tool],
    llm=llm_1,
    allow_delegation=False,
    verbose=True
)


job_search_agent = Agent(
    role="LinkedIn Job Search Agent",
    goal=(
        "Find the most recent and relevant fresher only job postings for the given role "
        "({target_role}) from LinkedIn in India, focusing on Indian candidateswith no experience."
    ),
    backstory=(
        "You are a professional job-hunting assistant who specializes in sourcing fresh, "
        "verified LinkedIn job postings for entry-level positions. "
        "You understand job queries and extract concise, structured listings."
    ),
    tools=[job_search_tool],
    llm=llm_2,
    verbose=True,
    allow_delegation=False
)

"""
from crewai import Agent

# Assuming llm_2 is your configured LLM instance for this agent
# Make sure llm_2 is defined or imported correctly before this line

job_match_agent = Agent(
    role="Job List Formatter Agent", # Changed role slightly
    goal=(
        "Analyze a candidate summary and a list of job postings to identify the top relevant fresher/entry-level jobs (up to 10). "
        "Your MOST CRITICAL final task is to format ONLY these selected jobs into a numbered list adhering STRICTLY to the specified multi-line format, "
        "ensuring the output contains absolutely nothing else."
    ),
    backstory=(
        "You are an AI assistant specializing in data formatting. You receive context about a candidate and potential jobs. "
        "You internally assess relevance based on skills and role fit for freshers. "
        "Your primary function is to output ONLY the best matching jobs (up to 10) in a precise numbered list format, excluding all reasoning, notes, or extraneous text."
    ),
    llm=llm_2, # Use the appropriate LLM
    verbose=True,
    allow_delegation=False # Agent must format the output itself
)
"""

job_match_agent = Agent(
    role="Job List Formatter Agent", # Changed role slightly
    goal=(
        "Analyze a candidate summary and a list of job postings to identify the top relevant fresher/entry-level jobs (up to 10). "
        "Your MOST CRITICAL final task is to format ONLY these selected jobs into a numbered list adhering STRICTLY to the specified multi-line format, "
        "ensuring the output contains absolutely nothing else."
    ),
    backstory=(
        "You are an AI assistant specializing in data formatting. You receive context about a candidate and potential jobs. "
        "You internally assess relevance based on skills and role fit for freshers. "
        "Your primary function is to output ONLY the best matching jobs (upto 10) in a precise numbered list format, excluding all reasoning, notes, or extraneous text."
    ),
    llm=llm_2, # Use the appropriate LLM
    verbose=True,
    allow_delegation=False # Agent must format the output itself
)


interview_search_agent = Agent(
    role="Specialist Interview Researcher",
    goal=(
        "Search the web to find the most relevant and high-quality "
        "interview experience pages for {target_company} and {target_role}. "
        "from GeeksforGeeks, Glassdoor, and InterviewBit."
    ),
    backstory=(
        "You are a master at using search tools to find specific, high-value information. "
        "You filter out noise and only return the most promising URLs for analysis, "
        "focusing exclusively on the trusted sites: GeeksforGeeks, Glassdoor, and InterviewBit."
    ),
    tools=[interview_search_tool],
    llm=llm_gemini_flash,
    verbose=True,
    allow_delegation=False
)



content_analysis_agent = Agent(
    role="Interview Content Analyst and Synthesizer",
    goal=(
        "Take the provided URLs (first 2 only). Scrape their contents completely, "
        "bypassing popups and dynamic content if possible. Then convert all HTML to clean text, "
        "combine them, and analyze the text to extract key technical topics, behavioral themes, "
        "and example interview questions. Always produce a comprehensive and detailed mutli-section summary "
        "using the scraped content."
    ),
    backstory=(
        "You are a specialized AI trained to synthesize structured insights from unstructured web pages into a "
        "clean detailed summary. "
        "You extract interview-related content, identify patterns, and summarize clearly. "
        "Your summaries are always clear, detailed and usable for preparing interview questions."
    ),
    tools=[scrape_website],
    llm=llm_gemini_flash,
    
    verbose=True,
    allow_delegation=False
)



question_generator_agent = Agent(
    role="Expert Interview Question Crafter",
    goal=(
        "Generate a diverse set of high-quality interview questions tailored "
        "to the specific {target_company}, {target_role}, and the provided "
        "interview process summary and candidate profile. Ensure questions cover "
        "resume details, technical depth, behavioral competencies, and realistic technical scenarios."
    ),
    backstory=(
        "You are an AI assistant specialized in recruitment and interview design. "
        "You analyze summaries of typical interview processes and candidate profiles "
        "to create insightful and relevant questions that effectively assess a candidate's suitability."
        "You generate exactly the number and type of questions requested."
    ),
    llm=llm_gemini_pro, # Use the Gemini 2.5 Pro LLM
    verbose=True,
    allow_delegation=False,
)



# Assuming llm_gemini_pro is your configured Gemini 2.5 Pro instance
answer_generator_agent = Agent(
    role="Concise Interview Answer Specialist",
    goal=(
        "Receive a list of categorized interview questions and the original interview/resume context. "
        "For **each question**, generate a brief, 'on-point' model answer. "
        "Answers should reflect the likely expectations for the {target_company} and {target_role}, "
        "drawing from the provided context where relevant (especially for resume/technical questions)."
    ),
    backstory=(
        "You are an AI assistant skilled at crafting model answers for interviews. "
        "You understand the need for brevity and relevance. You analyze the question type "
        "(resume, technical, behavioral, scenario) and the provided context "
        "to generate answers that are informative but not overly long."
    ),
    llm=llm_gemini_pro, # Use Gemini Pro
    verbose=True,
    allow_delegation=False,
    # No tools needed
)