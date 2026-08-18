import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/backend")

from app.services.resume_parser import ResumeParserService

def test():
    parser = ResumeParserService()
    raw_text = """
    John Doe
    Email: john.doe@example.com
    Phone: 123-456-7890
    Experience: Software Engineer at Google (2020-2022). Developed backend microservices using Python and Go.
    Education: BS in Computer Science from MIT (2016-2020).
    Skills: Python, Go, Docker, Kubernetes
    """
    try:
        res = parser.parse_with_ai(raw_text)
        print("Parsed Data:", res.model_dump_json(indent=2))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test()
