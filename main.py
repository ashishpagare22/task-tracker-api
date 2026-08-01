from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Task Tracker API")

# In-memory storage: a simple dictionary acting as our "database" for now
tasks = {}
next_id = 1

class Task(BaseModel):
    title: str
    completed: bool = False

class TaskResponse(Task):
    id: int

@app.post("/tasks", response_model=TaskResponse)
def create_task(task: Task):
    global next_id
    task_id = next_id
    tasks[task_id] = task
    next_id += 1
    return TaskResponse(id=task_id, **task.dict())

@app.get("/tasks")
def list_tasks():
    return [TaskResponse(id=tid, **t.dict()) for tid, t in tasks.items()]

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(id=task_id, **tasks[task_id].dict())

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: Task):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    tasks[task_id] = task
    return TaskResponse(id=task_id, **task.dict())

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return {"message": "Task deleted"}
