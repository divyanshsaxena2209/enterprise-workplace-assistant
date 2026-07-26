import requests

url = "http://localhost:8003/api/v1/knowledge/upload"
with open("test.txt", "w") as f:
    f.write("Hello World!")
    
files = {'file': ('test.pdf', open('test.txt', 'rb'), 'application/pdf')}
print("Sending request to port 8003...")
try:
    res = requests.post(url, files=files, timeout=30)
    print(res.status_code, res.text)
except Exception as e:
    print("Error:", e)
