from dotenv import load_dotenv
load_dotenv()


from crewai_tools import SerperDevTool,HyperbrowserLoadTool,SeleniumScrapingTool,ScrapegraphScrapeTool,FirecrawlCrawlWebsiteTool
import os
import PyPDF2
import json
from crewai.tools import BaseTool
from typing import Type, List, Dict
from pydantic import BaseModel, Field
import requests
from browserbase import Browserbase
from bs4 import BeautifulSoup




os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")
os.environ["BROWSERBASE_PROJECT_ID"] = os.getenv("BROWSERBASE_PROJECT_ID")
os.environ["BROWSERBASE_API_KEY"] = os.getenv("BROWSERBASE_API_KEY")


class PDFToolInput(BaseModel):
    file_path: str = Field(..., description="Path to the PDF file to be read.")

class PDFTool(BaseTool):
    name: str = "PDF Reader Tool"
    description: str = "Tool to read and extract text content from a PDF file."
    args_schema: Type[BaseModel] = PDFToolInput

    def _run(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

pdftool = PDFTool()




class JobSearchInput(BaseModel):
    role: str = Field(..., description="Target role to search jobs for (e.g., 'Python Backend Developer')")
    location: str = Field("India", description="Location for job search, default is India")

class JobSearchTool(BaseTool):
    name: str = "LinkedIn Freshers Job Search Tool"
    description: str = (
        "Fetches up to 20 fresher job listings from LinkedIn using the Serper API "
        "for the given role and location. Results include title, link, and snippet."
    )
    args_schema: Type[BaseModel] = JobSearchInput

    def _run(self, role: str, location: str = "India") -> List[Dict[str, str]]:
        """
        Queries Serper API to get up to 20 fresher LinkedIn job listings
        based on the role and location.
        """
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            raise ValueError("❌ SERPER_API_KEY not found in environment variables.")

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }

        query = (
            f"search for {role} roles for freshers with no experience in linkedin.com "
            f"for {location} candidates"
        )

        payload = json.dumps({
            "q": query,
            "location": location,
            "gl": "in",
            "tbs": "qdr:d",  # limit to last 24 hours
            "num": 20
        })

        response = requests.post(url, headers=headers, data=payload)
        data = response.json()

        jobs = []
        for item in data.get("organic", []):
            jobs.append({
                "title": item.get("title", "No title"),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "No description available"),
                "date_posted": item.get("date", "No date available"),
                "rating": item.get("rating", "No rating available")
            })

        if not jobs:
            return [{"message": "No fresher job postings found for this query."}]

        return jobs

# Instantiate tool for CrewAI use
job_search_tool = JobSearchTool()


class InterviewSearchInput(BaseModel):
    role: str = Field(..., description="Target role to search interview questions for")
    company: str = Field(..., description="Company name to search interview questions for")

class InterviewSearchTool(BaseTool):
    name: str = "Interview Question Search Tool"
    description: str = (
        "Searches for interview questions and experiences related to the given role and company "
        "from trusted sites like Glassdoor and GeeksforGeeks using the Serper API."
    )
    args_schema: Type[BaseModel] = InterviewSearchInput

    def _run(self, role: str, company: str) -> List[Dict[str, str]]:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            raise ValueError("❌ SERPER_API_KEY not found in environment variables.")

        url = "https://google.serper.dev/search"

        payload = json.dumps({
        "q": f"{company} {role} interview questions from geeksforgeeks ,glassdoor and interviewBit",
        "location": "India",
        "gl": "in"
        })
        headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()

        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", "No title"),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })

        if not results:
            return [{"message": f"No interview question sources found for {company} - {role}."}]

        return results

interview_search_tool = InterviewSearchTool()

serper_tool = SerperDevTool(api_key=os.getenv("SERPER_API_KEY"),
)

hyperbrowser_tool = HyperbrowserLoadTool(api_key=os.getenv("HYPERBROWSER_API_KEY"),
                                         name="Hyperbrowser Load Tool",
)

seleniumscrapping_tool = SeleniumScrapingTool(
    name="Selenium Scraping Tool",
    wait_time=15,
)


scrapegraph_tool = ScrapegraphScrapeTool(api_key=os.getenv("SCRAPEGRAPH_API_KEY"),
                                         name="Scrapegraph Scrape Tool",
)



firecrawl_tool = FirecrawlCrawlWebsiteTool(
    api_key=os.getenv("FIRECRAWL_API_KEY"),
    name = "scrape_website",
)


class SerperScrapeInput(BaseModel):
    url: str = Field(..., description="URL of the webpage to scrape content from.")

# Tool class
class SerperScrapeTool(BaseTool):
    name: str = "Serper Web Scraper"
    description: str = (
        "Uses Serper Scrape API to extract and clean visible text content from any webpage, "
        "such as interview experiences or job descriptions. Automatically removes HTML, scripts, and ads."
    )
    args_schema: Type[BaseModel] = SerperScrapeInput

    def clean_html(self, html: str) -> str:
        """Remove unnecessary tags and extract clean readable text."""
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "header", "footer", "nav", "noscript", "svg", "img", "aside"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        return " ".join(text.split())

    def _run(self, url: str) -> str:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            raise ValueError("❌ SERPER_API_KEY not found in environment variables.")

        endpoint = "https://scrape.serper.dev"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = json.dumps({"url": url})

        try:
            response = requests.post(endpoint, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Use either clean text or fallback to HTML cleanup
            raw_text = data.get("text")
            html_content = data.get("html")
            if raw_text and len(raw_text.strip()) > 200:
                cleaned = raw_text.strip()
            elif html_content:
                cleaned = self.clean_html(html_content)
            else:
                cleaned = "⚠️ No readable text content found on page."

            return cleaned

        except Exception as e:
            return f"❌ Error scraping {url}: {str(e)}"

# Instantiate the tool
scrape_website = SerperScrapeTool()

