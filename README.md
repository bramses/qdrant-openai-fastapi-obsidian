TODO:
- keep a stable collection of data
- upsert any filenames that are not in the collection
   - go over each filename in the directory and skip if it's already in the collection
   - if not, create an embedding and upload it to the collection
   - if something is deleted, remove it from the collection
- host the service on a server
- create an ios shortcut that calls the service

# Running

`python service.py`

in another tab

```
docker run -p 6333:6333 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```