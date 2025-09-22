---
name: 🔌 API Issue
about: API 관련 문제를 신고하세요
title: '[API] '
labels: ['api', 'backend']
assignees: ''
---

## 🔌 API 엔드포인트
문제가 발생한 API 엔드포인트를 명시해주세요.
```
[HTTP METHOD] /api/endpoint/path
```

## 🐛 문제 설명
API에서 발생한 문제에 대한 명확한 설명을 작성해주세요.

## 📤 요청 정보
### Headers
```json
{
  "Authorization": "Bearer your-token",
  "Content-Type": "application/json"
}
```

### Body (해당하는 경우)
```json
{
  "example": "request body"
}
```

## 📥 응답 정보
### 실제 응답
```json
{
  "actual": "response"
}
```

### 예상 응답
```json
{
  "expected": "response"
}
```

## 🔍 HTTP 상태 코드
- 실제 상태 코드: 
- 예상 상태 코드: 

## 🖥️ 환경 정보
- API 환경: [개발/스테이징/프로덕션]
- 클라이언트: [모바일 앱/웹/Postman 등]
- 인증 방식: [JWT/OAuth 등]

## 📝 추가 정보
API 문제에 대한 추가적인 컨텍스트나 정보를 여기에 작성해주세요.