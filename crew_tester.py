from crewai import Crew,Process
from tasks import (
    resume_summary_task,
    resume_extraction_task,
    job_search_task,job_filter_task,
    find_urls_task,
    #analyze_content_task,
    generate_questions_task,
    generate_answers_task
    )
from agents import (resume_summarizer,
                    resume_extractor,
                    job_search_agent,
                    job_match_agent,
                    interview_search_agent,
                    #content_analysis_agent,
                    question_generator_agent,
                    answer_generator_agent
                    )

crew = Crew(
    name="Smart Career Crew",
    agents=[resume_extractor,
            resume_summarizer,
            job_search_agent,
            job_match_agent,
            interview_search_agent,
            #content_analysis_agent,
            question_generator_agent,
            answer_generator_agent

            ],
    tasks=[resume_extraction_task,
           resume_summary_task,
           job_search_task,
           job_filter_task,
           find_urls_task,
           #analyze_content_task,
           generate_questions_task,
           generate_answers_task
           ],
    process=Process.sequential,
    verbose=True
)


result = crew.kickoff(inputs={"target_pdf": "resume_naveen_1.pdf", 
                              "target_role": "Software Developer Engineer","target_company": "Deloitte"})
print(result)   