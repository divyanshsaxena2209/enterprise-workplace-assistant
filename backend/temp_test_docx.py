import asyncio
from app.services.knowledge_rag import process_and_store_document
import os

try:
    from docx import Document
    document = Document()
    document.add_paragraph('Test Docx File')
    document.save('test_mock.docx')

    print("Testing processing...")
    result = process_and_store_document('test_mock.docx')
    print("Result:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    if os.path.exists('test_mock.docx'):
        os.remove('test_mock.docx')
