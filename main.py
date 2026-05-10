from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from data_handling import load_data, save_results, load_for_display
from agent import run_grader

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

@app.get("/load")
def load():
    try:
        return load_for_display()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset file missing: {e}")

@app.post("/grade")
def grade():
    try:
        documents, rubric, question = load_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset file missing: {e}")

    final_marks = run_grader(documents, rubric, question)
    saved_path  = save_results(final_marks)

    return {
        "status":  "grading complete",
        "saved":   saved_path,
        "results": final_marks,
    }