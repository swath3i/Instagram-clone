from fastapi import FastAPI, Request , Form, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel,Field
from google.cloud import firestore , storage
from uuid import uuid4
from typing import List, Optional
from fastapi import HTTPException , status ,APIRouter
from fastapi.responses import JSONResponse, RedirectResponse
from google.auth.transport import requests
import google.oauth2.id_token
import time
import starlette.status as status
import local_constants
import uuid
from datetime import datetime

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
    filename: str
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
 

def createPost(filename, user, postdescription):
    post_id = str(uuid.uuid4())  # generate unique post ID
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # format current time
    firebase_db.collection('Post').add({
                "post_id": post_id,
                "Username": user['Username'],  
                "email":user['email'],        
                "Date": current_time,            
                "filename": filename,
                "likes": 0,
                "description": postdescription,
                "comments":[]
            })
    print("post ",{
                "post_id": post_id,
                "Username": user['Username'],  
                "email":user['email'],        
                "Date": current_time,            
                "filename": filename,
                "likes": 0,
                "description": postdescription,
                "comments":[]
            })


def getUserPosts(username):
    posts = []
    posts_ref = firebase_db.collection('Post')
    query = posts_ref.where('Username', '==', username).stream()
    for post in query:
        posts.append(post.to_dict())

    return posts



def addDirectory(directory_name):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.blob(directory_name)
    blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')

def addFile(file , user , postdescription):
    print("inside add file")
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    # print(file)
    blob = storage.Blob(file.filename, bucket)
    blob.upload_from_file(file.file)
    createPost(file.filename,user, postdescription)

def blobList(prefix):
    print("local_constants.PROJECT_NAME ",local_constants.PROJECT_NAME)
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    return storage_client.list_blobs(local_constants.PROJECT_STORAGE_BUCKET, prefix=prefix)

def downloadBlob(filename):
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)
    blob = bucket.get_blob(filename)
    return blob.download_as_bytes()
    
def getuser(user_token):
    print("inside get user function")
    user = firebase_db.collection("users").document(user_token['user_id'])
    if not user.get().exists:
        user_data = {
            'name':'John Doe'
        }
        firebase_db.collection('users').document(user_token['user_id']).set(user_data)

    return user

def validateFirebaseToken(id_token):
    if not id_token:
        return None
    user_token = None 
    try:
        user_token = google.oauth2.id_token.verify_firebase_token(id_token, firebase_request_adapter)
    except ValueError as e:
        print(str(e))

    return user_token

def getuserfromemail(email):
    user_ref = firebase_db.collection('users').where('email', '==', email).limit(1).get()
    user_data = {
            'name':'John Doe'
        }
    if not user_ref:
        return user_data
    else:
        user_data = user_ref[0].to_dict()
        return user_data

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    id_token = request.cookies.get('token')
    error_message = "No error here"
    user_token = None
    user = None

    print("inside get")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return templates.TemplateResponse("main-page.html",{'request':request, 'user_token':None , 'error_message':None , 'user_info':None})
    
    print("user validated")
    file_list = []
    directory_list = []

    blobs = blobList(None)
    print("after blobs")
    for blob in blobs:
        if blob.name[-1] == "/":
            directory_list.append(blob)
        else:
            file_list.append(blob)
    print("after blob") 
    user = getuser(user_token).get()
    return templates.TemplateResponse("main-page.html", {"request": request, 'user_token':user_token , 'error_message':error_message , 'user_info':user, 'file_list':file_list,'directory_list':directory_list})

@app.get("/dashboard", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/test", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})

@app.get("/testing", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("testing.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/search", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})

@app.get("/userprofile/{username}", response_class=HTMLResponse)
async def renderuserprofile(request: Request, username:str):
    return templates.TemplateResponse("userprofile.html", {"request": request, 'user':username})


@app.get("/followers", response_class=HTMLResponse)
async def renderfollowers(request: Request):
    id_token = request.cookies.get('token')
    error_message = "No error here"
    user_token = None
    user = None

    print("inside get")
    user_token = validateFirebaseToken(id_token)
    print("inside user toekn ",user_token)

    if not user_token:
        return templates.TemplateResponse("main-page.html",{'request':request, 'user_token':None , 'error_message':None , 'user_info':None})
    
    return templates.TemplateResponse("followers.html", {"request": request , 'user_email':user_token['email']})

@app.get("/following", response_class=HTMLResponse)
async def renderfollowing(request: Request):
    id_token = request.cookies.get('token')
    error_message = "No error here"
    user_token = None
    user = None

    user_token = validateFirebaseToken(id_token)

    print("inside user toekn ",user_token)
    if not user_token:
        return templates.TemplateResponse("main-page.html",{'request':request, 'user_token':None , 'error_message':None , 'user_info':None})
    
    return templates.TemplateResponse("following.html", {"request": request , 'user_email':user_token['email']})


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

@app.post("/getPostsOfUser")
async def getPostsOfUser(data: EmailRequest, response_class=JSONResponse):
    print("getting posts of user")
    posts_ref = firebase_db.collection('Post').where('email', '==', data.username).get()
    if not posts_ref:
        posts = []
    else:
        posts = [doc.to_dict() for doc in posts_ref]
    return JSONResponse(content={"posts": posts}, status_code=200)

    

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


@app.get("/getallusers")
async def get_all_users():
    user_ref = firebase_db.collection('users')
    docs = user_ref.stream()
    users = []
    
    for doc in docs:
        user_data = doc.to_dict()
        selected_data = {
            "username": user_data.get("Username"),
            "email": user_data.get("email"),
            "profileName":user_data.get("name")
        }
        users.append(selected_data)
    
    return {"users": users}


@app.post("/add-directory", response_class=RedirectResponse)
async def addDirectoryHandler(request: Request):
    id_token = request.cookies.get("token")
    user_token= validateFirebaseToken(id_token)
    if not user_token:
      return RedirectResponse('/')
    form = await request.form()
    dir_name = form['dir_name']
    if dir_name == '' or dir_name[-1] != '/':
        return RedirectResponse('/')
    addDirectory(dir_name)
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)


# handler that will take in a filename to download and will serve it to the user
@app.post("/download-file", response_class=Response)
async def downloadFileHandler(request: Request):
    # there should be a token. Validate it and if invalid then redirect back to / as a basic security measure 
    id_token= request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    if not user_token:
        return RedirectResponse('/')
    # pull the form data and see what filename we have for download
    form = await request.form()
    filename = form['filename']
    return Response (downloadBlob(filename))



@app.post("/upload-file", response_class=RedirectResponse)
async def uploadFileHandler(request: Request):
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)
    # print("user token ",user_token)
    if not user_token:
        return RedirectResponse('/test')
    form = await request.form()
    if form['file_name'].filename == '':
        return RedirectResponse('/test', status_code=status.HTTP_302_FOUND)
    
    user = getuserfromemail(user_token['email'])
    
    addFile(form['file_name'],user,form['description'])
    print(".filename = ",form['file_name'].filename) 
    return RedirectResponse('/test', status_code=status.HTTP_302_FOUND)


@app.post("/getuserposts", response_class=JSONResponse)
async def getUserPostsHandler(request: Request, username: str = Form(...)):
    id_token = request.cookies.get("token")
    user_token = validateFirebaseToken(id_token)

    if not user_token:
        return RedirectResponse('/login', status_code=status.HTTP_302_FOUND)

    posts = getUserPosts(username)
    
    return JSONResponse(content={"posts": posts})


@app.post("/addCommentToPost", response_class=JSONResponse)
async def addCommentToPost(request: Request):
    data = await request.json()  # Parse the incoming JSON body
    # comment = data.get("comment")  # Extract the 'comment' object
    # print("Received comment:", comment)  # Print the comment
    new_comment_data = data.get("comment")
    if not new_comment_data:
        return JSONResponse(content={"error": "No comment provided"}, status_code=400)

    post_id = new_comment_data.get("activePostId")
    if not post_id:
        return JSONResponse(content={"error": "No post ID provided"}, status_code=400)

    # Fetch the post document from Firestore
    posts_ref = firebase_db.collection("Post")
    query = posts_ref.where("post_id", "==", post_id).limit(1)
    results = query.stream()

    post_doc = None
    post_doc_id = None
    for doc in results:
        post_doc = doc.to_dict()
        post_doc_id = doc.id
        break

    if not post_doc:
        return JSONResponse(content={"error": "Post not found"}, status_code=404)

    # Prepare the new comment
    new_comment = {
        "username": new_comment_data["email"],
        "comment": new_comment_data["text"],
        "time": new_comment_data["timestamp"],
    }

    # Update the comments list
    comments = post_doc.get("comments", [])
    comments.append(new_comment)

    # Save updated comments back to Firestore
    post_ref = firebase_db.collection("Post").document(post_doc_id)
    post_ref.update({
        "comments": comments
    })

    return {"message": "Comment added successfully", "new_comment": new_comment}


