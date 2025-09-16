"""Email service for sending verification emails."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import HTTPException, status


class EmailService:
    """이메일 서비스 클래스"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)

    async def send_verification_email(
        self, to_email: str, verification_code: str
    ) -> bool:
        """이메일 인증 코드 전송"""
        try:
            # 개발 환경에서는 콘솔에 출력
            if os.getenv("ENVIRONMENT") == "development":
                print("\n📧 [개발모드] 이메일 인증 코드")
                print(f"수신자: {to_email}")
                print(f"인증코드: {verification_code}")
                print("=" * 50)
                return True

            # 프로덕션 환경에서는 실제 이메일 전송
            if not all([self.smtp_username, self.smtp_password]):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="이메일 서비스 설정이 필요합니다",
                )

            message = MIMEMultipart("alternative")
            message["Subject"] = "[LinkUp] 이메일 인증 코드"
            message["From"] = self.from_email
            message["To"] = to_email

            # HTML 이메일 템플릿
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>LinkUp 이메일 인증</title>
            </head>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #333; margin: 0;">🔗 LinkUp</h1>
                        <p style="color: #666; margin-top: 10px;">이메일 인증을 완료해주세요</p>
                    </div>

                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <h2 style="color: #333; margin: 0 0 15px 0;">인증 코드</h2>
                        <div style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 5px; font-family: monospace;">
                            {verification_code}
                        </div>
                    </div>

                    <div style="margin: 20px 0; line-height: 1.6; color: #555;">
                        <p>안녕하세요! LinkUp에 가입해주셔서 감사합니다.</p>
                        <p>위의 <strong>6자리 인증 코드</strong>를 앱에 입력하여 이메일 인증을 완료해주세요.</p>
                        <p style="color: #dc3545;"><strong>인증 코드는 10분 후 만료됩니다.</strong></p>
                    </div>

                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

                    <div style="text-align: center; color: #999; font-size: 14px;">
                        <p>본 메일은 발신 전용입니다. 문의사항이 있으시면 고객센터로 연락해주세요.</p>
                        <p>&copy; 2024 LinkUp. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # 텍스트 버전
            text_content = f"""
            LinkUp 이메일 인증

            안녕하세요! LinkUp에 가입해주셔서 감사합니다.

            아래의 6자리 인증 코드를 앱에 입력하여 이메일 인증을 완료해주세요.

            인증 코드: {verification_code}

            * 인증 코드는 10분 후 만료됩니다.

            본 메일은 발신 전용입니다.
            © 2024 LinkUp. All rights reserved.
            """

            # MIME 객체 생성
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            message.attach(text_part)
            message.attach(html_part)

            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            return True

        except Exception as e:
            print(f"이메일 전송 오류: {e}")
            # 개발 환경에서는 오류가 발생해도 계속 진행
            if os.getenv("ENVIRONMENT") == "development":
                return True
            return False


# 전역 이메일 서비스 인스턴스
email_service = EmailService()
