# Import client library
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from qdrant_client import QdrantClient
import os
import openai
from dotenv import load_dotenv
load_dotenv()


openai.organization = os.getenv("OPENAI_ORG")
openai.api_key = os.getenv("OPENAI_API_KEY")


class NeuralSearcher:

    qdrant_client = None

    def __init__(self, collection_name):
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(host='localhost', port=6333)
        # my_collection_info = self.qdrant_client.http.collections_api.get_collection(
        #     collection_name)

        # create_collection(collection_name=collection_name, qdrant_client=self.qdrant_client)
        # filenames = os.listdir("data")
        # # print(filenames)
        # embeddings = create_embeddings(filenames)

        # vectors = map(lambda x: x["embedding"], embeddings)
        # vectors = list(vectors)
        # payload = map(lambda x: { "filename": x }, filenames)

        # upload_data(collection_name=collection_name, vectors=vectors, payload=payload, qdrant_client=self.qdrant_client)

    def upload_data(self):
        filenames = os.listdir("data")
        embeddings = create_embeddings(filenames)
        vectors = map(lambda x: x["embedding"], embeddings)
        vectors = list(vectors)
        payload = map(lambda x: {"filename": x}, filenames)
        upload_data(collection_name=self.collection_name, vectors=vectors,
                    payload=payload, qdrant_client=self.qdrant_client)

    def search(self, query, top=10):
        return search(collection_name=self.collection_name, query=query, top=top, qdrant_client=self.qdrant_client)

    def scroll(self, filename):
        return self.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="filename",
                        match=MatchValue(
                            value="{filename}".format(filename=filename))
                    ),
                ]
            ),
            limit=1,
            with_payload=True,
            with_vector=False,
        )

    def get_all(self):
        points = []
        next_page_offset = 0


        while True:
            res = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True,
                with_vector=False,
                offset=next_page_offset
            )
            
            points.append(res[0])
            next_page_offset = res[1]


            if res[1] == None:
                break


        # compare with files in data folder
        points_list = list(points[0])
        # print(list(points_list)[0].payload["filename"])
        filenames = recursive("data", [])
        point_filenames = list(map(lambda x: x.payload["filename"], points_list))
        ins, delt = compare_lists(filenames, point_filenames)
        print("Inserted: ", ins)
        print("Deleted: ", delt)

        
        return points

# https://stackoverflow.com/questions/49273647/python-recursive-function-by-using-os-listdir
def recursive(dir, all_files=[]):
    files = os.listdir(dir)
    for obj in files:
        
        if os.path.isfile(os.path.join(dir,obj)):
            print ("File : "+os.path.join(dir,obj))
            all_files.append(obj)
        elif os.path.isdir(os.path.join(dir,obj)):
            print('called on dir: ', os.path.join(dir,obj))
            recursive(os.path.join(dir, obj), all_files)
        else:
            print('Not a directory or file %s' % (os.path.join(dir, obj)))
    
    return all_files

def compare_lists(filenames, points):
    to_insert = []
    to_delete = []

    print(filenames)
    print(points)

    for filename in filenames:
        if filename not in points:
            to_insert.append(filename)
        
    for point in points:
        if point not in filenames:
            to_delete.append(point)
    
    return to_insert, to_delete

def create_embeddings(query, model="text-search-davinci-doc-001"):
    response = openai.Embedding.create(
        model=model,
        input=query
    )

    if not response.data:
        print("No data returned")
        return
    return response.data


def create_collection(collection_name, qdrant_client=None):
    qdrant_client.recreate_collection(
        collection_name=collection_name,
        vector_size=12288,
        distance="Cosine"
    )


def upload_data(collection_name, vectors, payload, qdrant_client=None):
    qdrant_client.upload_collection(
        collection_name=collection_name,
        vectors=vectors,
        payload=payload,
        ids=None,  # Vector ids will be assigned automatically
        batch_size=256  # How many vectors will be uploaded in a single request?
    )


def search(collection_name, query, top=10, qdrant_client=None):

    embeddings = create_embeddings(
        query, model="text-search-davinci-query-001")
    vectors = map(lambda x: x["embedding"], embeddings)
    vectors = list(vectors)
    vector = vectors[0]

    # Use `vector` for search for closest vectors in the collection
    search_result = qdrant_client.search(
        collection_name=collection_name,
        query_vector=vector,
        query_filter=None,  # We don't want any filters for now
        limit=top  # 5 the most closest results is enough
    )
    # `search_result` contains found vector ids with similarity scores along with the stored payload
    # In this function we are interested in payload only
    payloads = [hit.payload for hit in search_result]
    return payloads


'''
TODO:
- keep a stable collection of data
- upsert any filenames that are not in the collection
   - go over each filename in the directory and skip if it's already in the collection
   - if not, create an embedding and upload it to the collection
   - if something is deleted, remove it from the collection
- host the service on a server
- create an ios shortcut that calls the service
'''
