from tortoise import fields
from app.core.mixins import TimestampMixin


class Artist(TimestampMixin):
    """아티스트 기본 모델"""
    
    id = fields.BigIntField(pk=True, description="아티스트 ID")
    real_name = fields.CharField(max_length=200, description="실명")
    birthdate = fields.DateField(null=True, description="생년월일")
    gender = fields.CharField(max_length=200, null=True, description="성별")  
    company = fields.CharField(max_length=200, null=True, description="소속사")
    role = fields.CharField(max_length=200, null=True, description="역할")
    mbti = fields.CharField(max_length=4, null=True, description="MBTI")
    height = fields.CharField(max_length=255, null=True, description="키")
    nickname = fields.CharField(max_length=200, null=True, description="별명")
    email = fields.CharField(max_length=200, unique=True, description="이메일")
    debut_date = fields.DateField(null=True, description="데뷔일")
    is_group = fields.BooleanField(default=False, description="그룹 여부")
    
    class Meta:
        table = "artist"


class SoloArtist(Artist):
    """솔로 아티스트 모델"""
    
    # 솔로 아티스트 특화 필드들
    stage_name = fields.CharField(max_length=200, description="예명")
    
    class Meta:
        table = "solo_artist"


class GroupArtist(Artist):
    """그룹 아티스트 모델"""
    
    # 그룹 특화 필드들
    member_count = fields.IntField(null=True, description="멤버 수")
    status = fields.CharField(max_length=50, default="active", description="활동 상태")
    group_name = fields.CharField(max_length=200, description="그룹명")
    
    class Meta:
        table = "group_artist"