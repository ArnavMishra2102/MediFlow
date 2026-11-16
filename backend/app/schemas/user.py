from pydantic import BaseModel, EmailStr,Field,ConfigDict

#data required when registering a new user

class UserCreate(BaseModel):
    full_name:str=Field(min_length=1,max_length=100)
    email:EmailStr
    password:str=Field(min_length=8)

#data required when logging in

class UserLogin(BaseModel):
    email:EmailStr
    password:str=Field(min_length=8)

#data returned by the API

class UserResponse(BaseModel):
    id:int
    full_name:str
    email:EmailStr
    role:str

    model_config=ConfigDict(from_attributes=True)