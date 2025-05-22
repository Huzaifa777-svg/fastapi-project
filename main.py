from fastapi import FastAPI, Depends, HTTPException
from database import Base, engine, SessionLocal
import models, schemas, auth
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext

app = FastAPI()
Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(auth.get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = get_password_hash(user.password)
    new_user = models.User(username=user.username, password=hashed, role=user.role)
    db.add(new_user)
    db.commit()
    return {"msg": "User registered"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(auth.get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/books/")
def add_book(book: schemas.BookCreate, user=Depends(auth.get_current_user), db: Session = Depends(auth.get_db)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can add books")
    new_book = models.Book(**book.dict())
    db.add(new_book)
    db.commit()
    return {"msg": "Book added"}

@app.get("/books/", response_model=list[schemas.BookOut])
def list_books(db: Session = Depends(auth.get_db)):
    return db.query(models.Book).all()

@app.post("/borrow/{book_id}")
def borrow_book(book_id: int, user=Depends(auth.get_current_user), db: Session = Depends(auth.get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book or not book.available:
        raise HTTPException(status_code=404, detail="Book not available")
    book.available = False
    record = models.BorrowRecord(user_id=user.id, book_id=book.id)
    db.add(record)
    db.commit()
    return {"msg": "Book borrowed"}

@app.post("/return/{book_id}")
def return_book(book_id: int, user=Depends(auth.get_current_user), db: Session = Depends(auth.get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    record = db.query(models.BorrowRecord).filter(models.BorrowRecord.book_id == book_id, models.BorrowRecord.user_id == user.id, models.BorrowRecord.return_date == None).first()
    if not record:
        raise HTTPException(status_code=404, detail="No active borrow record found")
    record.return_date = __import__("datetime").datetime.utcnow()
    book.available = True
    db.commit()
    return {"msg": "Book returned"}

