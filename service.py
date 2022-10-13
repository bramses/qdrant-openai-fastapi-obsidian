# File: service.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",
    "localhost:3000"
]


# That is the file where NeuralSearcher is stored
from neural_searcher import NeuralSearcher, open_file_in_obsidian, recursive
from typing import List, Union
from pydantic import BaseModel
import os
from dotenv import load_dotenv
load_dotenv()

'''BEGIN OAUTH'''
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token or token != "bram":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


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
'''END OAUTH'''

@app.get("/")
async def main():
    return {"message": "Hello World"}

class Item(BaseModel):
    filenames: List[str]

# Create an instance of the neural searcher
neural_searcher = NeuralSearcher(collection_name='to-go-brain', filenames=recursive("data", []))

# search for k results in the collection with the given query
@app.get("/api/search")
def search_startup(q: str, vault: str, current_user: User = Depends(get_current_user)):
    print(current_user)
    search_results = neural_searcher.search(query=q)
    return {
        "result": search_results,
        "obsidianURIS": list(map(lambda x: open_file_in_obsidian(vault="{vault}".format(vault=vault), filename=x["filename"]), search_results))
    }


# get a single file from the collection by filename
@app.get("/api/scroll")
def scroll_startup(filename: str):
    return {
        "result": neural_searcher.scroll(filename=filename)
    }

# get all the filenames in the collection
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


@app.get("/api/create")
def create(collection_name: str):
    return {
        "result": neural_searcher.create_collection(collection_name=collection_name)
    }

# upload a list of filenames to the neural searcher
@app.post("/api/upload_filenames")
def upload_filenames(files: Item):
    return {
        "result": neural_searcher.upload_filenames(filenames=files.filenames)
    }

# dry run file comparison
@app.post("/api/dry_run")
def dry_run(files: Item):
    return {
        "result": neural_searcher.dry_run(filenames=files.filenames)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)