from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from jose import JWTError

from database import Base, engine, get_db
from models import TaskModel, UserModel
from auth import hash_password, verify_password, create_access_token, decode_access_token

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Tracker API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ---------- Schemas ----------
class UserCreate(BaseModel):
    email: str
    password: str

class Task(BaseModel):
    title: str
    completed: bool = False
    priority: str = "medium"
    category: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskResponse(Task):
    id: int
    class Config:
        from_attributes = True

# ---------- Auth helper ----------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_error = HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if email is None:
            raise credentials_error
    except JWTError:
        raise credentials_error
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user is None:
        raise credentials_error
    return user

# ---------- Auth endpoints ----------
@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = UserModel(email=user.email, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created", "email": new_user.email}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# ---------- Task endpoints ----------
@app.post("/tasks", response_model=TaskResponse)
def create_task(task: Task, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    db_task = TaskModel(
        title=task.title,
        completed=task.completed,
        priority=task.priority,
        category=task.category,
        due_date=task.due_date,
        owner_id=current_user.id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks")
def list_tasks(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
):
    query = db.query(TaskModel).filter(TaskModel.owner_id == current_user.id)
    if priority:
        query = query.filter(TaskModel.priority == priority)
    if category:
        query = query.filter(TaskModel.category == category)
    if completed is not None:
        query = query.filter(TaskModel.completed == completed)
    return query.all()

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    db_task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.owner_id == current_user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: Task, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    db_task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.owner_id == current_user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.title = task.title
    db_task.completed = task.completed
    db_task.priority = task.priority
    db_task.category = task.category
    db_task.due_date = task.due_date
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    db_task = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.owner_id == current_user.id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted"}
