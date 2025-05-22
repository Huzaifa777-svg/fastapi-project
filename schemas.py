from pydantic import BaseModel
from typing import Optional
import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class BookCreate(BaseModel):
    title: str
    author: str

class BookOut(BaseModel):
    id: int
    title: str
    author: str
    available: bool
    class Config:
        orm_mode = True

class BorrowRecordOut(BaseModel):
    id: int
    user_id: int
    book_id: int
    borrow_date: datetime.datetime
    return_date: Optional[datetime.datetime]
    class Config:
        orm_mode = True
