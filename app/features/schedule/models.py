from tortoise import fields
from tortoise.models import Model


class CrawledSchedule(Model):
    id = fields.IntField(pk=True)
    artist_name = fields.CharField(max_length=255)         # 아티스트명
    event_title = fields.CharField(max_length=255)         # 일정 제목
    event_date = fields.DateField()                        # 일정 날짜
    event_time = fields.CharField(max_length=50, null=True) # 시간 정보 (없을 수도 있음)
    source_url = fields.CharField(max_length=500)          # 크롤링한 출처
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "crawled_schedule"
