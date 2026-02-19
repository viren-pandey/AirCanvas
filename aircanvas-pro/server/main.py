from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import os

# ==========================================
# CONFIGURATION
# ==========================================

app = FastAPI(title="AirCanvas Pro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# DATA STORAGE (In-Memory for this file)
# ==========================================

users_db = {
    "pandeyviren78@gmail.com": {
        "id": "admin-1",
        "email": "pandeyviren78@gmail.com",
        "name": "Viren Pandey",
        "password": "admin123", # In prod: hash this
        "role": "ADMIN"
    }
}
sessions_db = {}
frames_db = []

# CMS Storage - Start Empty
posts_db = [] 
jobs_db = []

# ==========================================
# MODELS
# ==========================================

class UserLogin(BaseModel):
    email: str
    password: str

class UserSignup(BaseModel):
    email: str
    name: str
    password: str

class SessionStart(BaseModel):
    user_id: str

class SessionEnd(BaseModel):
    session_id: str
    avg_fps: float

class BlogPost(BaseModel):
    title: str
    excerpt: str
    content: str
    image_url: str
    author: str
    category: str

class JobPost(BaseModel):
    title: str
    department: str
    location: str
    type: str # Full-time, Contract
    description: str

# ==========================================
# AUTH ENDPOINTS
# ==========================================

@app.post("/auth/signup")
def signup(user: UserSignup):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already exists")
    user_id = str(uuid.uuid4())
    users_db[user.email] = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "password": user.password,
        "role": "USER"
    }
    return {"success": True, "user_id": user_id, "role": "USER"}

@app.post("/auth/login")
def login(user: UserLogin):
    stored_user = users_db.get(user.email)
    if not stored_user or stored_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "success": True, 
        "token": "fake-jwt-token", 
        "user": {
            "name": stored_user["name"], 
            "email": stored_user["email"],
            "role": stored_user.get("role", "USER")
        }
    }

# ==========================================
# SESSION ENDPOINTS
# ==========================================

@app.post("/sessions/start")
def start_session(data: SessionStart):
    session_id = str(uuid.uuid4())
    sessions_db[session_id] = {
        "user_id": data.user_id,
        "start_time": datetime.now(),
        "active": True
    }
    return {"id": session_id, "status": "started"}

@app.post("/sessions/end")
def end_session(data: SessionEnd):
    if data.session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    sessions_db[data.session_id]["end_time"] = datetime.now()
    sessions_db[data.session_id]["active"] = False
    sessions_db[data.session_id]["avg_fps"] = data.avg_fps
    return {"success": True}

@app.post("/frames/upload")
async def upload_frame(session_id: str, file: UploadFile = File(...)):
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Session not found")
    os.makedirs("uploads", exist_ok=True)
    file_location = f"uploads/{session_id}_{uuid.uuid4()}.png"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    frames_db.append({
        "session_id": session_id,
        "path": file_location,
        "timestamp": datetime.now()
    })
    return {"success": True, "url": f"http://localhost:8000/{file_location}"}

# ==========================================
# CMS ENDPOINTS (BLOG)
# ==========================================

@app.get("/api/posts")
def get_posts():
    return posts_db

@app.get("/api/posts/{post_id}")
def get_post(post_id: str):
    for post in posts_db:
        if post["id"] == post_id:
            return post
    raise HTTPException(status_code=404, detail="Post not found")

@app.post("/api/posts")
def create_post(post: BlogPost):
    new_post = post.dict()
    new_post["id"] = str(uuid.uuid4())
    new_post["date"] = datetime.now().isoformat()
    posts_db.append(new_post)
    return new_post

@app.delete("/api/posts/{post_id}")
def delete_post(post_id: str):
    global posts_db
    posts_db = [p for p in posts_db if p["id"] != post_id]
    return {"success": True}

# ==========================================
# CMS ENDPOINTS (CAREERS)
# ==========================================

@app.get("/api/jobs")
def get_jobs():
    return jobs_db

@app.post("/api/jobs")
def create_job(job: JobPost):
    new_job = job.dict()
    new_job["id"] = str(uuid.uuid4())
    new_job["date"] = datetime.now().isoformat()
    jobs_db.append(new_job)
    return new_job

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    global jobs_db
    jobs_db = [j for j in jobs_db if j["id"] != job_id]
    return {"success": True}
