import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from database import create_document
from schemas import Lead

app = FastAPI(title="Martial Arts Gym API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Martial Arts Gym Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


# -------- Static content endpoints (programs, schedule) --------
class Program(BaseModel):
    id: str
    title: str
    level: str
    description: str
    days: List[str]


class ClassItem(BaseModel):
    id: str
    title: str
    instructor: str
    day: str
    time: str
    level: str


PROGRAMS: List[Program] = [
    Program(
        id="kickboxing",
        title="Kickboxing",
        level="All Levels",
        description="High-energy striking class blending boxing and Muay Thai fundamentals.",
        days=["Mon", "Wed", "Fri"],
    ),
    Program(
        id="karate",
        title="Karate",
        level="Beginner to Advanced",
        description="Traditional karate focusing on kihon, kata, and kumite for discipline and power.",
        days=["Tue", "Thu", "Sat"],
    ),
    Program(
        id="kids",
        title="Kids Martial Arts",
        level="Ages 6-12",
        description="Confidence, focus, and fitness in a fun, safe environment for kids.",
        days=["Mon", "Wed", "Sat"],
    ),
]

SCHEDULE: List[ClassItem] = [
    ClassItem(id="kb-mon-6pm", title="Kickboxing Fundamentals", instructor="Coach Maya", day="Mon", time="6:00 PM", level="All"),
    ClassItem(id="kb-wed-6pm", title="Kickboxing Bag Work", instructor="Coach Tom", day="Wed", time="6:00 PM", level="All"),
    ClassItem(id="kb-fri-6pm", title="Kickboxing Sparring", instructor="Coach Maya", day="Fri", time="6:00 PM", level="Intermediate"),
    ClassItem(id="kar-tue-7pm", title="Karate Basics", instructor="Sensei Ken", day="Tue", time="7:00 PM", level="Beginner"),
    ClassItem(id="kar-thu-7pm", title="Karate Kata", instructor="Sensei Ken", day="Thu", time="7:00 PM", level="All"),
    ClassItem(id="kar-sat-10am", title="Karate Kumite", instructor="Sensei Aiko", day="Sat", time="10:00 AM", level="Advanced"),
    ClassItem(id="kids-wed-5pm", title="Kids Martial Arts", instructor="Coach Lee", day="Wed", time="5:00 PM", level="Ages 6-12"),
]


@app.get("/api/programs", response_model=List[Program])
def get_programs():
    return PROGRAMS


@app.get("/api/schedule", response_model=List[ClassItem])
def get_schedule(day: Optional[str] = None):
    if day:
        return [c for c in SCHEDULE if c.day.lower() == day.lower()]
    return SCHEDULE


# -------- Lead capture endpoint (uses database) --------
class LeadResponse(BaseModel):
    id: str
    message: str


@app.post("/api/leads", response_model=LeadResponse)
async def create_lead(lead: Lead):
    try:
        inserted_id = create_document("lead", lead)
        return {"id": inserted_id, "message": "Thanks! We received your request and will get back to you shortly."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os

    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
