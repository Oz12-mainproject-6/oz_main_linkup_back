# external/scrapping.py
import re

import requests
from bs4 import BeautifulSoup

# 올바른 URL - /schedule 경로 추가
BASE_URL = "https://blip.kr/artists/{artist_name}/schedule?unitId={unit_id}"


def get_artist_schedule(artist_name: str, unit_id: str):
    url = BASE_URL.format(artist_name=artist_name, unit_id=unit_id)
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)

    # 🔍 디버깅용 출력
    print("🔗 요청 URL:", url)
    print("📊 응답 상태:", res.status_code)

    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    print("🔍 HTML 구조 확인 (앞부분 2000자만)")
    print(soup.prettify()[:2000])

    schedules = []

    # 캘린더에서 스케줄 이벤트 찾기
    # blip.kr의 실제 구조에 맞는 셀렉터들
    possible_selectors = [
        # 캘린더 관련
        ".calendar-event",
        ".schedule-event",
        ".event-item",
        "[class*='calendar']",
        "[class*='schedule']",
        "[class*='event']",
        # 날짜별 이벤트
        ".date-event",
        ".day-event",
        # 일반적인 이벤트 컨테이너
        ".event",
        ".schedule",
        # 데이터 속성
        "[data-date]",
        "[data-event]",
        "[data-schedule]",
    ]

    found_elements = False

    for selector in possible_selectors:
        items = soup.select(selector)
        if items:
            print(f"✅ 발견된 요소: {selector} ({len(items)}개)")
            found_elements = True

            for item in items:
                # 각 이벤트에서 정보 추출
                date = extract_date_info(item)
                title = extract_title_info(item)
                category = extract_type_info(item)

                if date or title:
                    # 유효한 제목이 있는 경우만 추가
                    if title and len(title) > 2 and not title.isdigit():
                        schedules.append(
                            {
                                "date": date or "날짜 없음",
                                "title": title,
                                "type": category or "타입 없음",
                            }
                        )

    # 스크립트에서 JSON 데이터 찾기 (많은 사이트가 이 방식 사용)
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string and (
            "schedule" in script.string.lower() or "event" in script.string.lower()
        ):
            print("📜 스케줄 관련 스크립트 발견")
            # JSON 패턴 찾기
            json_matches = re.findall(
                r"schedules?\s*:\s*(\[.*?\])", script.string, re.DOTALL
            )
            if json_matches:
                print(f"📄 JSON 패턴 발견: {json_matches[0][:100]}...")

    if not found_elements:
        print("❌ 스케줄 요소를 찾지 못함")
        print("💡 이유: JavaScript로 동적 로드되는 캘린더")

        # 페이지에 있는 모든 클래스 출력
        all_classes = set()
        for element in soup.find_all(class_=True):
            if isinstance(element.get("class"), list):
                all_classes.update(element.get("class"))

        print("🔍 페이지의 실제 클래스들:")
        calendar_classes = [
            cls
            for cls in all_classes
            if any(
                keyword in cls.lower()
                for keyword in ["calendar", "schedule", "event", "date"]
            )
        ]

        if calendar_classes:
            for cls in calendar_classes:
                print(f"   .{cls}")
        else:
            print("   스케줄/캘린더 관련 클래스 없음")
            print("   처음 20개 클래스:", list(all_classes)[:20])

    return schedules


def extract_date_info(element):
    """요소에서 날짜 정보 추출"""
    # 데이터 속성에서 찾기
    date_attrs = ["data-date", "data-day", "datetime", "data-time"]
    for attr in date_attrs:
        if element.get(attr):
            return element.get(attr)

    # 클래스 이름에서 날짜 패턴 찾기
    classes = element.get("class", [])
    for cls in classes:
        if re.search(r"\d{4}-\d{2}-\d{2}", cls):
            return re.search(r"\d{4}-\d{2}-\d{2}", cls).group()

    # 텍스트에서 날짜 패턴 찾기
    text = element.get_text(strip=True)
    date_patterns = [
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        r"(\d{1,2})월\s*(\d{1,2})일",
        r"(\d{1,2})/(\d{1,2})",
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()

    return None


def extract_title_info(element):
    """요소에서 제목 정보 추출"""
    # 제목 관련 하위 요소 찾기
    title_selectors = [
        ".title",
        ".event-title",
        ".schedule-title",
        ".name",
        ".event-name",
        ".text",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    ]

    for selector in title_selectors:
        title_elem = element.select_one(selector)
        if title_elem:
            return title_elem.get_text(strip=True)

    # 전체 텍스트 확인
    text = element.get_text(strip=True)

    # 숫자만 있는 경우 제외 (캘린더 날짜)
    if text.isdigit() or len(text) <= 2:
        return None

    # 날짜 패턴만 있는 경우 제외
    if re.match(r"^[\d\s/\-월일년]+$", text):
        return None

    return text[:50] if len(text) > 50 else text

def extract_type_info(element):
    """요소에서 타입 정보 추출"""
    # 타입 관련 속성이나 클래스 찾기
    type_attrs = ["data-type", "data-category", "data-kind"]
    for attr in type_attrs:
        if element.get(attr):
            return element.get(attr)

    # 클래스에서 타입 유추
    classes = element.get("class", [])
    type_keywords = [
        "broadcast",
        "방송",
        "concert",
        "콘서트",
        "fanmeeting",
        "팬미팅",
        "release",
        "발매",
    ]

    for cls in classes:
        for keyword in type_keywords:
            if keyword in cls.lower():
                return keyword

    return None
