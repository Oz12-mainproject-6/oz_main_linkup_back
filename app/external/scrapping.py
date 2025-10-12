import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# MyLoveIdol URL
MYLOVEIDOL_BASE_URL = "https://www.myloveidol.com/api/v1/schedules/all_schedule/"


def get_myloveidol_schedule(
    locale: str = "ko", date_filter: str | None = None, artist_name: str | None = None
) -> list[dict]:
    """
    MyLoveIdol 스케줄 크롤링 및 필터링
    - locale: 'ko', 'en' 등
    - date_filter: 'YYYY-MM-DD' 형식
    - artist_name: 솔로면 stage_name, 그룹이면 group_name으로 필터링
    """
    response = requests.get(MYLOVEIDOL_BASE_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    # 예시: schedule-item 클래스로 이벤트 추출
    for item in soup.select(".schedule-item"):
        date_text = item.get("data-date")
        event_date = datetime.strptime(date_text, "%Y-%m-%d")
        group_name = item.get("data-group-name")
        stage_name = item.get("data-stage-name")
        title = item.select_one(".title").text.strip()

        event = {
            "date": event_date,
            "group_name": group_name,
            "stage_name": stage_name,
            "title": title,
        }

        events.append(event)

    # 날짜 필터
    if date_filter:
        events = [e for e in events if e["date"].strftime("%Y-%m-%d") == date_filter]

    # 아티스트 필터 (솔로/그룹 모두 체크)
    if artist_name:
        events = [
            e
            for e in events
            if e.get("stage_name") == artist_name or e.get("group_name") == artist_name
        ]

    return events


def extract_myloveidol_schedule_data(element):
    """HTML 요소에서 스케줄 데이터 추출"""
    try:
        date = extract_myloveidol_date_info(element)
        title = extract_myloveidol_title_info(element)
        artist = extract_myloveidol_artist_info(element)
        category = extract_myloveidol_category_info(element)
        time_info = extract_myloveidol_time_info(element)
        location = extract_myloveidol_location_info(element)

        if title:
            return {
                "date": date or "날짜 미상",
                "time": time_info,
                "title": title.strip(),
                "artist": artist,
                "type": category or "기타",
                "location": location,
                "source": "myloveidol.com",
            }
    except Exception as e:
        print(f"MyLoveIdol 요소 추출 오류: {e}")
    return None


def extract_myloveidol_date_info(element):
    """날짜 추출"""
    for attr in ["data-date", "datetime", "data-start-date"]:
        if element.get(attr):
            return element.get(attr)
    text = element.get_text()
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if match:
        return match.group()
    return None


def extract_myloveidol_title_info(element):
    """제목 추출"""
    selectors = [".title", ".event-title", "h1", "h2", "h3"]
    for sel in selectors:
        e = element.select_one(sel)
        if e and e.get_text(strip=True):
            return e.get_text(strip=True)
    return element.get_text(strip=True)


def extract_myloveidol_artist_info(element):
    """아티스트 추출"""
    selectors = [".artist", ".performer", '[class*="artist"]']
    for sel in selectors:
        e = element.select_one(sel)
        if e:
            return e.get_text(strip=True)
    img = element.select_one("img")
    if img and img.get("alt"):
        return img.get("alt")
    return None


def extract_myloveidol_category_info(element):
    """카테고리 추출"""
    for attr in ["data-category", "data-type", "data-genre"]:
        if element.get(attr):
            return element.get(attr)
    return None


def extract_myloveidol_time_info(element):
    """시간 추출"""
    text = element.get_text()
    match = re.search(r"(\d{1,2}:\d{2})", text)
    if match:
        return match.group()
    return None


def extract_myloveidol_location_info(element):
    """장소 추출"""
    selectors = [".location", ".venue", ".place"]
    for sel in selectors:
        e = element.select_one(sel)
        if e:
            return e.get_text(strip=True)
    return None


def extract_myloveidol_json_schedules(soup):
    """스크립트 안 JSON 데이터 추출"""
    schedules = []
    scripts = soup.find_all("script")
    for script in scripts:
        if not script.string:
            continue
        matches = re.findall(r"schedules?\s*[:=]\s*(\[.*?\])", script.string, re.DOTALL)
        for m in matches:
            try:
                data = json.loads(m)
                schedules.extend(parse_myloveidol_json_schedules(data))
            except Exception:
                continue
    return schedules


def parse_myloveidol_json_schedules(data):
    """JSON -> 일정 dict"""
    schedules = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                schedules.append(
                    {
                        "date": item.get("date"),
                        "time": item.get("time"),
                        "title": item.get("title"),
                        "artist": item.get("artist"),
                        "type": item.get("category") or "기타",
                        "location": item.get("location"),
                        "source": "myloveidol.com",
                    }
                )
    return schedules


def detect_and_call_myloveidol_api(soup, headers):
    """페이지에서 API 호출 URL 찾아서 JSON 추출"""
    schedules = []
    scripts = soup.find_all("script")
    for script in scripts:
        if not script.string:
            continue
        matches = re.findall(r'["\'](/api/schedules?[^"\']*)["\']', script.string)
        for m in matches:
            api_url = f"https://www.myloveidol.com{m}"
            try:
                res = requests.get(api_url, headers=headers, timeout=5)
                if res.status_code == 200:
                    schedules.extend(parse_myloveidol_json_schedules(res.json()))
            except Exception:
                continue
    return schedules


def remove_schedule_duplicates(schedules):
    """중복 제거"""
    seen = set()
    unique = []
    for s in schedules:
        key = f"{s.get('date')}-{s.get('title')}-{s.get('artist')}"
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def convert_to_calendar_events(schedules):
    """캘린더용 이벤트 변환"""
    events = []
    for s in schedules:
        start = s["date"]
        if s.get("time"):
            start += f"T{s['time']}"
        events.append(
            {
                "title": f"{s.get('title', '')} - {s.get('artist', '')}",
                "start": start,
                "allDay": not bool(s.get("time")),
            }
        )
    return events


if __name__ == "__main__":
    schedules = get_myloveidol_schedule(date_filter="2025-09-25")
    events = convert_to_calendar_events(schedules)
    print(json.dumps(events, ensure_ascii=False, indent=2))


def fetch_myloveidol_json(locale: str = "ko", limit: int = 1000) -> list[dict]:
    """
    최애돌 API에서 일정 JSON 데이터 가져오기
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    }
    response = requests.get(MYLOVEIDOL_BASE_URL, headers=headers)
    data = response.json()
    params = {"locale": locale, "limit": limit}

    response = requests.get(MYLOVEIDOL_BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if not data.get("success"):
        return []

    return data.get("objects", [])


def parse_myloveidol_events(
    json_objects: list[dict], artist_filter: str | None = None
) -> list[dict]:
    """
    JSON 데이터를 DB/캘린더용 이벤트 리스트로 변환
    """
    events = []

    for obj in json_objects:
        idol = obj.get("idol", {})
        artist_name = idol.get("name")
        group_id = idol.get("group_id")

        # 솔로/그룹 필터링
        if artist_filter:
            events = [e for e in events if e["idol"]["name"] == artist_filter]
            if artist_filter != artist_name:
                continue

        dtstart = obj.get("dtstart") or obj.get("created_at")
        if dtstart:
            start_time = datetime.fromisoformat(dtstart)
        else:
            start_time = None

        event = {
            "title": obj.get("title", ""),
            "artist_name": artist_name,
            "group_id": group_id,
            "start_time": start_time,
            "category": obj.get("category", "other"),
            "allday": bool(obj.get("allday")),
            "location": obj.get("location"),
            "extra": obj.get("extra"),
            "article_id": obj.get("article_id"),
            "source": "myloveidol.com",
        }
        events.append(event)

    return events


def convert_to_calendar_events(events: list[dict]) -> list[dict]:
    """캘린더용 이벤트 변환"""
    calendar_events = []
    for e in events:
        start = e["start_time"].isoformat() if e.get("start_time") else None
        calendar_events.append(
            {
                "title": f"{e.get('title', '')} - {e.get('artist_name', '')}",
                "start": start,
                "allDay": e.get("allday", True),
            }
        )
    return calendar_events
