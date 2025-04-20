from fastapi import FastAPI, Request , Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel,Field
from google.cloud import firestore
from uuid import uuid4
from typing import List, Optional
from fastapi import HTTPException , status ,APIRouter
from fastapi.responses import JSONResponse, RedirectResponse
from google.auth.transport import requests
import google.oauth2.id_token
import time



app = FastAPI()

# Serve static files like CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set template directory
templates = Jinja2Templates(directory="htmlpages")

firebase_db = firestore.Client()
firebase_request_adapter = requests.Request()


class Follower(BaseModel):
    username: str

class Following(BaseModel):
    username: str

class Comment(BaseModel):
    username: str
    comment: str
    time: str 

class Post(BaseModel):
    post_id: str
    Username: str             
    Date: str                 
    imageurl: str
    likes: int
    description: str
    comments: Optional[List[Comment]] = []

class User(BaseModel):
    name: str
    Username: str
    followers: Optional[List[Follower]] = []
    following: Optional[List[Following]] = []
    posts: Optional[List[str]] = []  
    joinedDate:str


class EmailRequest(BaseModel):
    username: str
 

class UsernameRequest(BaseModel):
    username: str
    name:str
    email:str
 

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("main-page.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.post("/checkandcreateuser")
async def checkandcreatenewuser(data: EmailRequest):
    # print("check user ", data)
    user_ref = firebase_db.collection('users').where('email', '==', data.username).limit(1).get()
    if not user_ref:
        firebase_db.collection('users').add({
                "name": "",
                "email":data.username,
                "joinedDate":time.strftime("%Y-%m-%dT%H:%M:%SZ",  time.gmtime()),
                "Username":"",
                "followers":[],
                "following":[],
                "posts":[]
            })
        print("user created")
    else:
        print("user already exist")
        pass
    return 0

@app.post("/getUser")
async def getUser(data: EmailRequest , response_class=JSONResponse):
    print("getting usrr")
    user_ref = firebase_db.collection('users').where('email', '==', data.username).limit(1).get()
    if not user_ref:
        return JSONResponse(content={"error": "User not found"}, status_code=404)
    else:
        user_data = user_ref[0].to_dict()
        return JSONResponse(content={"user": user_data}, status_code=200)
    

@app.post("/updateUserName")
async def updateUserName(data: UsernameRequest , response_class=JSONResponse):

    existing_user_query = firebase_db.collection('users').where('Username', '==', data.username).limit(1).get()

    if existing_user_query:
        # If username exists, return an error
        return JSONResponse(content={"error": "Username already exists"}, status_code=400)


    user_query = firebase_db.collection('users').where('email', '==', data.email).limit(1).get()
    if not user_query:
        return JSONResponse(content={"error": "User not found"}, status_code=404)

    user_doc = user_query[0]
    user_ref = firebase_db.collection('users').document(user_doc.id)

    # Now update name and Username
    user_ref.update({
        "name": data.name, 
        "Username": data.username
    })

    return JSONResponse(content={"message": "User updated successfully"}, status_code=200)

@app.post("/addpost")
async def checkandcreatenewuser(data: EmailRequest):
    print("check user ", data)
    user_ref = firebase_db.collection('users').where('Username', '==', data.username).limit(1).get()
    if not user_ref:
        firebase_db.collection('users').add({
                "name": data.username,
                "Username":data.username,
                "joinedDate":time.strftime("%Y-%m-%dT%H:%M:%SZ",  time.gmtime()),
                "followers":[],
                "following":[],
                "posts":[]
            })
        print("user created")
    else:
        print("user already exist")
        pass
    return 0