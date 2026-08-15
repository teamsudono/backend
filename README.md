main_pipeline.py
        │
        ▼
FileExtensionValidator
        │
        ├─ 파일 존재 여부 확인
        │
        └─ 확장자 검증
           (.txt / .pdf / .docx)
        │
        ▼
stage1_analyzer.py
        │
        ├─ 원본 문서 읽기
        ├─ 사용자 / 파트너 국가 추출
        ├─ 시차 및 근무시간 자동 계산
        └─ OpenAI API 기반 회의 내용 분석
        │
        ▼
openai_file_result.json
        │
        ▼
stage2_todo.py
        │
        ├─ meeting_summary 추출
        ├─ OpenAI API 기반 To-Do 추출
        └─ Stage1 + Stage2 결과 병합
        │
        ├──────────────► todo_result.json
        │
        ▼
frontend_result.json
