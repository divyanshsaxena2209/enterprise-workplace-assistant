import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/backend")

from app.services.knowledge_rag import retrieve_and_answer
import traceback
try:
    print(retrieve_and_answer("explain onboarding process like im a 5 year old"))
except Exception as e:
    traceback.print_exc()
