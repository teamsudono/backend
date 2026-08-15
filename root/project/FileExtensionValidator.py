from pathlib import Path


# 파일 확장자 검증 기능
class FileExtensionValidator:
    def __init__(self):
        self.base_path = Path("/root/project")
        self.analyze_file_path = self.base_path / "analyze_file.txt"
        self.allowed_extensions = {".txt", ".docx", ".pdf"}

    def validate_document(self):
        try:
            # 1. 파일 존재 여부 확인
            if not self.analyze_file_path.is_file():
                return "오류: 파일이 존재하지 않습니다."

            # 2. 파일 확장자 추출
            extension = self.analyze_file_path.suffix.lower()

            # 3. 허용된 확장자인지 확인
            if extension not in self.allowed_extensions:
                return "오류: 지원하지 않는 문서 형식입니다."

            return "정상: 지원하는 문서 형식입니다."

        except Exception as e:
            return f"오류: {e}"
