# 테이블 명세서

## 1. user (사용자)
팬과 소속사 계정을 모두 포함하는 사용자 테이블

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 사용자 ID |
| email | VARCHAR(200) | UNIQUE, NOT NULL | 이메일 |
| password | VARCHAR(200) | NOT NULL | 비밀번호 (해시화) |
| phone_number | VARCHAR(20) | NULL | 전화번호 |
| nickname | VARCHAR(50) | NULL | 별명 |
| user_type | ENUM('fan', 'company') | NOT NULL, DEFAULT 'fan' | 사용자 타입 |
| push_notification_enabled | BOOLEAN | NOT NULL, DEFAULT TRUE | 푸시 알림 활성화 |
| in_app_notification_enabled | BOOLEAN | NOT NULL, DEFAULT TRUE | 앱 내 알림 활성화 |
| oauth_provider | VARCHAR(50) | NULL | 소셜 로그인 제공자 |
| oauth_id | VARCHAR(200) | NULL | 소셜 로그인 ID |
| is_email_verified | BOOLEAN | NOT NULL, DEFAULT FALSE | 이메일 인증 여부 |
| last_login_at | DATETIME | NULL | 마지막 로그인 시간 |
| deleted_at | DATETIME | NULL | 삭제 시간 (soft delete) |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

**인덱스**
- UNIQUE: (oauth_provider, oauth_id)

---

## 2. company (소속사)
소속사 정보를 담는 테이블 (User와 1:1 관계)

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 소속사 ID |
| user_id | BigInt | FK(user.id), UNIQUE, NOT NULL | 소속사 계정 |
| name | VARCHAR(200) | NOT NULL | 소속사명 |
| business_number | VARCHAR(50) | NULL | 사업자등록번호 |
| contact_email | VARCHAR(200) | NULL | 담당자 이메일 |
| contact_phone | VARCHAR(20) | NULL | 담당자 전화번호 |
| address | TEXT | NULL | 주소 |
| description | TEXT | NULL | 소속사 소개 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

---

## 3. artist (아티스트)
그룹, 멤버, 솔로 아티스트를 통합 관리하는 테이블

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 아티스트 ID |
| company_id | BigInt | FK(company.id), NOT NULL | 소속사 |
| stage_name | VARCHAR(200) | NULL | 개인 예명 (개인 아티스트만) |
| group_name | VARCHAR(200) | NULL | 그룹명 (그룹만) |
| birthdate | DATE | NULL | 생년월일 |
| gender | VARCHAR(200) | NULL | 성별 |
| role | ENUM | NULL | 역할 (leader, main_vocal, etc.) |
| mbti | VARCHAR(4) | NULL | MBTI |
| height | VARCHAR(255) | NULL | 키 |
| nickname | VARCHAR(200) | NULL | 별명 |
| email | VARCHAR(200) | UNIQUE, NOT NULL | 이메일 |
| debut_date | DATE | NULL | 데뷔일 |
| artist_type | ENUM('individual', 'group') | NOT NULL | 아티스트 타입 |
| parent_group_id | BigInt | FK(artist.id), NULL | 소속 그룹 (멤버인 경우) |
| member_count | INT | NULL | 멤버 수 (그룹인 경우) |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 활동 상태 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

**Role ENUM 값:**
- leader, main_vocal, lead_vocal, sub_vocal
- main_rapper, lead_rapper, sub_rapper
- main_dancer, lead_dancer, sub_dancer
- visual, maknae, solo

---

## 4. events (이벤트)
아티스트의 스케줄/이벤트 정보

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 이벤트 ID |
| artist_id | BigInt | FK(artist.id), NOT NULL | 아티스트 |
| title | VARCHAR(200) | NOT NULL | 이벤트 제목 |
| description | TEXT | NULL | 이벤트 설명 |
| start_time | DATETIME | NOT NULL | 시작 시간 |
| end_time | DATETIME | NULL | 종료 시간 |
| location | VARCHAR(200) | NULL | 위치 |
| category | ENUM | NOT NULL | 이벤트 카테고리 |
| instant_notification_sent | BOOLEAN | NOT NULL, DEFAULT FALSE | 등록 즉시 알림 발송 여부 |
| one_hour_notification_sent | BOOLEAN | NOT NULL, DEFAULT FALSE | 1시간 전 알림 발송 여부 |
| visibility | ENUM('public', 'private', 'subscribers_only') | NOT NULL, DEFAULT 'public' | 공개 설정 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 활성 상태 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

**Category ENUM 값:**
- concert, fanmeeting, showcase, festival, award_show
- tv_show, broadcast, photoshoot, interview, release, other

---

## 5. post (포스트)
팬이 작성하는 게시글

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 포스트 ID |
| user_id | BigInt | FK(user.id), NOT NULL | 작성자 |
| artist_id | BigInt | FK(artist.id), NOT NULL | 관련 아티스트 |
| content | TEXT | NOT NULL | 게시글 내용 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

---

## 6. comment (댓글)
포스트에 달리는 댓글

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 댓글 ID |
| post_id | BigInt | FK(post.id), NOT NULL | 포스트 |
| user_id | BigInt | FK(user.id), NOT NULL | 작성자 |
| content | VARCHAR(500) | NOT NULL | 댓글 내용 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

---

## 7. like (좋아요)
포스트에 대한 좋아요

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 좋아요 ID |
| post_id | BigInt | FK(post.id), NOT NULL | 포스트 |
| user_id | BigInt | FK(user.id), NOT NULL | 사용자 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

**인덱스**
- UNIQUE: (post_id, user_id)

---

## 8. subscription (구독)
팬이 아티스트를 구독하는 관계

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 구독 ID |
| user_id | BigInt | FK(user.id), NOT NULL | 팬 유저 |
| artist_id | BigInt | FK(artist.id), NOT NULL | 구독한 아티스트 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | 구독 상태 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

**인덱스**
- UNIQUE: (user_id, artist_id)

---

## 9. notifications (알림)
사용자에게 전송되는 알림

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 알림 ID |
| user_id | BigInt | FK(user.id), NOT NULL | 사용자 |
| type | ENUM | NOT NULL | 알림 타입 |
| message | VARCHAR(200) | NULL | 알림 메시지 |
| entity_type | ENUM('Events', 'Post', 'Artist') | NULL | 관련 엔티티 타입 |
| entity_id | BigInt | NULL | 관련 엔티티 ID |
| read_at | DATETIME | NULL | 읽은 시간 |
| url | VARCHAR(255) | NULL | 알림 관련 URL |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

**Type ENUM 값:**
- event_reminder, new_post, subscription_confirmed, artist_update, system_notice

---

## 10. shared_image (공유 이미지)
소속사가 업로드하고 구독자가 사용할 수 있는 이미지

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 이미지 ID |
| uploaded_by_id | BigInt | FK(user.id), NOT NULL | 업로드한 사용자 (소속사) |
| artist_id | BigInt | FK(artist.id), NULL | 관련 아티스트 |
| event_id | BigInt | FK(events.id), NULL | 관련 이벤트 |
| url | TEXT | NOT NULL | S3 이미지 URL |
| name | VARCHAR(255) | NULL | 원본 파일명 |
| size | BigInt | NULL | 파일 크기 (bytes) |
| content_type | VARCHAR(100) | NULL | MIME 타입 |
| image_type | ENUM('face', '전체 사진', '배너 사진', 'post') | NOT NULL | 이미지 타입 |
| is_public | BOOLEAN | NOT NULL, DEFAULT TRUE | 구독자가 사용 가능한지 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

---

## 11. image_usage (이미지 사용 기록)
팬 포스트에서 공유 이미지 사용 기록

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 사용 기록 ID |
| shared_image_id | BigInt | FK(shared_image.id), NOT NULL | 사용된 이미지 |
| post_id | BigInt | FK(post.id), NULL | 포스트 |
| used_by_id | BigInt | FK(user.id), NOT NULL | 사용한 사용자 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

---

## 12. email_verification (이메일 인증)
이메일 인증 코드 관리

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | BigInt | PK, AUTO_INCREMENT | 인증 ID |
| email | VARCHAR(200) | NOT NULL | 인증할 이메일 |
| code | VARCHAR(6) | NOT NULL | 인증 코드 |
| expires_at | DATETIME | NOT NULL | 만료 시간 |
| is_used | BOOLEAN | NOT NULL, DEFAULT FALSE | 사용 여부 |
| created_at | DATETIME | NOT NULL, AUTO | 생성일시 |
| updated_at | DATETIME | NOT NULL, AUTO | 수정일시 |

---

## 주요 비즈니스 로직

### Soft Delete
- `user.deleted_at`: 사용자 소프트 삭제
- 삭제된 사용자는 로그인 불가, 관련 데이터는 유지

### 구독 시스템
- 팬(user_type='fan')만 아티스트 구독 가능
- 구독 시 알림 설정에 따라 이벤트 알림 수신

### 이미지 공유
- 소속사가 이미지 업로드
- 구독자는 공개된 이미지를 포스트에 사용 가능
- 사용 기록을 통해 추적

### 알림 시스템
- 이벤트 등록 즉시 + 1시간 전 알림
- 사용자별 알림 설정 적용
- 읽음 처리 지원