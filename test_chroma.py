import chromadb
client = chromadb.HttpClient(host="127.0.0.1", port=8080)
print("Client created.")
try:
    client.get_or_create_collection("test")
    print("Collection created.")
except Exception as e:
    print("Error:", e)
