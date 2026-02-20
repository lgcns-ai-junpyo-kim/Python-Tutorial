"""
04_staticmethod.py
주제:
- staticmethod
- 인스턴스/클래스와 무관한 유틸 함수
"""
import re

class Validator:

    @staticmethod # 객체 상태와 무관하지만 user 정보를 처리하는 역할을 수행할 때 보통 사용
    def is_email(value):
        """
        TODO:
        - 문자열인지 확인
        - '@'가 포함되어 있는지 확인
        - 간단한 이메일 형식 검증 구현
        """
        if not isinstance(value, str):
            raise TypeError("문자열 형식의 입력값이 필요합니다.")
        
        EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
        return bool(EMAIL_RE.match(value))


if __name__ == "__main__":
    print(Validator.is_email("test@test.com"))
    print(Validator.is_email("invalid-email"))