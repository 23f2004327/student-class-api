import csv
import os
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Student Class API")

# Allow GET requests from any origin, as required by the assignment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = Path(os.environ.get("STUDENTS_CSV", str(BASE_DIR / "students.csv")))


def load_students() -> list[dict[str, int | str]]:
    """Read the assignment CSV, preserving its original row order."""
    if not CSV_PATH.is_file():
        raise HTTPException(
            status_code=500,
            detail=(
                "Student CSV not found. Add the assignment CSV to the project as "
                "students.csv, or set the STUDENTS_CSV environment variable."
            ),
        )

    try:
        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or not {"studentId", "class"}.issubset(reader.fieldnames):
                raise HTTPException(
                    status_code=500,
                    detail="CSV must contain columns named studentId and class.",
                )

            students: list[dict[str, int | str]] = []
            for row in reader:
                try:
                    student_id = int(row["studentId"])
                except (TypeError, ValueError):
                    raise HTTPException(
                        status_code=500,
                        detail="Every studentId value must be an integer.",
                    )

                students.append(
                    {
                        "studentId": student_id,
                        "class": row["class"],
                    }
                )
            return students
    except HTTPException:
        raise
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not read student CSV.") from exc


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "endpoint": "/api"}


@app.get("/api")
def get_students(
    classes: Annotated[list[str] | None, Query(alias="class")] = None,
) -> dict[str, list[dict[str, int | str]]]:
    students = load_students()

    # A repeated query parameter such as ?class=1A&class=1B becomes a list.
    # Filtering the original list preserves CSV row order, not query-param order.
    if classes:
        selected_classes = set(classes)
        students = [student for student in students if student["class"] in selected_classes]

    return {"students": students}
