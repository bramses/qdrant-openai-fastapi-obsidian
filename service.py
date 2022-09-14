# File: service.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# That is the file where NeuralSearcher is stored
from neural_searcher import NeuralSearcher, open_file_in_obsidian, recursive
from typing import List, Union
from pydantic import BaseModel


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Item(BaseModel):
    filenames: List[str]

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

def fake_hash_password(password: str):
    return "fakehashed" + password



class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str

app = FastAPI(debug=True)


def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
    )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


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
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Create an instance of the neural searcher
neural_searcher = NeuralSearcher(collection_name='to-go-brain', filenames=recursive("data", []))

@app.get("/api/search")
def search_startup(q: str, vault: str, token: str = Depends(oauth2_scheme)):
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