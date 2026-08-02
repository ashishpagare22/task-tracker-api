import { useState, useEffect } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignup, setIsSignup] = useState(false)
  const [authError, setAuthError] = useState('')

  const [tasks, setTasks] = useState([])
  const [newTitle, setNewTitle] = useState('')
  const [newPriority, setNewPriority] = useState('medium')

  useEffect(() => {
    if (token) fetchTasks()
  }, [token])

  async function fetchTasks() {
    const res = await fetch(`${API_URL}/tasks`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.ok) {
      setTasks(await res.json())
    } else {
      handleLogout()
    }
  }

  async function handleAuth(e) {
    e.preventDefault()
    setAuthError('')
    if (isSignup) {
      const res = await fetch(`${API_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      if (!res.ok) {
        const err = await res.json()
        setAuthError(err.detail || 'Signup failed')
        return
      }
    }

    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const loginRes = await fetch(`${API_URL}/login`, {
      method: 'POST',
      body: form
    })
    if (!loginRes.ok) {
      setAuthError('Login failed')
      return
    }
    const data = await loginRes.json()
    localStorage.setItem('token', data.access_token)
    setToken(data.access_token)
  }

  function handleLogout() {
    localStorage.removeItem('token')
    setToken(null)
    setTasks([])
  }

  async function handleCreateTask(e) {
    e.preventDefault()
    if (!newTitle.trim()) return
    const res = await fetch(`${API_URL}/tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ title: newTitle, priority: newPriority })
    })
    if (res.ok) {
      setNewTitle('')
      fetchTasks()
    }
  }

  async function toggleComplete(task) {
    await fetch(`${API_URL}/tasks/${task.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ ...task, completed: !task.completed })
    })
    fetchTasks()
  }

  async function deleteTask(id) {
    await fetch(`${API_URL}/tasks/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` }
    })
    fetchTasks()
  }

  if (!token) {
    return (
      <div className="auth-container">
        <h1>Task Tracker</h1>
        <form onSubmit={handleAuth}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
          <button type="submit">{isSignup ? 'Sign Up' : 'Log In'}</button>
        </form>
        {authError && <p className="error">{authError}</p>}
        <button className="link-button" onClick={() => setIsSignup(!isSignup)}>
          {isSignup ? 'Already have an account? Log in' : "Don't have an account? Sign up"}
        </button>
      </div>
    )
  }

  return (
    <div className="app-container">
      <div className="header">
        <h1>My Tasks</h1>
        <button onClick={handleLogout}>Log Out</button>
      </div>

      <form onSubmit={handleCreateTask} className="new-task-form">
        <input
          type="text"
          placeholder="New task..."
          value={newTitle}
          onChange={e => setNewTitle(e.target.value)}
        />
        <select value={newPriority} onChange={e => setNewPriority(e.target.value)}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <button type="submit">Add</button>
      </form>

      <ul className="task-list">
        {tasks.map(task => (
          <li key={task.id} className={task.completed ? 'completed' : ''}>
            <span onClick={() => toggleComplete(task)}>
              {task.completed ? '✅' : '⬜'} {task.title}
            </span>
            <span className={`priority priority-${task.priority}`}>{task.priority}</span>
            <button onClick={() => deleteTask(task.id)}>Delete</button>
          </li>
        ))}
      </ul>
      {tasks.length === 0 && <p>No tasks yet — add one above!</p>}
    </div>
  )
}

export default App
