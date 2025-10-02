from locust import HttpUser, task, between
import json

class LinkupAPIUser(HttpUser):
    wait_time = between(0.5, 2.0)  # 0.5-2초 대기 (실제 사용자 패턴)
    host = "https://linkup.p-e.kr"
    token = None  # 토큰 저장용
    
    def on_start(self):
        """테스트 시작 시 로그인"""
        response = self.client.post("/api/auth/login", json={
            "email": "fan_dummy_3@gmail.com",
            "password": "fan123!"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            if self.token:
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
    
    @task(4)
    def get_artists(self):
        """아티스트 목록 조회 (가장 자주 조회될 API)"""
        with self.client.get("/api/idol?limit=20", 
                           catch_response=True, name="아티스트목록") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(3)
    def get_posts(self):
        """포스트 목록 조회 (피드 기능)"""
        with self.client.get("/api/posts?limit=20&page=1", 
                           catch_response=True, name="포스트목록") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(3)
    def get_subscriptions(self):
        """구독 목록 조회 (복잡한 조인 쿼리)"""
        if not self.token:
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        with self.client.get("/api/subscriptions/?include_image=true", 
                           headers=headers,
                           catch_response=True, name="구독목록") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(2)
    def get_events(self):
        """이벤트 목록 조회"""
        with self.client.get("/api/events?limit=20", 
                           catch_response=True, name="이벤트목록") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """헬스체크 (기본 연결 확인)"""
        with self.client.get("/health", 
                           catch_response=True, name="헬스체크") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")