# AI Student Grading System

An AI-powered student answer grading system built with FastAPI, LangGraph, and DeepSeek.

> **Version:** v1.0.0 — Initial Release  
> **Status:** Active Development — Research Project (Ongoing)

---

## How It Works

A multi-agent pipeline grades student answers automatically:

1. **Grader Agent** — reads each student answer and assigns a mark (1–10)
2. **Critic Agent** — reviews the marks for fairness against the rubric
3. **Supervisor Agent** — accepts or sends back for re-grading

The frontend shows the full pipeline in 3 screens: data preview → grading progress → results.

---

## Folder Structure

```
grading-api/
├── main.py              # FastAPI app and endpoints
├── agent.py             # LangGraph multi-agent pipeline
├── data_handling.py     # Load CSV/TXT files, save results
├── frontend/
│   ├── index.html       # UI (3 screens in one file)
│   ├── style.css        # QuillBot-inspired light theme
│   └── app.js           # Screen logic and API calls
├── dataset/
│   ├── answers.csv      # Student answers (stdno, answer)
│   ├── rubric.txt       # Marking criteria
│   └── question.txt     # Exam question
├── .env                 # API key 
└── requirements.txt     # Python dependencies
```

---

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Add your DeepSeek API key**

Create a `.env` file in the root folder:
```
DEEPSEEK_API_KEY=your_key_here
```

**3. Add your dataset**

- `dataset/answers.csv` — two columns: `stdno`, `answer`
- `dataset/rubric.txt` — your marking scheme as plain text
- `dataset/question.txt` — the exam question as plain text

Example `answers.csv`:
```csv
stdno,answer
S001,Photosynthesis is the process by which plants use sunlight...
S002,Plants make food using the sun and water only.
```

**4. Run the server**
```bash
uvicorn main:app --reload
```

**5. Open the app**

Go to `http://localhost:8000` in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Serves the frontend |
| GET | `/load` | Returns dataset, rubric, and question |
| POST | `/grade` | Runs the grading pipeline and saves results |

---

## Output

Results are saved to `dataset/results.csv` with columns:

```
stdno, mark, lost_marks_reason
```

---

## Changelog

### v1.0.0 — Initial Release
- Multi-agent grading pipeline (Grader → Critic → Supervisor)
- Batch processing with configurable batch size
- Re-grading loop with critic feedback injection
- FastAPI backend with `/load` and `/grade` endpoints
- Light-theme frontend (QuillBot-inspired) with 3-screen flow
- Full answer text display — no truncation regardless of answer length
- Results saved automatically to `dataset/results.csv`

---

## Upcoming — Within One Week

The following features are currently in development and will be released shortly:

- **RAG System Integration** — the grading agents will use Retrieval-Augmented Generation to reference past graded answers, course material, and model answers stored in a vector database. This will significantly improve grading consistency and contextual accuracy across long or complex answers.

- **UI Improvements** — richer results view with per-student mark breakdown charts, batch progress indicators showing which batch is being processed in real time, and a side-by-side answer vs. feedback panel.

---

## Research Notes

This project is part of ongoing research into **automated educational assessment using multi-agent LLM systems**. The key research questions being explored are:

- How reliably can a Grader–Critic–Supervisor agent loop replicate human double-marking?
- What is the effect of batch size on grading consistency and LLM context quality?
- Can RAG-enhanced grading reduce mark variance across similar student answers?
- How does critic feedback injection on re-grade attempts improve final mark accuracy?

Results and findings will be documented as the project develops.

---

## Notes

- Answers of any length are fully displayed in the UI — no text is cut off.
- Grading runs in batches of 4 students per LLM call.
- Each batch gets a maximum of 2 re-grade attempts if the critic rejects it.
- The `404 /favicon.ico` log line is harmless — it is just the browser looking for a tab icon.
