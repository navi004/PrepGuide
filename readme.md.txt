
```

---

# PrepGuide – AI Interview Assistant

PrepGuide is an AI-powered interview preparation system that generates **personalized interview questions**, conducts a **mock interview simulation**, evaluates candidate responses using **LLM-based reasoning**, and provides **structured feedback and job recommendations**.

The system integrates **CrewAI multi-agent orchestration**, **Google Gemini models**, and a **Next.js + Firebase frontend** with a **FastAPI backend** to create a complete interview preparation workflow.

---

# Key Features

### Resume-Based Personalization

PrepGuide analyzes the uploaded resume to generate **role-specific interview questions** tailored to the candidate's skills and experience.

### AI-Powered Interview Question Generation

Using **Gemini 2.5 Pro**, the system generates:

* Technical questions
* Behavioral questions
* Scenario-based questions

Each question includes a **model answer** to help guide learning.

### Interactive Mock Interview

The platform simulates a real interview environment:

* Questions displayed sequentially
* **Speech-to-Text (STT)** for answering
* **Text-to-Speech (TTS)** for reading questions
* Progress tracking

### Multi-Criteria Answer Evaluation

After the interview, responses are evaluated using four metrics:

* Relevance
* Completeness
* Clarity
* Contextual Accuracy

Detailed feedback and improvement suggestions are generated using LLM reasoning.

### Job Recommendation Engine

Based on the resume and selected role, the system retrieves **relevant job listings** and displays them in a dedicated recommendation page.

### Asynchronous Processing

Heavy AI tasks run in background pipelines using **CrewAI agents**, ensuring the frontend remains responsive.

---

# System Architecture

The system follows a **distributed architecture** consisting of:

```
Frontend (Next.js + Firebase)
            ↓
        Ngrok Tunnel
            ↓
Backend (FastAPI)
            ↓
CrewAI Multi-Agent Pipeline
            ↓
Google Gemini LLM APIs
```

### Frontend

Handles:

* Resume upload
* Interview interface
* Speech interaction
* Evaluation dashboard

### Backend

Handles:

* Resume processing
* AI pipeline orchestration
* Question generation
* Answer evaluation
* Job recommendations

---

# Multi-Agent Pipeline (CrewAI)

PrepGuide uses multiple specialized AI agents:

| Agent                    | Role                                           |
| ------------------------ | ---------------------------------------------- |
| Resume Extractor Agent   | Extract skills and experiences from the resume |
| Resume Summarizer Agent  | Generate a structured candidate profile        |
| Question Generator Agent | Create role-based interview questions          |
| Answer Generator Agent   | Generate model answers                         |
| Job Search Agent         | Retrieve job listings                          |
| Job Matching Agent       | Rank jobs based on resume relevance            |
| Evaluation Agent         | Evaluate interview responses                   |

---

# Project Folder Structure

Based on your current project directory:

```
PrepGuide/
│
├── agents/                  # CrewAI agent definitions
├── tools/                   # Custom tools used by agents
├── tasks/                   # Task definitions for CrewAI pipeline
├── tasks_refactored/        # Updated task configurations
│
├── questions_folder/        # Generated interview questions
├── answers_folder/          # Generated model answers
│
├── sessions/                # Session-based storage for user runs
│
├── uploads_gradio/          # Uploaded resume files
│
├── candidate_summary/       # Generated candidate summaries
├── interview_questions/     # Question files
├── recommended_jobs/        # Job recommendation outputs
│
├── files_split/             # File processing utilities
├── split_files/             # Question/answer splitting modules
│
├── questions_and_answers/   # Combined QA outputs
│
├── app/                     # FastAPI application modules
├── crew/                    # CrewAI orchestration logic
│
├── main.py                  # Main FastAPI backend server
├── crew_tester.py           # Pipeline testing script
│
├── question_audio/          # Generated audio for questions
│
├── requirements.txt         # Python dependencies
├── .env                     # API keys and environment variables
│
└── README.md
```

---

# Technologies Used

### Backend

* Python
* FastAPI
* CrewAI
* Google Gemini API
* LangChain (for LLM orchestration)

### Frontend

* Next.js
* React
* Firebase Hosting
* Chart.js

### AI Models

* Gemini 2.5 Pro
* Gemini Flash

### Speech Processing

* Web Speech API
* SpeechRecognition
* SpeechSynthesis

### Development Tools

* Ngrok
* Python Virtual Environments
* Git & GitHub

---

# Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/prepguide.git
cd prepguide
```

---

### Create Virtual Environment

```bash
python -m venv venv
```

Activate environment:

Windows

```bash
venv\Scripts\activate
```

Mac/Linux

```bash
source venv/bin/activate
```

---

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file in the root directory:

```
GEMINI_API_KEY=your_api_key
SERPER_API_KEY=your_api_key
```

---

# Running the Backend

Start the FastAPI server:

```bash
python main.py
```

or

```bash
uvicorn main:app --reload
```

The API will run on:

```
http://localhost:8000
```

---

# Exposing Backend Using Ngrok

Since the frontend is hosted separately:

```
ngrok http 8000
```

Use the generated public URL in your frontend configuration.

---

# Running the CrewAI Pipeline (Test Mode)

To test the AI pipeline independently:

```bash
python crew_tester.py
```

---

# System Workflow

1️⃣ User uploads resume
2️⃣ Backend creates session folder
3️⃣ CrewAI agents process resume
4️⃣ Questions and answers are generated
5️⃣ Frontend conducts interview simulation
6️⃣ User responses are collected
7️⃣ Gemini evaluates responses
8️⃣ Dashboard displays results
9️⃣ Job recommendations are shown

---

# Evaluation Framework

The answer evaluation module scores responses using four criteria:

| Criterion           | Description                       |
| ------------------- | --------------------------------- |
| Relevance           | Alignment with interview question |
| Completeness        | Coverage of key concepts          |
| Clarity             | Logical structure and grammar     |
| Contextual Accuracy | Consistency with resume           |

Scores are visualized using **Chart.js dashboards**.

---

# Current Limitations

* Backend currently runs locally
* Ngrok tunnel required for frontend communication
* Speech APIs depend on browser support
* CrewAI pipeline processing time ~3 minutes
* No persistent user progress tracking yet

---

# Future Improvements

* Deploy backend on **cloud infrastructure**
* Add **voice sentiment analysis**
* Implement **adaptive interview difficulty**
* Add **long-term user progress tracking**
* Expand **domain-specific interview datasets**
* Integrate **Explainable AI (XAI) for evaluation transparency**

---

# Author

Naveen Nidadavolu
Integrated M.Tech CSE (Business Analytics)
Vellore Institute of Technology, Chennai

---

# License

This project is intended for **educational and research purposes**.

---

