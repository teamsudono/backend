from pathlib import Path


class FileExtensionValidator:

    def __init__(self, analyze_file_path):

        # 메인 파이프라인에서 전달받은 파일 경로 사용
        self.analyze_file_path = Path(analyze_file_path).resolve()

        # 허용 확장자
        self.allowed_extensions = {
            ".txt",
            ".docx",
            ".pdf"
        }

    def validate_document(self):

        try:

            # 1. 파일 존재 여부 확인
            if not self.analyze_file_path.is_file():

                return {
                    "success": False,
                    "message": "파일이 존재하지 않습니다."
                }

            # 2. 확장자 추출
            extension = (
                self.analyze_file_path
                .suffix
                .lower()
            )

            # 3. 허용 확장자 확인
            if extension not in self.allowed_extensions:

                return {
                    "success": False,
                    "message": (
                        f"지원하지 않는 문서 형식입니다: "
                        f"{extension}"
                    )
                }

            return {
                "success": True,
                "message": "지원하는 문서 형식입니다.",
                "extension": extension,
                "file_path": str(self.analyze_file_path)
            }

        except Exception as e:

            return {
                "success": False,
                "message": f"파일 검증 중 오류 발생: {e}"
            }
