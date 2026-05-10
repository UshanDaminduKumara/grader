import csv, os

DATASET_DIR = "dataset"

import csv

def load_data():
    documents = []

    # Read CSV safely
    with open(
        f"{DATASET_DIR}/answers.csv",
        newline="",
        encoding="cp1252",   # Fix Windows encoding issue
        errors="replace"     # Prevent crash on bad characters
    ) as f:

        for row in csv.DictReader(f):
            documents.append({
                "stdno": row["stdno"],
                "answer": row["answer"]
            })

    # Read rubric
    with open(
        f"{DATASET_DIR}/rubric.txt",
        encoding="utf-8",
        errors="replace"
    ) as f:
        rubric = f.read().strip()

    # Read question
    with open(
        f"{DATASET_DIR}/question.txt",
        encoding="utf-8",
        errors="replace"
    ) as f:
        question = f.read().strip()

    return documents, rubric, question


def load_for_display():
    documents, rubric, question = load_data()
    return {"question": question, "rubric": rubric, "students": documents}


def save_results(results):
    out_path = f"{DATASET_DIR}/results.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["stdno", "mark", "lost_marks_reason"])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "stdno":             r["stdno"],
                "mark":              r["mark"],
                "lost_marks_reason": "; ".join(r.get("lost_marks_reason", [])),
            })
    return out_path