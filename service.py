# File: service.py
from fastapi import FastAPI
# That is the file where NeuralSearcher is stored
from neural_searcher import NeuralSearcher, open_file_in_obsidian, recursive
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    filenames: List[str]

app = FastAPI()

# Create an instance of the neural searcher
neural_searcher = NeuralSearcher(collection_name='test-tutorial', filenames=recursive("data", []))

@app.get("/api/search")
def search_startup(q: str, vault: str):
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


@app.post("/api/upload_filenames")
def upload_filenames(files: Item):
    return {
        "result": neural_searcher.upload_filenames(filenames=files.filenames)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)