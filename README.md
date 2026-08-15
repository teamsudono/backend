# Backend

회의 문서를 입력받아 파일 형식을 검증한 후, OpenAI API를 활용하여 **회의 내용 분석 → To-Do 추출 → 프론트엔드용 최종 JSON 생성**까지 수행하는 백엔드 파이프라인입니다.

---

##  Backend Pipeline

```text
main_pipeline.py
        │
        ▼
FileExtensionValidator
        │
        ├── 파일 존재 여부 확인
        │
        └── 파일 확장자 검증
            (.txt / .pdf / .docx)
        │
        ▼
stage1_analyzer.py
        │
        ├── 원본 문서 읽기
        ├── 시차 자동 계산
        └── OpenAI API 기반 회의 내용 분석
        │
        ▼
openai_file_result.json
        │
        ▼
stage2_todo.py
        │
        ├── meeting_summary 추출
        ├── OpenAI API 기반 To-Do 분석
        │
        ├──────────────► todo_result.json
        │
        └── Stage1 + Stage2 결과 병합
                         │
                         ▼
                frontend_result.json
```

---

##  실행 흐름

`main_pipeline.py`를 실행하면 다음 순서로 전체 파이프라인이 자동으로 실행됩니다.

```text
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
```

### 1. 파일 검증

`FileExtensionValidator`를 통해 입력된 파일을 검증합니다.

- 파일 존재 여부 확인
- 파일 확장자 확인
- 지원하지 않는 파일 형식 차단

### 지원 파일 형식

| 형식 | 확장자 |
|---|---|
| Text | `.txt` |
| PDF | `.pdf` |
| Word | `.docx` |

---

##  Stage 1 — Meeting Analysis

`stage1_analyzer.py`에서 원본 회의 문서를 분석합니다.

### 주요 기능

- TXT / PDF / DOCX 문서 읽기
- 사용자 및 파트너 국가 정보 추출
- 국가별 Time Zone 확인
- 현재 시점 기준 시차 계산
- 서머타임(DST) 자동 반영
- 양측 근무시간 중 겹치는 시간 계산
- 권장 회의 시간 계산
- OpenAI API 기반 회의 내용 분석

### 분석 결과

Stage 1에서는 다음 정보를 생성합니다.

```text
cultural_analysis
communication_style
time_zone_analysis
meeting_summary
risk_notes
```

분석 결과는 다음 파일에 저장됩니다.

```text
openai_file_result.json
```

---

##  Stage 2 — To-Do Extraction

`stage2_todo.py`에서는 Stage 1에서 생성된 `meeting_summary`를 기반으로 실행 항목을 추출합니다.

### 주요 기능

- `meeting_summary` 추출
- 회의에서 결정된 실행 항목 분석
- 담당자(Assignee) 추출
- 마감일(Due Date) 추출
- 미합의/보류 사항 중 추가 조치가 필요한 항목 확인

### To-Do 결과 예시

```json
{
  "action_items": [
    {
      "task": "견적서 수정본 전달",
      "assignee": "Kim",
      "due_date": "금요일까지"
    }
  ]
}
```

Stage 2의 분석 결과는 다음 파일에 저장됩니다.

```text
todo_result.json
```

---

##  Final Merge

Stage 1과 Stage 2의 결과를 병합하여 프론트엔드에서 사용할 최종 JSON을 생성합니다.

```text
Stage 1 Result
      +
Stage 2 Result
      │
      ▼
frontend_result.json
```

### 최종 JSON 구조

```json
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

    "communication_style": {
      "directness": "",
      "formality": "",
      "evidence": "",
      "tone_recommendation": ""
    },

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
```

프론트엔드에서는 최종적으로 `frontend_result.json`을 사용합니다.

---

##  Project Structure

```text
/root/project/
│
├── main_pipeline.py
│   └── 전체 백엔드 파이프라인 실행
│
├── file_validator.py
│   └── 파일 존재 여부 및 확장자 검증
│
├── stage1_analyzer.py
│   └── 회의 내용 / 문화 / 시차 분석
│
├── stage2_todo.py
│   └── To-Do / 담당자 / 마감일 추출
│
├── api_key.txt
│   └── OpenAI API Key
│
├── analyze_file.txt
│   └── 기본 분석 대상 회의 문서
│
├── openai_file_result.json
│   └── Stage 1 분석 결과 (자동 생성)
│
├── todo_result.json
│   └── Stage 2 분석 결과 (자동 생성)
│
└── frontend_result.json
    └── 프론트엔드 전달용 최종 결과 (자동 생성)
```

---

##  Installation

필요한 Python 패키지를 설치합니다.

```bash
pip install openai pytz babel pypdf python-docx
```

---

##  API Key

OpenAI API Key는 코드에 직접 작성하지 않고 `api_key.txt` 파일에서 불러옵니다.

`api_key.txt`

```text
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

>  `api_key.txt`는 보안상 GitHub에 업로드하지 않습니다.

`.gitignore`에 다음 내용을 추가합니다.

```gitignore
api_key.txt
.env
__pycache__/
*.pyc
```

---

##  Usage

### 기본 파일 실행

프로젝트 폴더의 `analyze_file.txt`를 분석합니다.

```bash
cd /root/project
python3 main_pipeline.py
```

### TXT 파일 지정

```bash
python3 main_pipeline.py /root/upload/meeting.txt
```

### PDF 파일 지정

```bash
python3 main_pipeline.py /root/upload/meeting.pdf
```

### DOCX 파일 지정

```bash
python3 main_pipeline.py /root/upload/meeting.docx
```

---

##  Output

파이프라인이 정상적으로 실행되면 다음 파일들이 자동 생성됩니다.

```text
openai_file_result.json
        │
        ▼
todo_result.json
        │
        ▼
frontend_result.json
```

| 파일 | 설명 |
|---|---|
| `openai_file_result.json` | Stage 1 회의 분석 결과 |
| `todo_result.json` | Stage 2 To-Do 분석 결과 |
| `frontend_result.json` | 프론트엔드 전달용 최종 통합 결과 |

최종적으로 프론트엔드에서는 **`frontend_result.json`**을 사용합니다.
