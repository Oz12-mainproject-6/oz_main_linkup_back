import asyncio
from datetime import datetime
from typing import List, Dict, Any
import httpx
from loguru import logger

from app.features.events.models import Events


class NotificationService:
    """알림 서비스 클래스"""

    def __init__(self):
        # 설정값들 (실제 환경에서는 config에서 가져오기)
        self.push_service_url = "http://localhost:8001"  # 푸시 서비스 URL
        self.email_service_url = "http://localhost:8002"  # 이메일 서비스 URL
        self.webhook_urls = [
            # "https://discord.com/api/webhooks/your-webhook-url",
            # "https://hooks.slack.com/services/your-webhook-url"
        ]

    async def send_instant_notification(self, event: Events):
        """즉시 알림 전송 (이벤트 등록시)"""
        message = self._create_instant_message(event)

        # 여러 채널로 동시 전송
        tasks = [
            self._send_push_notification(message),
            self._send_email_notification(message),
            self._send_webhook_notifications(message, event)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 로깅
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        logger.info(f"Instant notification sent for event {event.id}: {success_count}/{len(tasks)} channels succeeded")

    async def send_upcoming_notification(self, event: Events):
        """1시간 전 알림 전송"""
        message = self._create_upcoming_message(event)

        tasks = [
            self._send_push_notification(message),
            self._send_email_notification(message)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for result in results if not isinstance(result, Exception))
        logger.info(f"Upcoming notification sent for event {event.id}: {success_count}/{len(tasks)} channels succeeded")

    def _create_instant_message(self, event: Events) -> Dict[str, Any]:
        """즉시 알림 메시지 생성 - 안전성 개선"""
        artist_name = "Unknown Artist"  # 기본값

        if hasattr(event, 'artist') and event.artist:
            artist_name = getattr(event.artist, 'name', 'Unknown Artist')

        return {
            "type": "instant",
            "event_id": event.id,
            "title": f"🎵 새로운 이벤트: {event.title}",
            "body": f"{artist_name}의 {event.category.value} 일정이 등록되었습니다!",
            "data": {
                "event_id": event.id,
                "artist_id": event.artist_id,
                "start_time": event.start_time.isoformat(),
                "location": event.location or "미정",
                "category": event.category.value
            }
        }

    def _create_upcoming_message(self, event: Events) -> Dict[str, Any]:
        """1시간 전 알림 메시지 생성 - 안전성 개선"""
        artist_name = "Unknown Artist"  # 기본값

        if hasattr(event, 'artist') and event.artist:
            artist_name = getattr(event.artist, 'name', 'Unknown Artist')

        return {
            "type": "upcoming",
            "event_id": event.id,
            "title": f"⏰ 곧 시작: {event.title}",
            "body": f"{artist_name}의 {event.category.value}이 1시간 후 시작됩니다!",
            "data": {
                "event_id": event.id,
                "artist_id": event.artist_id,
                "start_time": event.start_time.isoformat(),
                "location": event.location or "미정",
                "category": event.category.value
            }
        }

    async def _send_push_notification(self, message: Dict[str, Any]) -> bool:
        """푸시 알림 전송"""
        if not self.push_service_url:
            logger.warning("Push service URL not configured")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.push_service_url}/send",
                    json=message,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Push notification sent successfully for event {message['event_id']}")
                return True

        except httpx.RequestError as e:
            logger.error(f"Push notification request failed: {str(e)}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Push notification HTTP error: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to send push notification: {str(e)}")
            return False

    async def _send_email_notification(self, message: Dict[str, Any]) -> bool:
        """이메일 알림 전송"""
        if not self.email_service_url:
            logger.warning("Email service URL not configured")
            return False

        try:
            email_data = {
                "subject": message["title"],
                "body": message["body"],
                "template": "event_notification",
                "data": message["data"]
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.email_service_url}/send",
                    json=email_data,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Email notification sent successfully for event {message['event_id']}")
                return True

        except httpx.RequestError as e:
            logger.error(f"Email notification request failed: {str(e)}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"Email notification HTTP error: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False

    async def _send_webhook_notifications(self, message: Dict[str, Any], event: Events) -> bool:
        """웹훅 알림 전송 - artist 안전성 체크 추가"""
        if not self.webhook_urls:
            logger.info("No webhook URLs configured")
            return True  # 설정이 없어도 에러는 아님

        # artist 이름 안전하게 가져오기
        artist_name = "Unknown Artist"
        if hasattr(event, 'artist') and event.artist:
            artist_name = getattr(event.artist, 'name', 'Unknown Artist')

        # 디스코드용 웹훅 페이로드
        webhook_payload = {
            "content": f"🎵 **{message['title']}**\n{message['body']}",
            "embeds": [
                {
                    "title": event.title,
                    "description": event.description or "설명이 없습니다.",
                    "color": 0x667eea,
                    "fields": [
                        {"name": "아티스트", "value": artist_name, "inline": True},
                        {"name": "카테고리", "value": event.category.value, "inline": True},
                        {"name": "시작 시간", "value": event.start_time.strftime("%Y-%m-%d %H:%M"), "inline": True},
                        {"name": "위치", "value": event.location or "미정", "inline": True}
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }

        successful = 0
        for webhook_url in self.webhook_urls:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        webhook_url,
                        json=webhook_payload,
                        timeout=10.0
                    )
                    response.raise_for_status()
                    successful += 1

            except Exception as e:
                logger.error(f"Failed to send webhook notification to {webhook_url}: {str(e)}")

        logger.info(f"Webhook notifications sent: {successful}/{len(self.webhook_urls)} successful")
        return successful > 0

    async def send_batch_notification(self, events: List[Events], notification_type: str = "batch"):
        """일괄 알림 전송 (관리자용)"""
        if not events:
            logger.info("No events to send batch notification for")
            return

        # 안전하게 아티스트 이름 가져오기
        event_data = []
        for event in events[:5]:  # 최대 5개만
            artist_name = "Unknown Artist"
            if hasattr(event, 'artist') and event.artist:
                artist_name = getattr(event.artist, 'name', 'Unknown Artist')

            event_data.append({
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time.isoformat(),
                "artist_name": artist_name
            })

        message = {
            "type": notification_type,
            "title": f"📅 {len(events)}개의 이벤트 알림",
            "body": f"새로운 {len(events)}개의 이벤트가 추가되었습니다.",
            "data": {
                "event_count": len(events),
                "events": event_data
            }
        }

        await self._send_push_notification(message)
        logger.info(f"Batch notification sent for {len(events)} events")

    async def send_test_notification(self, message: str = "테스트 알림입니다."):
        """테스트 알림 전송 (개발/디버깅용)"""
        test_message = {
            "type": "test",
            "event_id": 0,
            "title": "🧪 테스트 알림",
            "body": message,
            "data": {
                "timestamp": datetime.now().isoformat()
            }
        }

        tasks = [
            self._send_push_notification(test_message),
            self._send_email_notification(test_message)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for result in results if not isinstance(result, Exception))

        logger.info(f"Test notification sent: {success_count}/{len(tasks)} channels succeeded")
        return success_count > 0


# 싱글톤 인스턴스 생성
notification_service = NotificationService()