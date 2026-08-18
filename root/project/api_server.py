import json
import os
import tempfile
import threading
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import auth
import models
from database import get_db, init_db
from file_validator import FileExtensionValidator
from stage1_analyzer import OpenAIFileAnalyzer
from stage2_todo import OpenAITodoExtractor

app = FastAPI(title="Meeting Summary API")
app.include_router(auth.router)

init_db()

_origins_env = os.environ.get("ALLOWED_ORIGINS", "*").strip()
_allow_origins = ["*"] if _origins_env == "*" else [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_origin_regex=os.environ.get("ALLOWED_ORIGIN_REGEX"),
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipeline_lock = threading.Lock()

MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_MB", "20")) * 1024 * 1024


@app.post("/api/meeting-summary")
def create_meeting_summary(
    file: UploadFile = File(...),
    lang: str = Form("en"),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    suffix = Path(file.filename or "").suffix.lower()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / (file.filename or f"upload{suffix}")

        written = 0
        with tmp_path.open("wb") as out_file:
            while chunk := file.file.read(1024 * 1024):
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"파일 용량이 너무 큽니다. 최대 {MAX_UPLOAD_BYTES // (1024 * 1024)}MB까지 업로드할 수 있습니다.",
                    )
                out_file.write(chunk)

        validation = FileExtensionValidator(tmp_path).validate_document()

        if not validation["success"]:
            raise HTTPException(status_code=400, detail=validation["message"])

        with _pipeline_lock:
            try:
                result = _run_pipeline(tmp_path)
            except FileNotFoundError as e:
                raise HTTPException(status_code=500, detail=str(e))
            except Exception as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"회의 분석 중 오류가 발생했습니다: {e}",
                )

    meeting = models.Meeting(
        user_id=current_user.id,
        filename=file.filename or "meeting",
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return JSONResponse(content={**result, "meeting_id": meeting.id})


@app.get("/api/meetings")
def list_meetings(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.Meeting)
        .filter(models.Meeting.user_id == current_user.id)
        .order_by(models.Meeting.created_at.desc())
        .all()
    )
    return [
        {"id": m.id, "filename": m.filename, "created_at": m.created_at.isoformat()}
        for m in rows
    ]


@app.get("/api/meetings/{meeting_id}")
def get_meeting(
    meeting_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="회의 기록을 찾을 수 없습니다.")
    if meeting.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 회의 기록에 접근할 권한이 없습니다.")

    return {
        "id": meeting.id,
        "filename": meeting.filename,
        "created_at": meeting.created_at.isoformat(),
        "result": json.loads(meeting.result_json),
    }


def _run_pipeline(input_file_path: Path) -> dict:
    analyzer = OpenAIFileAnalyzer(input_file_path=input_file_path)
    analyzer.clear_previous_result()

    if not analyzer.openfile():
        raise RuntimeError("Stage1 파일 불러오기 실패")
    if not analyzer.analyze_file():
        raise RuntimeError("Stage1 OpenAI 분석 실패")
    if not analyzer.save_result():
        raise RuntimeError("Stage1 결과 저장 실패")

    extractor = OpenAITodoExtractor()
    extractor.clear_previous_result()

    if not extractor.openfile():
        raise RuntimeError("Stage2 입력 파일 불러오기 실패")
    if not extractor.analyze_file():
        raise RuntimeError("Stage2 OpenAI 분석 실패")
    if not extractor.save_result():
        raise RuntimeError("Stage2 결과 저장 실패")
    if not extractor.merge_for_frontend():
        raise RuntimeError("최종 결과 병합 실패")

    with extractor.final_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/health")
def health():
    return {"status": "ok"}
