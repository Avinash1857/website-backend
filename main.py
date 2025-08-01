import json
import os
from hashlib import sha256
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = FastAPI()

# CORS so frontend can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your Netlify domain later
    allow_methods=["*"],
    allow_headers=["*"],
)

# Template loader
templates = Jinja2Templates(directory="templates")

# Email setup
OWNER_EMAIL = "kvvdavinash@gmail.com"
APP_PASSWORD = "cidq pkde aphl sxki"  # Your app password

class AccessRequest(BaseModel):
    username: str
    mobile: str
    email: str

@app.post("/request-access")
async def request_access(data: AccessRequest, request: Request):
    username = data.username
    mobile = data.mobile
    email = data.email

    accept_link = f"https://website-backend-dm6y.onrender.com/accept?email={email}&username={username}"
    decline_link = f"https://website-backend-dm6y.onrender.com/decline?email={email}&username={username}"

    # Render the email template using Jinja2
    html_content = templates.get_template("access_request_email.html").render({
        "username": username,
        "mobile": mobile,
        "email": email,
        "accept_link": accept_link,
        "decline_link": decline_link
    })

    # Send the email
    send_email("Access Request", html_content)
    return {"message": "Request sent to admin!"}

def send_email(subject, html, to=None):
    msg = MIMEMultipart()
    msg["From"] = OWNER_EMAIL
    msg["To"] = to or OWNER_EMAIL  # default to owner if not specified
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(OWNER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

        
from fastapi.responses import PlainTextResponse

@app.get("/accept")
async def accept_user(email: str, username: str):
    print(f"✅ ACCEPTED: {username} ({email})")
    send_password_setup_email(username, email)
    return PlainTextResponse(f"User '{username}' accepted! Password setup email sent.")


@app.get("/decline")
async def decline_user(email: str, username: str):
    print(f"❌ DECLINED: {username} ({email})")
    # No email sent to user
    return PlainTextResponse(f"User '{username}' declined. No account will be created.")

def send_password_setup_email(username: str, email: str):
    link = f"https://your-netlify-frontend-url.netlify.app/set-password?username={username}&email={email}"

    html = f"""
    <html>
      <body>
        <p>Hello <strong>{username}</strong>,</p>
        <p>You’ve been approved to access the website. Please set your password using the link below:</p>
        <p><a href="{link}" style="padding: 10px; background: blue; color: white; text-decoration: none;">Set Your Password</a></p>
      </body>
    </html>
    """

    send_email("Set Your Password", html, to=email)
    
from fastapi import HTTPException

@app.post("/set-password")
async def set_password(data: dict):
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not (username and email and password):
        raise HTTPException(status_code=400, detail="Missing fields")

    # Hash the password for security
    hashed_password = sha256(password.encode()).hexdigest()

    # Load existing users
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = []

    # Check if user already exists
    for user in users:
        if user["email"] == email:
            raise HTTPException(status_code=400, detail="User already exists")

    # Add new user
    users.append({
        "username": username,
        "email": email,
        "password": hashed_password,
        "history": []  # will store login/logout later
    })

    # Save back to file
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)

    return {"message": "Password set successfully. You can now log in."}

from datetime import datetime

@app.post("/login")
async def login_user(data: dict):
    email = data.get("email")
    password = data.get("password")

    if not (email and password):
        raise HTTPException(status_code=400, detail="Missing email or password")

    hashed_input = sha256(password.encode()).hexdigest()

    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        raise HTTPException(status_code=500, detail="Server error")

    for user in users:
        if user["email"] == email and user["password"] == hashed_input:
            user["history"].append({
                "event": "login",
                "timestamp": datetime.now().isoformat()
            })
            with open("users.json", "w") as f:
                json.dump(users, f, indent=2)
            return {"message": "Login successful", "username": user["username"]}

    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/logout")
async def logout_user(data: dict):
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username missing")

    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        raise HTTPException(status_code=500, detail="Server error")

    for user in users:
        if user["username"] == username:
            user["history"].append({
                "event": "logout",
                "timestamp": datetime.now().isoformat()
            })
            with open("users.json", "w") as f:
                json.dump(users, f, indent=2)
            return {"message": "Logout recorded"}

    raise HTTPException(status_code=404, detail="User not found")

@app.get("/history")
async def get_history(username: str):
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        raise HTTPException(status_code=500, detail="Server error")

    for user in users:
        if user["username"] == username:
            return {"history": user.get("history", [])}

    raise HTTPException(status_code=404, detail="User not found")


