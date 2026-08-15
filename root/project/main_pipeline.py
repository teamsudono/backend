import sys
from pathlib import Path

from file_validator import FileExtensionValidator
from stage1_analyzer import OpenAIFileAnalyzer
from stage2_todo import OpenAITodoExtractor


class MainPipeline:

    def __init__(self, input_file_path=None):

        # -----------------------------------------------------
        # 프로젝트 기본 경로
        # -----------------------------------------------------
        self.base_path = (
            Path(__file__)
            .resolve()
            .parent
        )

        # -----------------------------------------------------
        # 입력 파일
        #
        # 실행할 때 파일 경로를 전달하면 해당 파일 사용
        #
        # python3 main_pipeline.py /root/files/meeting.pdf
        #
        # 전달하지 않으면 기본:
        # /root/project/analyze_file.txt
        # -----------------------------------------------------
        if input_file_path:

            input_path = Path(input_file_path)

            # 상대 경로인 경우 현재 실행 위치 기준
            if not input_path.is_absolute():

                input_path = (
                    Path.cwd()
                    / input_path
                )

            self.input_file_path = (
                input_path.resolve()
            )

        else:

            self.input_file_path = (
                self.base_path
                / "analyze_file.txt"
            )

        print(
            f"[INFO] 분석 대상 파일: "
            f"{self.input_file_path}"
        )

    # =========================================================
    # STEP 0
    # 파일 검증
    # =========================================================
    def validate_file(self):

        print()
        print("=" * 60)
        print("[STEP 0] 파일 검증 시작")
        print("=" * 60)

        validator = FileExtensionValidator(
            self.input_file_path
        )

        result = (
            validator
            .validate_document()
        )

        if not result["success"]:

            print(
                f"[ERROR] {result['message']}"
            )

            return False

        print(
            f"[SUCCESS] {result['message']}"
        )

        print(
            f"[INFO] 파일 경로: "
            f"{result['file_path']}"
        )

        print(
            f"[INFO] 파일 확장자: "
            f"{result['extension']}"
        )

        return True

    # =========================================================
    # STEP 1
    # 회의 내용 분석
    # =========================================================
    def run_stage1(self):

        print()
        print("=" * 60)
        print("[STEP 1] 회의 내용 분석 시작")
        print("=" * 60)

        try:

            analyzer = OpenAIFileAnalyzer(
                input_file_path=self.input_file_path
            )

            # 이전 결과 제거
            analyzer.clear_previous_result()

            # 파일 읽기
            if not analyzer.openfile():

                print(
                    "[ERROR] Stage1 파일 불러오기 실패"
                )

                return False

            # AI 분석
            if not analyzer.analyze_file():

                print(
                    "[ERROR] Stage1 OpenAI 분석 실패"
                )

                return False

            # 결과 저장
            if not analyzer.save_result():

                print(
                    "[ERROR] Stage1 결과 저장 실패"
                )

                return False

            print(
                "[SUCCESS] Stage1 완료"
            )

            print(
                f"[INFO] Stage1 결과: "
                f"{analyzer.result_path}"
            )

            return True

        except Exception as e:

            print(
                f"[ERROR] Stage1 실행 중 오류: {e}"
            )

            return False

    # =========================================================
    # STEP 2
    # To-Do 추출
    # =========================================================
    def run_stage2(self):

        print()
        print("=" * 60)
        print("[STEP 2] To-Do 추출 시작")
        print("=" * 60)

        try:

            extractor = OpenAITodoExtractor()

            # 이전 결과 제거
            extractor.clear_previous_result()

            # Stage1 결과 불러오기
            if not extractor.openfile():

                print(
                    "[ERROR] Stage2 입력 파일 불러오기 실패"
                )

                return False

            # AI 분석
            if not extractor.analyze_file():

                print(
                    "[ERROR] Stage2 OpenAI 분석 실패"
                )

                return False

            # Stage2 결과 저장
            if not extractor.save_result():

                print(
                    "[ERROR] Stage2 결과 저장 실패"
                )

                return False

            # Stage1 + Stage2 결과 병합
            if not extractor.merge_for_frontend():

                print(
                    "[ERROR] 최종 결과 병합 실패"
                )

                return False

            print(
                "[SUCCESS] Stage2 완료"
            )

            print(
                f"[INFO] 최종 결과: "
                f"{extractor.final_path}"
            )

            return True

        except Exception as e:

            print(
                f"[ERROR] Stage2 실행 중 오류: {e}"
            )

            return False

    # =========================================================
    # 전체 Pipeline 실행
    # =========================================================
    def run(self):

        print()
        print("=" * 60)
        print("OpenAI Meeting Analysis Pipeline")
        print("=" * 60)

        # -----------------------------------------------------
        # STEP 0
        # 확장자 / 파일 존재 여부 검사
        # -----------------------------------------------------
        if not self.validate_file():

            print()
            print(
                "[PIPELINE FAILED] "
                "파일 검증 단계에서 종료되었습니다."
            )

            return False

        # -----------------------------------------------------
        # STEP 1
        # 회의 내용 분석
        # -----------------------------------------------------
        if not self.run_stage1():

            print()
            print(
                "[PIPELINE FAILED] "
                "Stage1에서 종료되었습니다."
            )

            return False

        # -----------------------------------------------------
        # STEP 2
        # To-Do 분석
        # -----------------------------------------------------
        if not self.run_stage2():

            print()
            print(
                "[PIPELINE FAILED] "
                "Stage2에서 종료되었습니다."
            )

            return False

        # -----------------------------------------------------
        # 전체 완료
        # -----------------------------------------------------
        final_result = (
            self.base_path
            / "frontend_result.json"
        )

        print()
        print("=" * 60)
        print("[PIPELINE SUCCESS]")
        print("=" * 60)

        print(
            "모든 분석 단계가 정상적으로 완료되었습니다."
        )

        print(
            f"최종 결과 파일: {final_result}"
        )

        return True


# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":

    # ---------------------------------------------------------
    # 실행 방법
    #
    # 1.
    # python3 main_pipeline.py
    #
    # 기본:
    # /root/project/analyze_file.txt
    #
    #
    # 2.
    # python3 main_pipeline.py meeting.docx
    #
    #
    # 3.
    # python3 main_pipeline.py /root/files/meeting.pdf
    # ---------------------------------------------------------

    input_file = None

    if len(sys.argv) >= 2:

        input_file = sys.argv[1]

    try:

        pipeline = MainPipeline(
            input_file_path=input_file
        )

        success = pipeline.run()

        if not success:

            # Linux에서 실패 상태 코드
            sys.exit(1)

    except KeyboardInterrupt:

        print(
            "\n[INFO] 사용자가 실행을 중단했습니다."
        )

        sys.exit(130)

    except Exception as e:

        print(
            f"[FATAL ERROR] {e}"
        )

        sys.exit(1)
