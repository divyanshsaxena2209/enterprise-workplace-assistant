from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

try:
    embeddings = FastEmbedEmbeddings()
    vector = embeddings.embed_query("Hello world")
    print("Success! Dimensions:", len(vector))
except Exception as e:
    print("Error:", e)
