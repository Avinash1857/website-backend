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

    accept_link = f"https://your-backend-url.com/accept?email={email}&username={username}"
    decline_link = f"https://your-backend-url.com/decline?email={email}&username={username}"

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

def send_email(subject, html):
    msg = MIMEMultipart()
    msg["From"] = OWNER_EMAIL
    msg["To"] = OWNER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(OWNER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)
        
from fastapi.responses import PlainTextResponse

@app.get("/accept")
async def accept_user(email: str, username: str):
    print(f"✅ ACCEPTED: {username} ({email})")
    # TODO: Send password setup email here
    return PlainTextResponse(f"User '{username}' accepted! They will receive a password setup email soon.")

@app.get("/decline")
async def decline_user(email: str, username: str):
    print(f"❌ DECLINED: {username} ({email})")
    # No email sent to user
    return PlainTextResponse(f"User '{username}' declined. No account will be created.")

