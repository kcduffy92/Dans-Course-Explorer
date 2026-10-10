"""Yale SOM course explorer API desk.

Run from backend/:  uvicorn main:app --reload --port 8000
Open API docs:      http://127.0.0.1:8000/docs
Frontend (Vite):    http://127.0.0.1:5173
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import run_agent
from db import engine, fetch_courses, init_db

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

init_db()

app = FastAPI(title="Yale SOM Courses", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# The React catalog was built against the JSON file's column names, so courses
# from the database are served with those same keys.
CATALOG_KEYS = {
    "course_id": "Course ID",
    "course_number": "Course Number",
    "course_title": "Course Title",
    "section": "Section",
    "course_category": "Course Category",
    "course_type": "Course Type",
    "course_session": "Course Session",
    "daytimes": "Daytimes",
    "room": "Room",
    "units": "Units",
    "faculty_1": "Faculty 1",
    "faculty_1_email": "Faculty 1 Email",
    "syllabus": "Syllabus",
    "old_syllabus": "Old Syllabus",
    "course_description": "Course Description",
    "faculty_bio": "faculty_bio",
}


def load_courses() -> list[dict]:
    return [
        {key: row.get(col) or "" for col, key in CATALOG_KEYS.items()}
        for row in fetch_courses()
    ]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str] = Field(default_factory=list)


@app.get("/api/health")
def health():
    return {"ok": True, "database": engine.url.get_backend_name()}


@app.get("/api/courses")
def list_courses(q: str | None = Query(default=None)):
    """Return courses for the React catalog (optional text filter)."""
    courses = load_courses()
    if not q:
        return {"count": len(courses), "courses": courses}
    needle = q.lower().strip()
    matched = [
        c
        for c in courses
        if needle in json.dumps(c, ensure_ascii=False).lower()
    ]
    return {"count": len(matched), "courses": matched}


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    result = run_agent(body.message)
    return ChatResponse(
        reply=result.get("reply", ""),
        tools_used=list(result.get("tools_used") or []),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
