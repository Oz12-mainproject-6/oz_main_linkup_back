---
name: 🗄️ Database Issue
about: 데이터베이스 관련 문제를 신고하세요
title: '[DB] '
labels: ['database', 'backend']
assignees: ''
---

## 🗄️ 데이터베이스 문제
데이터베이스 관련 문제에 대한 명확한 설명을 작성해주세요.

## 📊 관련 테이블/모델
문제가 발생한 테이블이나 모델을 명시해주세요.
```
테이블명: example_table
모델명: ExampleModel
```

## 💾 에러 로그
데이터베이스 관련 에러 로그를 첨부해주세요.
```sql
ERROR: duplicate key value violates unique constraint
DETAIL: Key (email)=(example@test.com) already exists.
```

## 🔍 쿼리 정보
문제가 발생한 쿼리나 ORM 코드:
```sql
SELECT * FROM users WHERE email = 'example@test.com';
```

또는

```python
user = await User.filter(email="example@test.com").first()
```

## 📋 재현 단계
1. 특정 데이터 상태 설정
2. 특정 쿼리 실행
3. 오류 발생 확인

## 🎯 예상 동작
데이터베이스에서 어떤 동작이 일어날 것으로 예상했는지 설명해주세요.

## 🖥️ 환경 정보
- 데이터베이스: PostgreSQL 15
- ORM: Tortoise ORM
- 환경: [개발/스테이징/프로덕션]

## 📝 추가 정보
마이그레이션, 스키마 변경, 또는 기타 관련 정보를 여기에 추가하세요.