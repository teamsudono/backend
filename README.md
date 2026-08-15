Backend Pipeline

회의 문서 파일을 입력받아 파일 형식을 검증한 뒤, OpenAI API를 활용해 회의 내용 분석 → To-Do 추출 → 프론트엔드용 JSON 생성까지 자동으로 처리하는 백엔드 파이프라인입니다.

Pipeline

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

⸻

Execution Flow

main_pipeline.py를 실행하면 아래 순서로 전체 분석이 자동 진행됩니다.

파일 검증
   ↓
Stage 1
   ↓
openai_file_result.json
   ↓
Stage 2
   ↓
todo_result.json
   ↓
frontend_result.json

Stage 0 — File Validation

입력된 회의 문서가 실제로 존재하는지 확인하고 지원하는 파일 형식인지 검증합니다.

지원 형식:

.txt
.pdf
.docx

지원하지 않는 파일 형식이 입력되면 파이프라인을 종료합니다.

⸻

Stage 1 — Meeting Analysis

stage1_analyzer.py에서 회의 원본 문서를 분석합니다.

주요 기능:

원본 문서 텍스트 추출
        ↓
사용자 / 파트너 국가 정보 확인
        ↓
현재 시점 기준 시차 계산
        ↓
업무 시간 중 겹치는 시간 계산
        ↓
OpenAI API 회의 분석
        ↓
회의 요약 및 협업 정보 생성

생성 파일:

openai_file_result.json

주요 결과:

cultural_analysis
communication_style
time_zone_analysis
meeting_summary
risk_notes

⸻

Stage 2 — To-Do Extraction

stage2_todo.py는 Stage 1에서 생성된 meeting_summary를 기반으로 실행 항목을 추출합니다.

openai_file_result.json
        ↓
meeting_summary 추출
        ↓
OpenAI API 분석
        ↓
To-Do / 담당자 / 마감일 추출
        ↓
todo_result.json

추출되는 정보:

{
  "task": "작업 내용",
  "assignee": "담당자",
  "due_date": "마감일"
}

⸻

Final Merge

Stage 1과 Stage 2 결과를 병합하여 프론트엔드에서 사용할 최종 JSON 파일을 생성합니다.

Stage 1 Result
      +
Stage 2 Result
      ↓
frontend_result.json

최종 결과 구조 예시:

{
  "meeting_summary": {
    "agreed": [],
    "disputed_or_pending": []
  },
  "time_zone_analysis": {
    "time_difference": "",
    "overlap_hours": "",
    "recommended_meeting_time": ""
  },
  "caution_notes": {
    "cultural_analysis": [],
    "communication_style": {},
    "risk_notes": []
  },
  "todo_list": [
    {
      "task": "",
      "assignee": "",
      "due_date": "",
      "done": false
    }
  ]
}

⸻

Project Structure

/root/project/
│
├── main_pipeline.py
│
├── file_validator.py
│
├── stage1_analyzer.py
│
├── stage2_todo.py
│
├── api_key.txt
│
├── analyze_file.txt
│
├── openai_file_result.json
│├── todo_result.json
│
└── frontend_result.json

File Description

File	Description
main_pipeline.py	전체 분석 파이프라인 실행
file_validator.py	파일 존재 여부 및 확장자 검증
stage1_analyzer.py	회의 내용, 문화, 시차 분석
stage2_todo.py	To-Do / 담당자 / 마감일 추출
api_key.txt	OpenAI API Key 저장
analyze_file.txt	기본 분석 대상 회의 문서
openai_file_result.json	Stage 1 분석 결과
todo_result.json	Stage 2 To-Do 분석 결과
frontend_result.json	프론트엔드 전달용 최종 결과

⸻

Installation

필요한 Python 패키지를 설치합니다.

pip install openai pytz babel pypdf python-docx

⸻

API Key

OpenAI API Key는 코드에 직접 작성하지 않고 별도의 api_key.txt에서 불러옵니다.

sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

보안을 위해 api_key.txt는 GitHub에 업로드하지 않습니다.

.gitignore

api_key.txt
__pycache__/
*.pyc
.env

⸻

Usage

기본 입력 파일인 analyze_file.txt를 사용할 경우:

cd /root/project
python3 main_pipeline.py

다른 TXT 파일을 분석할 경우:

python3 main_pipeline.py /root/upload/meeting.txt

PDF:

python3 main_pipeline.py /root/upload/meeting.pdf

DOCX:

python3 main_pipeline.py /root/upload/meeting.docx

⸻

Output

정상적으로 실행되면 최종적으로 다음 파일이 생성됩니다.

openai_file_result.json
todo_result.json
frontend_result.json

프론트엔드에서는 최종적으로 아래 파일을 사용합니다.

frontend_result.json

frontend_result.json은 회의 요약, 시차 분석, 문화적 주의사항, 커뮤니케이션 스타일, 리스크 및 To-Do 정보를 하나의 JSON으로 통합한 최종 결과입니다.
