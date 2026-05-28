from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from app.db.supabase import get_db
from app.services.transcription_service import transcribe_audio_file
from app.services.meeting_intelligence import analyze_meeting
from app.services.rag_service import RAGService
import uuid

router = APIRouter(prefix="/meetings", tags=["Meetings"])

def process_meeting_background(meeting_id: str, file_bytes: bytes, filename: str, db):
    try:
        # 1. Update status to Transcribing
        db.table("meetings").update({"status": "Transcribing"}).eq("id", meeting_id).execute()
        
        # 2. Transcribe Audio
        transcript = transcribe_audio_file(file_bytes, filename)
        
        # 3. Update status to Analyzing
        db.table("meetings").update({"status": "Analyzing"}).eq("id", meeting_id).execute()
        
        # 4. Generate AI Summary & Tasks
        analysis = analyze_meeting(transcript)
        
        # 5. Save Transcript & Summary to DB
        db.table("transcripts").insert({
            "meeting_id": meeting_id,
            "raw_text": transcript,
            "executive_summary": analysis.executive_summary,
            "decisions_made": analysis.decisions_made,
            "discussion_points": analysis.discussion_points
        }).execute()
        
        # 6. Save Tasks to DB
        tasks_to_insert = []
        for task in analysis.action_items:
            tasks_to_insert.append({
                "meeting_id": meeting_id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "due_date": task.deadline # Assume parsing handles ISO format for now
            })
        if tasks_to_insert:
            db.table("meeting_tasks").insert(tasks_to_insert).execute()
            
        # 7. Ingest into RAG Pipeline
        # We index the transcript so the Knowledge Assistant can query it.
        RAGService.ingest_document(
            document_id=f"meeting_{meeting_id}", 
            text=transcript, 
            metadata={"type": "meeting", "meeting_id": meeting_id}
        )
        
        # 8. Complete
        db.table("meetings").update({"status": "Completed"}).eq("id", meeting_id).execute()
    except Exception as e:
        db.table("meetings").update({"status": "Failed"}).eq("id", meeting_id).execute()
        print(f"Background meeting processing failed: {str(e)}")


@router.post("/upload")
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    department: str = Form(None),
    db=Depends(get_db)
):
    try:
        file_bytes = await file.read()
        
        # 1. Create Meeting Record
        meeting_data = {
            "title": title,
            "department": department,
            "audio_file_url": f"/mock/storage/{file.filename}",
            "status": "Uploading"
        }
        res = db.table("meetings").insert(meeting_data).execute()
        meeting_id = res.data[0]["id"]
        
        # 2. Trigger background processing
        background_tasks.add_task(process_meeting_background, meeting_id, file_bytes, file.filename, db)
        
        return {"status": "success", "meeting_id": meeting_id, "message": "Meeting uploaded and processing started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def get_meetings(db=Depends(get_db)):
    try:
        res = db.table("meetings").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{meeting_id}/details")
def get_meeting_details(meeting_id: str, db=Depends(get_db)):
    try:
        meeting = db.table("meetings").select("*").eq("id", meeting_id).execute().data[0]
        transcript = db.table("transcripts").select("*").eq("meeting_id", meeting_id).execute().data
        tasks = db.table("meeting_tasks").select("*").eq("meeting_id", meeting_id).execute().data
        
        return {
            "meeting": meeting,
            "transcript_summary": transcript[0] if transcript else None,
            "tasks": tasks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
