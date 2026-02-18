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
    padding-top: 14px !important;
    padding-bottom: 14px !important;
}
/* 사이드바 드롭다운 호버 색상 */
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"] {
    background-color: #333 !important;
}

</style>
""", unsafe_allow_html=True)
# 다국어 지원
LANG = {
    "ko": {
        "title": "🧩 미로 풀이기",
        "mode_solve": "🖼️ 미로 풀기",
        "mode_gen": "🎲 미로 생성",
        "mode_select": "모드 선택",
        "upload": "미로 이미지 업로드",
        "upload_desc": "미로 이미지를 업로드하면 자동으로 풀어줍니다.",
        "gen_title": "미로 생성",
        "gen_w": "가로", "gen_h": "세로",
        "gen_cells": "미로 셀",
        "gen_btn": "🎲 미로 생성",
        "gen_generating": "미로 생성 중...",
        "solve_btn": "🚀 풀기",
        "solving": "풀이 중...",
        "auto_solving": "자동 풀이 중...",
        "manual_solving": "풀이 시도 중...",
        "success": "✅ 미로 풀이 완료!",
        "fail_auto": "자동 풀이 실패",
        "fail_all": "❌ 모든 조합 실패. 초기화 후 다른 점을 찍어보세요.",
        "fail_solve": "풀이 실패",
        "download": "📥 다운로드",
        "download_orig": "📥 원본 다운로드",
        "download_result": "📥 풀이 결과 다운로드",
        "manual_btn": "🖱️ 수동",
        "reset_btn": "🔄 초기화",
        "retry_btn": "🔄 다시",
        "click_start": "🟢 시작점을 클릭하세요",
        "click_end": "🔴 끝점을 클릭하세요",
        "start_ok": "🟢 시작점 ✓",
        "ready": "🟢 시작점 ✓ ㅤㅤ 🔴 끝점 ✓ ㅤㅤ 준비 완료!",
        "start_ok_click_end": "🟢 시작점 ✓ ㅤㅤ 🔴 끝점을 클릭하세요",
        "auto_fail_manual": "자동 풀이 실패 → 🟢 시작점을 클릭하세요",
        "already_solved": "⚠️ 이미 풀린 이미지 같아요. 원본 미로 이미지를 업로드하세요.",
        "cant_read": "이미지를 읽을 수 없습니다.",
        "trying": "시도",
        "img_size": "이미지",
        "lang_label": "🌐",
    },
    "en": {
        "title": "🧩 Maze Solver",
        "mode_solve": "🖼️ Solve Maze",
        "mode_gen": "🎲 Generate Maze",
        "mode_select": "Mode",
        "upload": "Upload maze image",
        "upload_desc": "Upload a maze image to solve automatically.",
        "gen_title": "Generate Maze",
        "gen_w": "Width", "gen_h": "Height",
        "gen_cells": "Maze cells",
        "gen_btn": "🎲 Generate",
        "gen_generating": "Generating maze...",
        "solve_btn": "🚀 Solve",
        "solving": "Solving...",
        "auto_solving": "Auto-solving...",
        "manual_solving": "Trying to solve...",
        "success": "✅ Maze solved!",
        "fail_auto": "Auto-solve failed",
        "fail_all": "❌ All attempts failed. Reset and try different points.",
        "fail_solve": "Solve failed",
        "download": "📥 Download",
        "download_orig": "📥 Download original",
        "download_result": "📥 Download result",
        "manual_btn": "🖱️ Manual",
        "reset_btn": "🔄 Reset",
        "retry_btn": "🔄 Retry",
        "click_start": "🟢 Click start point",
        "click_end": "🔴 Click end point",
        "start_ok": "🟢 Start ✓",
        "ready": "🟢 Start ✓ ㅤㅤ 🔴 End ✓ ㅤㅤ Ready!",
        "start_ok_click_end": "🟢 Start ✓ ㅤㅤ 🔴 Click end point",
        "auto_fail_manual": "Auto-solve failed → 🟢 Click start point",
        "already_solved": "⚠️ This looks already solved. Upload the original maze.",
        "cant_read": "Cannot read image.",
        "trying": "Trying",
        "img_size": "Image",
        "lang_label": "🌐",
    },
}

lang_choice = st.sidebar.selectbox("🌐", ["한국어", "English"], label_visibility="collapsed")
L = LANG["ko"] if lang_choice == "한국어" else LANG["en"]

st.title(L["title"])

mode = st.radio(L["mode_select"], [L["mode_solve"], L["mode_gen"]], horizontal=True)

if mode == L["mode_gen"]:
    st.subheader(L["gen_title"])
    c1, c2 = st.columns(2)
    with c1:
        maze_w = st.slider(L["gen_w"], 10, 300, 50)
    with c2:
        maze_h = st.slider(L["gen_h"], 10, 300, 50)
    st.caption(f"{L['gen_cells']}: {2*maze_w+1} x {2*maze_h+1}")

    if st.button(L["gen_btn"], type="primary"):
        with st.spinner(L["gen_generating"]):
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
            st.success(L["success"])
            _, dl = cv2.imencode('.png', res)
            st.download_button(L["download_result"], dl.tobytes(), "maze_solved.png", "image/png")
        else:
            nparr = np.frombuffer(st.session_state.gen_img_bytes, np.uint8)
            gen_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            st.image(cv2.cvtColor(gen_img, cv2.COLOR_BGR2RGB), use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button(L["solve_btn"], type="primary"):
                    with st.spinner(L["solving"]):
                        res, info = solve_maze(st.session_state.gen_img_bytes)
                    if res is not None:
                        st.session_state.gen_result = res
                        st.session_state.gen_info = info
                        st.rerun()
                    else:
                        st.error(f"{L['fail_solve']}: {info}")
            with c2:
                st.download_button(L["download_orig"], st.session_state.gen_img_bytes, "maze.png", "image/png")

else:
    st.caption(L["upload_desc"])
    uploaded = st.file_uploader(L["upload"], type=["jpg", "jpeg", "png", "bmp"])

    if uploaded:
        if "solved" in uploaded.name.lower() or "debug" in uploaded.name.lower():
            st.error(L["already_solved"])
            st.stop()

        img_bytes = uploaded.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            st.error(L["cant_read"])
            st.stop()
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h_orig, w_orig = img.shape[:2]

        file_key = f"{uploaded.name}_{len(img_bytes)}"
        if st.session_state.get("last_file") != file_key:
            st.session_state.auto_tried = False
            st.session_state.auto_result = None
            st.session_state.auto_info = None
            st.session_state.last_file = file_key
            st.session_state.points = []
            st.session_state.last_click = None
            st.session_state.manual_result = None
            st.session_state.force_manual = False
            st.session_state.solving = False
            st.session_state.solve_failed = False

        if not st.session_state.get("auto_tried"):
            with st.spinner(L["auto_solving"]):
                result_img, info = solve_maze(img_bytes)
                st.session_state.auto_tried = True
                st.session_state.auto_result = result_img
                st.session_state.auto_info = info

        if st.session_state.auto_result is not None and not st.session_state.get("force_manual"):
            bc1, bc2, bc3 = st.columns([4, 1.5, 1.5])
            with bc1:
                st.success(L["success"])
            with bc2:
                _, buf = cv2.imencode('.png', st.session_state.auto_result)
                st.download_button(L["download"], buf.tobytes(), f"solved_{uploaded.name}", "image/png", use_container_width=True)
            with bc3:
                if st.button(L["manual_btn"], use_container_width=True):
                    st.session_state.force_manual = True
                    st.session_state.auto_result = None
                    st.session_state.points = []
                    st.session_state.last_click = None
                    st.session_state.manual_result = None
                    st.rerun()
            result_rgb = cv2.cvtColor(st.session_state.auto_result, cv2.COLOR_BGR2RGB)
            st.image(result_rgb, use_container_width=True)
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
                        st.success(L["success"])
                    with bc2:
                        _, buf = cv2.imencode('.png', st.session_state.manual_result)
                        st.download_button(L["download"], buf.tobytes(), f"solved_{uploaded.name}", "image/png", use_container_width=True)
                    with bc3:
                        if st.button(L["retry_btn"], use_container_width=True):
                            st.session_state.points = []
                            st.session_state.last_click = None
                            st.session_state.manual_result = None
                            st.rerun()
                elif n_points >= 2:
                    if st.session_state.get("solve_failed"):
                        # 실패 → 빨간 바 + 초기화
                        bc1, bc2 = st.columns([5, 1.5])
                        with bc1:
                            st.error(L["fail_all"])
                        with bc2:
                            if st.button(L["reset_btn"], use_container_width=True):
                                st.session_state.points = []
                                st.session_state.last_click = None
                                st.session_state.solve_failed = False
                                st.rerun()
                    elif st.session_state.get("solving"):
                        # 풀이 중 → 파란 바에 로딩 메시지
                        st.info("⏳ " + L["manual_solving"])
                        combos = [
                            (None, None), (None, 3), (None, 0),
                            (3, 5), (3, 3), (3, 0),
                            (4, 5), (4, 3), (4, 0),
                            (2, 3), (2, 0),
                        ]
                        solved = False
                        for s, b in combos:
                            res, info = solve_maze(img_bytes,
                                manual_start=points[0], manual_end=points[1],
                                override_scale=s, override_blur=b)
                            if res is not None:
                                st.session_state.manual_result = res
                                st.session_state.manual_info = L["success"]
                                st.session_state.solving = False
                                solved = True; break
                        if solved:
                            st.rerun()
                        else:
                            st.session_state.solving = False
                            st.session_state.solve_failed = True
                            st.rerun()
                    else:
                        # 준비 완료 → 파란 바 + 풀기/초기화
                        bc1, bc2, bc3 = st.columns([5, 1.5, 1.5])
                        with bc1:
                            st.info(L["ready"])
                        with bc2:
                            solve_clicked = st.button(L["solve_btn"], type="primary", use_container_width=True)
                        with bc3:
                            if st.button(L["reset_btn"], use_container_width=True):
                                st.session_state.points = []
                                st.session_state.last_click = None
                                st.rerun()
                elif n_points == 1:
                    bc1, bc2 = st.columns([6, 1.5])
                    with bc1:
                        st.warning(L["start_ok_click_end"])
                    with bc2:
                        if st.button(L["reset_btn"], use_container_width=True):
                            st.session_state.points = []
                            st.session_state.last_click = None
                            st.rerun()
                else:
                    st.warning(L["auto_fail_manual"])

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
                    st.session_state.solving = True
                    st.rerun()
