from pydantic import BaseModel

class User(BaseModel):
    fullname:str
    email:str
    password:str

    class Config:
        json_schema_extra={
            "example":{
            "fullname": "username",
            "email": "sample@gmail.com",
            "password":"samplepassword123"
        }
    }