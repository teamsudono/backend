# backend

                   main_pipeline.py

                          │

                          ▼

                FileExtensionValidator

                          │

                  파일 존재 여부 검사

                          │

              .txt / .pdf / .docx 검사

                          │

                          ▼

                  stage1_analyzer.py

                          │

                    원본 문서 읽기

                          │

                    시차 자동 계산

                          │

                    OpenAI 분석

                          │

                          ▼

              openai_file_result.json

                          │

                          ▼

                    stage2_todo.py

                          │

                meeting_summary 추출

                          │

                  OpenAI To-Do 분석

                          │

                          ├─────────────► todo_result.json

                          │

                          ▼

                 Stage1 + Stage2 병합

                          │

                          ▼

                frontend_result.json



실행 시

파일 검증
    ↓
Stage1
    ↓
openai_file_result.json
    ↓
Stage2
    ↓
todo_result.json
    ↓
frontend_result.json
