import os
import re
import json

from pathlib import Path
from openai import OpenAI


class OpenAITodoExtractor:

    # ---------------------------------------------------------
    # 초기화
    # ---------------------------------------------------------
    def __init__(self):

        self.content = None
        self.stage1_data = None
        self.result = None

        # =====================================================
        # 기준 경로
        #
        # stage2_todo.py가 존재하는 폴더
        # =====================================================
        self.base_path = (
            Path(__file__)
            .resolve()
            .parent
        )

        # =====================================================
        # 입력 파일
        #
        # 1단계 결과
        # =====================================================
        self.input_path = (
            self.base_path
            / "openai_file_result.json"
        )

        # =====================================================
        # 2단계 결과
        # =====================================================
        self.result_path = (
            self.base_path
            / "todo_result.json"
        )

        # =====================================================
        # 프론트엔드 전달 최종 결과
        # =====================================================
        self.final_path = (
            self.base_path
            / "frontend_result.json"
        )

        # =====================================================
        # OpenAI 설정
        # =====================================================
        self.model_name = "gpt-4o-mini"

        self.api_key = self.load_api_key()

        self.client = OpenAI(
            api_key=self.api_key
        )

        # =====================================================
        # SYSTEM PROMPT
        # =====================================================
        self.SYSTEM_PROMPT = """
당신은 회의 요약본에서 실행 항목(To-Do)을 추출하는 AI 비서입니다.

입력으로 [meeting_summary]가 주어집니다.

이는 이미 1차로 정리된 회의 요약
(합의된 사항 / 미합의·보류된 사항)입니다.


중요한 원칙:

1. meeting_summary에 실제로 언급된 행동이나 약속만 추출하세요.

요약에 없는 내용을 추측해서 만들어내지 마세요.


2. 담당자(assignee)가 이름으로 명시되어 있으면
그 이름을 그대로 사용하세요.

명시되지 않았지만 문맥상 특정 팀이나 역할로
명확하게 유추할 수 있다면 해당 팀/역할을 적으세요.

전혀 특정할 수 없으면 "미정"으로 표기하세요.


3. 마감일(due_date)은 원문 표현을 최대한 그대로 유지하세요.

예:

"이번 달 안으로"
"다음 달 초쯤"

이런 표현을 임의의 날짜로 바꾸지 마세요.

마감 언급이 전혀 없으면
"미정"으로 표기하세요.


4. disputed_or_pending 항목 중에서도
누군가 확인하거나 조치하기로 한 내용이라면
To-Do로 포함하세요.

단순히 이견이 존재한다는 사실 자체는
To-Do가 아닙니다.


5. 하나의 문장에 여러 행동이 섞여 있으면
각각 별도 To-Do 항목으로 분리하세요.


6. 최종 출력 전에 meeting_summary를 다시 확인하세요.

언급된 모든 행동이 빠짐없이 반영됐는지 확인하고,
중복된 항목이 없는지 검토하세요.


출력은 반드시 아래 JSON 형식으로만 작성하세요.

다른 설명이나 텍스트는 절대 포함하지 마세요.


{
  "action_items": [
    {
      "task": "...",
      "assignee": "...",
      "due_date": "..."
    }
  ]
}
""".strip()

    # ---------------------------------------------------------
    # API KEY 불러오기
    # ---------------------------------------------------------
    def load_api_key(self):

        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:

            raise ValueError(
                "[ERROR] OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다."
            )

        print(
            "[INFO] OPENAI_API_KEY 환경변수에서 API Key를 불러왔습니다."
        )

        return api_key.strip()

    # ---------------------------------------------------------
    # 기존 2단계 결과 삭제
    # ---------------------------------------------------------
    def clear_previous_result(self):

        self.result_path.unlink(
            missing_ok=True
        )

        self.final_path.unlink(
            missing_ok=True
        )

        print(
            "[INFO] 기존 2단계 결과 삭제 완료"
        )

    # ---------------------------------------------------------
    # 1단계 결과 불러오기
    # ---------------------------------------------------------
    def openfile(self):

        try:

            if not self.input_path.is_file():

                print(
                    "[ERROR] 1단계 결과 파일이 존재하지 않습니다:"
                )

                print(
                    self.input_path
                )

                return False

            with open(
                self.input_path,
                "r",
                encoding="utf-8"
            ) as f:

                self.stage1_data = (
                    json.load(f)
                )

            if not isinstance(
                self.stage1_data,
                dict
            ):

                print(
                    "[ERROR] 1단계 결과 형식이 올바르지 않습니다."
                )

                return False

            meeting_summary = (
                self.stage1_data
                .get("meeting_summary")
            )

            if not meeting_summary:

                print(
                    "[ERROR] 1단계 결과에 "
                    "meeting_summary가 없습니다."
                )

                if "raw_result" in self.stage1_data:

                    print(
                        "[ERROR] 1단계 OpenAI 응답의 "
                        "JSON 파싱이 실패했을 가능성이 있습니다."
                    )

                return False

            self.content = json.dumps(
                meeting_summary,
                ensure_ascii=False,
                indent=2
            )

            print(
                "[INFO] 1단계 결과 불러오기 성공:"
            )

            print(
                self.input_path
            )

            return True

        except json.JSONDecodeError as e:

            print(
                f"[ERROR] JSON 파싱 실패: {e}"
            )

            return False

        except Exception as e:

            print(
                f"[ERROR] 파일 읽기 실패: {e}"
            )

            return False

    # ---------------------------------------------------------
    # OpenAI 분석
    # ---------------------------------------------------------
    def analyze_file(self):

        try:

            if not self.content:

                print(
                    "[ERROR] 분석할 "
                    "meeting_summary가 없습니다."
                )

                return False

            user_message = (
                "[meeting_summary]\n"
                f"{self.content}"
            )

            print(
                "[INFO] OpenAI API 분석 시작 "
                "(2단계: To-Do 추출)"
            )

            response = (
                self.client
                .chat
                .completions
                .create(
                    model=self.model_name,

                    messages=[
                        {
                            "role": "system",
                            "content": self.SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": user_message
                        }
                    ],

                    temperature=0.0
                )
            )

            self.result = (
                response
                .choices[0]
                .message
                .content
                or ""
            ).strip()

            if not self.result:

                print(
                    "[ERROR] OpenAI 응답이 비어 있습니다."
                )

                return False

            print(
                "[INFO] OpenAI API 분석 완료"
            )

            return True

        except Exception as e:

            print(
                f"[ERROR] OpenAI API 분석 실패: {e}"
            )

            return False

    # ---------------------------------------------------------
    # JSON 안전 파싱
    # ---------------------------------------------------------
    @staticmethod
    def safe_parse_json(text):

        if not text:
            return None

        text = text.strip()

        # Markdown 코드블록 제거
        if text.startswith("```"):

            text = re.sub(
                r"^```(?:json)?\s*",
                "",
                text,
                flags=re.IGNORECASE
            )

            text = re.sub(
                r"\s*```$",
                "",
                text
            )

        try:

            return json.loads(text)

        except json.JSONDecodeError:

            start = text.find("{")
            end = text.rfind("}")

            if start == -1 or end == -1:
                return None

            try:

                return json.loads(
                    text[start:end + 1]
                )

            except json.JSONDecodeError:

                return None

    # ---------------------------------------------------------
    # 2단계 AI 원본 결과 저장
    # ---------------------------------------------------------
    def save_result(self):

        try:

            if not self.result:

                print(
                    "[ERROR] 저장할 분석 결과가 없습니다."
                )

                return False

            parsed_result = (
                self.safe_parse_json(
                    self.result
                )
            )

            if parsed_result is None:

                print(
                    "[WARN] JSON 파싱 실패 - "
                    "raw_result 형태로 저장합니다."
                )

                data = {
                    "raw_result": self.result
                }

            else:

                data = parsed_result

            with open(
                self.result_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print(
                "[INFO] 2단계 결과 저장 완료:"
            )

            print(
                self.result_path
            )

            return True

        except Exception as e:

            print(
                f"[ERROR] 결과 저장 실패: {e}"
            )

            return False

    # ---------------------------------------------------------
    # 프론트엔드용 최종 JSON 병합
    # ---------------------------------------------------------
    def merge_for_frontend(self):

        try:

            todo_data = (
                self.safe_parse_json(
                    self.result
                )
            )

            if not todo_data:

                todo_data = {
                    "action_items": []
                }

            action_items = (
                todo_data
                .get(
                    "action_items",
                    []
                )
            )

            if not isinstance(
                action_items,
                list
            ):

                action_items = []

            # -------------------------------------------------
            # 최종 프론트엔드 JSON
            # -------------------------------------------------
            final_output = {

                "meeting_summary": (
                    self.stage1_data
                    .get(
                        "meeting_summary",
                        {}
                    )
                ),

                "time_zone_analysis": (
                    self.stage1_data
                    .get(
                        "time_zone_analysis",
                        {}
                    )
                ),

                "caution_notes": {

                    "cultural_analysis": (
                        self.stage1_data
                        .get(
                            "cultural_analysis",
                            []
                        )
                    ),

                    "communication_style": (
                        self.stage1_data
                        .get(
                            "communication_style",
                            {}
                        )
                    ),

                    "risk_notes": (
                        self.stage1_data
                        .get(
                            "risk_notes",
                            []
                        )
                    )
                },

                "todo_list": [
                    {
                        **item,
                        "done": False
                    }
                    for item in action_items
                    if isinstance(item, dict)
                ]
            }

            with open(
                self.final_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    final_output,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print(
                "[INFO] 프론트엔드용 최종 결과 저장 완료:"
            )

            print(
                self.final_path
            )

            return True

        except Exception as e:

            print(
                f"[ERROR] 최종 결과 병합 실패: {e}"
            )

            return False

    # ---------------------------------------------------------
    # 최종 결과 출력
    # ---------------------------------------------------------
    def open_result_file(self):

        try:

            if not self.final_path.is_file():

                print(
                    "[ERROR] 최종 결과 파일이 존재하지 않습니다:"
                )

                print(
                    self.final_path
                )

                return

            with open(
                self.final_path,
                "r",
                encoding="utf-8"
            ) as f:

                result_data = f.read()

            print(
                "\n========== "
                "최종 결과 "
                "(프론트엔드 전달용) "
                "=========="
            )

            print(
                result_data
            )

            print(
                "==========================================="
            )

        except Exception as e:

            print(
                f"[ERROR] 결과 파일 읽기 실패: {e}"
            )


# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":

    try:

        extractor = (
            OpenAITodoExtractor()
        )

        extractor.clear_previous_result()

        if extractor.openfile():

            if extractor.analyze_file():

                extractor.save_result()

                extractor.merge_for_frontend()

                extractor.open_result_file()

    except Exception as e:

        print(
            f"[FATAL ERROR] {e}"
        )
