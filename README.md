# ResearchMind

AI-Powered Company Intelligence Report Generator

ResearchMind is an end-to-end business intelligence system that automatically researches companies, analyzes publicly available information, and generates professional intelligence reports in PDF format.

The goal is to reduce the time spent manually searching through company websites, news articles, funding information, leadership profiles, and financial reports by automating the research workflow.

---

## Features

* AI-generated Company Intelligence Reports
* Automated Web Research Pipeline
* Multi-source Information Collection
* Leadership Analysis
* Products & Services Overview
* Funding & Investor Research
* Recent News Tracking
* Competitor Analysis
* Financial Performance Summary
* Risk & Controversy Assessment
* Confidence Scoring System
* Hallucination Reduction Controls
* Professional PDF Report Generation
* Invalid Company Detection
* Streamlit Web Interface

---

## Problem Statement

Analysts, students, investors, and business professionals often spend significant time gathering information about companies from multiple websites.

ResearchMind automates this process by:

1. Searching the web for company-specific information
2. Filtering and validating sources
3. Extracting relevant content
4. Synthesizing findings using Large Language Models
5. Generating structured intelligence reports

---

## System Architecture

User Input
↓
Search Query Generation (Groq LLM)
↓
Web Search (DuckDuckGo Search)
↓
Source Filtering & Validation
↓
Content Scraping (BeautifulSoup)
↓
Research Confidence Scoring
↓
Report Synthesis (Groq LLM)
↓
PDF Report Builder
↓
Downloadable Intelligence Report

---

## Tech Stack

### Frontend

* Streamlit

### AI & NLP

* Groq API
* Llama 3.3 70B Versatile

### Research Pipeline

* DuckDuckGo Search (DDGS)
* Requests
* BeautifulSoup

### Report Generation

* ReportLab

### Environment Management

* Python
* dotenv

---

## Key Engineering Features

### Research Confidence Scoring

Each report is assigned a confidence score based on:

* Number of research areas covered
* Availability of full articles
* Source quality
* Data completeness

This helps prevent low-quality reports from being generated.

---

### Hallucination Controls

ResearchMind includes multiple safeguards:

* Company-specific search queries
* Source filtering
* Duplicate URL removal
* Invalid company rejection
* Financial verification rules
* Confidence threshold validation
* Forecast vs Fact separation

---

### Source Quality Controls

The system:

* Blocks low-quality domains
* Removes duplicate content
* Prioritizes authoritative sources
* Filters irrelevant articles
* Uses title-based relevance checks

---

## Example Report Sections

* Executive Summary
* Company Overview
* Leadership Team
* Products & Services
* Funding & Investors
* Recent News
* Competitors
* Financial Performance
* Risks & Controversies
* Analyst Assessment

---

## Installation

### Clone Repository

```bash
git clone https://github.com/prathameshbhujbal8/ResearchMind.git
cd ResearchMind
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows:

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Run Application

```bash
streamlit run app.py
```

---

## Sample Use Cases

* Company Research
* Market Analysis
* Startup Evaluation
* Internship Research Projects
* Business Intelligence Workflows
* Investor Research
* Competitor Benchmarking

---

## Future Improvements

* JavaScript Rendering Support (Playwright)
* SEC/Annual Report Integration
* Advanced Financial Data Sources
* Source Citation Mapping
* Industry Comparison Reports
* Multi-Company Benchmarking

---

## Project Highlights

* End-to-End AI Application
* Retrieval-Augmented Research Workflow
* Real-Time Information Gathering
* Confidence-Based Quality Control
* Automated PDF Generation
* Production Deployment with Streamlit

---

## Author

Prathamesh Bhujbal

Computer Engineering Student

Focused on AI, Data Analytics, Business Intelligence, and Intelligent Automation Systems.
