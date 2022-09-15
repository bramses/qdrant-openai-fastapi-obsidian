# File: service.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# That is the file where NeuralSearcher is stored
from neural_searcher import NeuralSearcher, open_file_in_obsidian, recursive
from typing import List, Union
from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_users_db = {
    os.getenv("USERNAME"): {
        "username": os.getenv("USERNAME"),
        "password": os.getenv("PASSWORD"),
    }

}


class User(BaseModel):
    username: str


class UserInDB(User):
    password: str

app = FastAPI(debug=True)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)

    if not user.password == form_data.password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

class Item(BaseModel):
    filenames: List[str]

# Create an instance of the neural searcher
neural_searcher = NeuralSearcher(collection_name='to-go-brain', filenames=recursive("data", []))

@app.get("/api/search")
def search_startup(q: str, vault: str, current_user: User = Depends(get_current_user)):
    search_results = neural_searcher.search(query=q)
    return {
        "result": search_results,
        "obsidianURIS": list(map(lambda x: open_file_in_obsidian(vault="{vault}".format(vault=vault), filename=x["filename"]), search_results))
    }


@app.get("/api/scroll")
def scroll_startup(filename: str):
    return {
        "result": neural_searcher.scroll(filename=filename)
    }

@app.get("/api/get_all")
def get_all():
    return {
        "result": neural_searcher.get_all()
    }


@app.get("/api/recreate")
def recreate():
    return {
        "result": neural_searcher.recreate_collection_from_scratch()
    }

@app.post("/api/upload_filenames")
def upload_filenames(files: Item):
    return {
        "result": neural_searcher.upload_filenames(filenames=files.filenames)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)