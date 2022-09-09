# File: service.py

from fastapi import FastAPI

# That is the file where NeuralSearcher is stored
from neural_searcher import NeuralSearcher

app = FastAPI()

# Create an instance of the neural searcher
neural_searcher = NeuralSearcher(collection_name='test-tutorial')

@app.get("/api/search")
def search_startup(q: str):
    return {
        "result": neural_searcher.search(query=q)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)