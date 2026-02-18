# 🧩 Maze Solver

미로 이미지를 업로드하면 자동으로 풀어주는 웹 앱.

## 기능
- 자동 입구/출구 감지 + BFS 최단 경로
- 실패 시 수동 모드 (시작/끝점 클릭)
- 다양한 전처리 조합 자동 재시도
- 직각/곡선/원형 미로 지원

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 배포
Streamlit Community Cloud에서 GitHub 연결 후 자동 배포.
