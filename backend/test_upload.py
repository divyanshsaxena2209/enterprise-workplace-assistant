import requests
url = 'http://localhost:8564/api/v1/knowledge/upload'
files = {'file': ('test_resume.pdf', open('test_resume.pdf', 'rb'), 'application/pdf')}
headers = {}
print(f"Sending POST to {url}")
try:
    response = requests.post(url, files=files, headers=headers)
    print(response.status_code)
    print(response.json())
except Exception as e:
    print(e)
