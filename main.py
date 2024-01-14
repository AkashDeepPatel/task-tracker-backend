from fastapi import FastAPI, Depends, Header, Query, File, UploadFile
import firebase_admin
import pyrebase
from firebase_admin import credentials, auth, firestore, storage
from fastapi import HTTPException, Body, Path
from models.user import UserData, UserCred
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse

security = HTTPBearer()

firebaseConfig = {
  "apiKey": "AIzaSyAjMwmIac0EU54t8zI95IVzrJMZXRxLIfs",
  "authDomain": "task-tracker-c56ce.firebaseapp.com",
  "databaseURL": "https://task-tracker-c56ce-default-rtdb.firebaseio.com",
  "projectId": "task-tracker-c56ce",
  "storageBucket": "task-tracker-c56ce.appspot.com",
  "messagingSenderId": "246476218105",
  "appId": "1:246476218105:web:aff46ad4e61ab634448c28",
  "measurementId": "G-ZZNVR66K10"
}

firebase = pyrebase.initialize_app(firebaseConfig)

app = FastAPI()

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)


# Access the Firestore database
db = firestore.client()

# Define a Firestore collection for users
users_collection = db.collection("users")

#final

# Dependency to authenticate the user using Firebase and get UID
def get_firebase_uid(access_token: str = Header(..., title="access-token")):
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(access_token)
        return decoded_token.get("uid")
    except Exception as e:
        print(f"Exception during token verification: {e}")
        raise HTTPException(status_code=401, detail="Invalid access token")
                        
@app.get("/check-user")
async def check_user(email: str):
    email = email
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    try:
        user = auth.get_user_by_email(email)
        return {"user_exist": True}
    except Exception as e:
            return {"user_exist": False}
    
@app.post("/register")
async def signup(user_data: UserData):
    name = user_data.username
    email = user_data.email
    password = user_data.password
    phone_number = user_data.phone_number
    profile_picture = user_data.profile_picture
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    try:
        # user = auth.create_user(email=email, password=password, display_name = name)
        user = firebase.auth().create_user_with_email_and_password(email = email, password= password)
        user_datas = {
            "username": name,
            "email": email,
            "phone_number": phone_number,
            "profile_picture": profile_picture
        }
        decoded_token = auth.verify_id_token(user['idToken'])
        users_collection.document(decoded_token.get('uid')).set(user_datas)
        return {"message": "User created successfully", "token": user['idToken']}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/login", response_model=dict)
def login(user_credentials: UserCred):
    try:
        user = firebase.auth().sign_in_with_email_and_password(email=user_credentials.email, password=user_credentials.password)
        custom_token = user["idToken"]
        print(custom_token)
        # id_token = auth.sign_in_with_custom_token(custom_token)['idToken']
        return {"id_token": custom_token}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail="Invalid email or password")

# Route to upload profile picture
# @app.post("/upload/profile-picture", response_class=JSONResponse)
# async def upload_profile_picture(
#     file: UploadFile = File(...),
#     uid: str = Depends(get_firebase_uid)
# ):
#     try:
#         # Ensure the file is an image
#         if not file.content_type.startswith("image/"):
#             raise HTTPException(status_code=400, detail="Only images are allowed")

#         # Set the path to store the profile picture in Firebase Storage
#         storage_path = f"profile_pictures/{uid}/{file.filename}"

#         # Upload the file to Firebase Storage
#         bucket = storage.bucket()
#         blob = bucket.blob(storage_path)
#         blob.upload_from_file(file.file, content_type=file.content_type)

#         # Get the public URL of the uploaded file
#         download_url = blob.generate_signed_url(expiration=3600)  # URL expires in 1 hour

#         return {"message": "Profile picture uploaded successfully", "download_url": download_url}

#     except Exception as e:
#         print(f"Error uploading profile picture: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")
    

# Dependency to get user details from Firestore using UID
@app.get("/user-details")
def get_user_details_from_firestore(uid: str = Depends(get_firebase_uid)):
    user_doc_ref = db.collection('users').document(uid)
    user_doc = user_doc_ref.get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        return user_data
    else:
        raise HTTPException(status_code=404, detail="User not found")