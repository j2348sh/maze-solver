import streamlit as st
from PIL import Image as PILImage
PILImage.MAX_IMAGE_PIXELS = None
import cv2
import numpy as np
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates
from maze_solver import solve_maze
from maze_generator import create_maze, maze_to_image

st.set_page_config(page_title="🧩 Maze Solver", layout="centered")

# 상태 바 스타일
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] button {
    padding-top: 13px !important;
    padding-bottom: 13px !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🧩 미로 풀이기")

mode = st.radio("모드 선택", ["🖼️ 미로 풀기", "🎲 미로 생성"], horizontal=True)

if mode == "🎲 미로 생성":
    st.subheader("미로 생성")
    c1, c2 = st.columns(2)
    with c1:
        maze_w = st.slider("가로", 10, 300, 50)
    with c2:
        maze_h = st.slider("세로", 10, 300, 50)
    st.caption(f"미로 셀: {2*maze_w+1} x {2*maze_h+1}")

    if st.button("🎲 미로 생성", type="primary"):
        with st.spinner(f"{maze_w}x{maze_h} 미로 생성 중..."):
            grid = create_maze(maze_w, maze_h)
            img_color = maze_to_image(grid, target_size=2000)
            _, buf = cv2.imencode('.png', img_color)
            st.session_state.gen_img_bytes = buf.tobytes()
            st.session_state.gen_result = None
            st.session_state.gen_info = None

    if st.session_state.get("gen_img_bytes"):
        if st.session_state.get("gen_result") is not None:
            res = st.session_state.gen_result
            st.image(cv2.cvtColor(res, cv2.COLOR_BGR2RGB), use_container_width=True)
            st.success(f"✅ {st.session_state.gen_info}")
            _, dl = cv2.imencode('.png', res)
            st.download_button("📥 풀이 결과 다운로드", dl.tobytes(), "maze_solved.png", "image/png")
        else:
            nparr = np.frombuffer(st.session_state.gen_img_bytes, np.uint8)
            gen_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            st.image(cv2.cvtColor(gen_img, cv2.COLOR_BGR2RGB), use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🚀 풀기", type="primary"):
                    with st.spinner("풀이 중..."):
                        res, info = solve_maze(st.session_state.gen_img_bytes)
                    if res is not None:
                        st.session_state.gen_result = res
                        st.session_state.gen_info = info
                        st.rerun()
                    else:
                        st.error(f"풀이 실패: {info}")
            with c2:
                st.download_button("📥 원본 다운로드", st.session_state.gen_img_bytes, "maze.png", "image/png")

else:
    st.caption("미로 이미지를 업로드하면 자동으로 풀어줍니다.")
    uploaded = st.file_uploader("미로 이미지 업로드", type=["jpg", "jpeg", "png", "bmp"])

    if uploaded:
        if "solved" in uploaded.name.lower() or "debug" in uploaded.name.lower():
            st.error("⚠️ 이미 풀린 이미지 같아요. 원본 미로 이미지를 업로드하세요.")
            st.stop()

        img_bytes = uploaded.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            st.error("이미지를 읽을 수 없습니다.")
            st.stop()
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h_orig, w_orig = img.shape[:2]

        if st.session_state.get("last_file") != uploaded.name:
            st.session_state.auto_tried = False
            st.session_state.auto_result = None
            st.session_state.auto_info = None
            st.session_state.last_file = uploaded.name
            st.session_state.points = []
            st.session_state.last_click = None
            st.session_state.manual_result = None

        if not st.session_state.get("auto_tried"):
            with st.spinner("자동 풀이 중..."):
                result_img, info = solve_maze(img_bytes)
                st.session_state.auto_tried = True
                st.session_state.auto_result = result_img
                st.session_state.auto_info = info

        if st.session_state.auto_result is not None:
            result_rgb = cv2.cvtColor(st.session_state.auto_result, cv2.COLOR_BGR2RGB)
            st.image(result_rgb, use_container_width=True)
            st.success(f"✅ {st.session_state.auto_info}")
            _, buf = cv2.imencode('.png', st.session_state.auto_result)
            st.download_button("📥 결과 다운로드", buf.tobytes(), f"solved_{uploaded.name}", "image/png")
        else:
            # 수동 모드
            points = st.session_state.get("points", [])
            n_points = len(points)

            # 통합 상태 바 (container 안에 텍스트 + 버튼)
            bar = st.container()
            with bar:
                if st.session_state.get("manual_result") is not None:
                    # 풀이 성공
                    bc1, bc2, bc3 = st.columns([5, 1.5, 1.5])
                    with bc1:
                        st.success(f"✅ {st.session_state.get('manual_info', '')}")
                    with bc2:
                        _, buf = cv2.imencode('.png', st.session_state.manual_result)
                        st.download_button("📥 다운로드", buf.tobytes(), f"solved_{uploaded.name}", "image/png", use_container_width=True)
                    with bc3:
                        if st.button("🔄 다시", use_container_width=True):
                            st.session_state.points = []
                            st.session_state.last_click = None
                            st.session_state.manual_result = None
                            st.rerun()
                elif n_points >= 2:
                    # 점 2개 찍음 → 풀기/초기화
                    bc1, bc2, bc3 = st.columns([5, 1.5, 1.5])
                    with bc1:
                        st.info("🟢 시작점 ✓ ㅤㅤ 🔴 끝점 ✓ ㅤㅤ 준비 완료!")
                    with bc2:
                        solve_clicked = st.button("🚀 풀기", type="primary", use_container_width=True)
                    with bc3:
                        if st.button("🔄 초기화", use_container_width=True):
                            st.session_state.points = []
                            st.session_state.last_click = None
                            st.rerun()
                elif n_points == 1:
                    bc1, bc2 = st.columns([6, 1.5])
                    with bc1:
                        st.warning("🟢 시작점 ✓ ㅤㅤ 🔴 끝점을 클릭하세요")
                    with bc2:
                        if st.button("🔄 초기화", use_container_width=True):
                            st.session_state.points = []
                            st.session_state.last_click = None
                            st.rerun()
                else:
                    st.warning("자동 풀이 실패 → 🟢 시작점을 클릭하세요")

            # 이미지 표시
            if st.session_state.get("manual_result") is not None:
                res_rgb = cv2.cvtColor(st.session_state.manual_result, cv2.COLOR_BGR2RGB)
                st.image(res_rgb, use_container_width=True)
            else:
                display_w = min(700, w_orig)
                scale_d = display_w / w_orig
                display_h = int(h_orig * scale_d)

                preview = img.copy()
                for i, (py, px) in enumerate(points[:2]):
                    color = (0, 255, 0) if i == 0 else (0, 0, 255)
                    r = max(5, w_orig // 100)
                    cv2.circle(preview, (px, py), r, color, -1)
                    cv2.putText(preview, "S" if i==0 else "E", (px+r+2, py+4),
                                cv2.FONT_HERSHEY_SIMPLEX, max(0.4, w_orig/2000), color, 2)
                pil_preview = Image.fromarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)).resize((display_w, display_h))

                coords = streamlit_image_coordinates(pil_preview, key=f"click_{n_points}")
                if coords and coords.get("x") is not None and coords.get("y") is not None:
                    click_x = int(coords["x"] / scale_d)
                    click_y = int(coords["y"] / scale_d)
                    new_click = (click_y, click_x)
                    if new_click != st.session_state.get("last_click") and n_points < 2:
                        if click_x > 3 or click_y > 3:
                            points.append(new_click)
                            st.session_state.points = points
                            st.session_state.last_click = new_click
                            st.rerun()

                # 풀이 실행
                if n_points >= 2 and 'solve_clicked' in dir() and solve_clicked:
                    combos = [
                        (None, None, "기본"),
                        (None, 3, "blur=3"), (None, 0, "blur=0"),
                        (3, 5, "3x,b5"), (3, 3, "3x,b3"), (3, 0, "3x,b0"),
                        (4, 5, "4x,b5"), (4, 3, "4x,b3"), (4, 0, "4x,b0"),
                        (2, 3, "2x,b3"), (2, 0, "2x,b0"),
                    ]
                    progress = st.progress(0)
                    status = st.empty()
                    solved = False
                    for i, (s, b, lbl) in enumerate(combos):
                        progress.progress((i+1)/len(combos))
                        status.text(f"시도: {lbl}...")
                        res, info = solve_maze(img_bytes,
                            manual_start=points[0], manual_end=points[1],
                            override_scale=s, override_blur=b)
                        if res is not None:
                            st.session_state.manual_result = res
                            st.session_state.manual_info = f"성공 ({lbl}): {info}"
                            status.empty(); progress.empty()
                            solved = True; st.rerun(); break
                    if not solved:
                        status.empty(); progress.empty()
                        st.error("❌ 모든 조합 실패. 초기화 후 다른 점을 찍어보세요.")
