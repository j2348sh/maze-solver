"""미로 풀이 핵심 로직 (Streamlit용, GUI 제거)"""
import cv2
import numpy as np
from collections import deque


def find_entry_exit(binary, top, bottom, left, right, border_thick):
    """4면 테두리에서 입구/출구 갭 찾기"""
    h, w = binary.shape
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2

    def find_gap_horizontal(y_range, x_start, x_end):
        for scan_y in y_range:
            gaps = []
            in_gap = False
            gap_start = 0
            for x in range(x_start, x_end + 1):
                if binary[scan_y, x] == 255 and not in_gap:
                    in_gap = True; gap_start = x
                elif binary[scan_y, x] == 0 and in_gap:
                    in_gap = False
                    gap_w = x - gap_start
                    if 2 < gap_w < (x_end - x_start) * 0.3:
                        gaps.append((gap_start, x - 1, gap_w))
            if in_gap:
                gap_w = x_end - gap_start
                if 2 < gap_w < (x_end - x_start) * 0.3:
                    gaps.append((gap_start, x_end, gap_w))
            if gaps:
                best = min(gaps, key=lambda g: abs((g[0]+g[1])//2 - center_x))
                xs = list(range(best[0], best[1] + 1))
                return xs, 'top' if y_range[0] < center_y else 'bottom'
        return [], None

    def find_gap_vertical(x_range, y_start, y_end):
        for scan_x in x_range:
            gaps = []
            in_gap = False
            gap_start = 0
            for y in range(y_start, y_end + 1):
                if binary[y, scan_x] == 255 and not in_gap:
                    in_gap = True; gap_start = y
                elif binary[y, scan_x] == 0 and in_gap:
                    in_gap = False
                    gap_h = y - gap_start
                    if 2 < gap_h < (y_end - y_start) * 0.3:
                        gaps.append((gap_start, y - 1, gap_h))
            if in_gap:
                gap_h = y_end - gap_start
                if 2 < gap_h < (y_end - y_start) * 0.3:
                    gaps.append((gap_start, y_end, gap_h))
            if gaps:
                best = min(gaps, key=lambda g: abs((g[0]+g[1])//2 - center_y))
                ys = list(range(best[0], best[1] + 1))
                return ys, 'left' if x_range[0] < center_x else 'right'
        return [], None

    all_entries = []
    xs, side = find_gap_horizontal(list(range(max(0, top-5), top+border_thick+3)), left+border_thick, right-border_thick)
    if xs: all_entries.append((xs, side))
    xs, side = find_gap_horizontal(list(range(min(h-1, bottom+5), bottom-border_thick-3, -1)), left+border_thick, right-border_thick)
    if xs: all_entries.append((xs, side))
    ys, side = find_gap_vertical(list(range(max(0, left-5), left+border_thick+3)), top+border_thick, bottom-border_thick)
    if ys: all_entries.append((ys, side))
    ys, side = find_gap_vertical(list(range(min(w-1, right+5), right-border_thick-3, -1)), top+border_thick, bottom-border_thick)
    if ys: all_entries.append((ys, side))

    start_priority = {'top': 0, 'left': 1, 'right': 2, 'bottom': 3}
    all_entries.sort(key=lambda e: start_priority.get(e[1], 99))
    if len(all_entries) >= 2:
        return all_entries[0], all_entries[-1]
    elif len(all_entries) == 1:
        return all_entries[0], ([], None)
    return ([], None), ([], None)


def find_entry_radial(binary):
    """방사형 스캔으로 입구/출구 감지 (원형/다각형 미로)"""
    h, w = binary.shape
    wall = (binary == 0)
    ys, xs = np.where(wall)
    if len(ys) == 0: return []
    cy = int(np.mean(ys)); cx = int(np.mean(xs))
    dists = np.sqrt((ys - cy)**2 + (xs - cx)**2)
    outer_r = np.percentile(dists, 95)
    inv = wall.astype(np.uint8) * 255
    dist_wall = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
    wall_dists = dist_wall[inv == 255]
    median_wall = float(np.median(wall_dists)) if len(wall_dists) > 0 else 2
    wall_thick_limit = max(8, int(median_wall * 6))
    n_angles = 720
    entry_angles = []
    for i in range(n_angles):
        angle = 2 * np.pi * i / n_angles
        sin_a, cos_a = np.sin(angle), np.cos(angle)
        r_start = int(outer_r * 0.5); r_end = int(outer_r * 1.3)
        wall_segs = []; in_wall = False; ws = 0
        for r in range(r_start, r_end):
            y = int(cy + r * sin_a); x = int(cx + r * cos_a)
            if 0 <= y < h and 0 <= x < w:
                is_w = binary[y, x] == 0
                if is_w and not in_wall: in_wall = True; ws = r
                elif not is_w and in_wall: in_wall = False; wall_segs.append(r - ws)
        if in_wall: wall_segs.append(r_end - ws)
        if wall_segs:
            if wall_segs[-1] > wall_thick_limit: entry_angles.append(i)
        else:
            entry_angles.append(i)
    if not entry_angles: return []
    groups = []; start = entry_angles[0]; prev = entry_angles[0]
    for g in entry_angles[1:]:
        if g == prev + 1: prev = g
        else: groups.append((start, prev)); start = g; prev = g
    groups.append((start, prev))
    if len(groups) >= 2 and groups[-1][1] == n_angles - 1 and groups[0][0] == 0:
        merged = (groups[-1][0], groups[0][1] + n_angles)
        groups = groups[1:-1]; groups.append(merged)
    mg = [groups[0]]
    for gs, ge in groups[1:]:
        pgs, pge = mg[-1]
        if gs - pge <= 10: mg[-1] = (pgs, ge)
        else: mg.append((gs, ge))
    result = []
    for gs, ge in mg:
        size = ge - gs + 1
        mid_idx = (gs + ge) / 2
        if mid_idx >= n_angles: mid_idx -= n_angles
        mid_angle = 2 * np.pi * mid_idx / n_angles
        ey = int(cy + (outer_r - 10) * np.sin(mid_angle))
        ex = int(cx + (outer_r - 10) * np.cos(mid_angle))
        result.append((ey, ex, size))
    result.sort(key=lambda e: -e[2])
    return result


def solve_maze(img_bytes, manual_start=None, manual_end=None, override_scale=None, override_blur=None):
    """미로 풀이 메인 함수. 성공 시 (result_img, info) 반환, 실패 시 (None, info) 반환"""
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None, "이미지를 읽을 수 없습니다."

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    otsu_val, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    light_walls = otsu_val > 170
    thresh_val = int(otsu_val) if light_walls else 128
    _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)

    # 업스케일
    temp_dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    white_dists = temp_dist[binary == 255]
    median_passage = np.median(white_dists) if len(white_dists) > 0 else 5

    if median_passage < 5:
        if light_walls:
            scale = 4
        else:
            scale = int(np.ceil(6 / median_passage))
            scale = min(scale, 4)
        if override_scale:
            scale = override_scale
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_k = 3 if light_walls else 5
        if override_blur is not None:
            blur_k = override_blur
        if blur_k > 0:
            gray = cv2.GaussianBlur(gray, (blur_k, blur_k), 0)
        _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)

    h, w = binary.shape

    # 테두리 찾기
    row_black = np.sum(binary == 0, axis=1)
    col_black = np.sum(binary == 0, axis=0)
    top = next((y for y in range(h) if row_black[y] > w * 0.3), 0)
    bottom = next((y for y in range(h-1, -1, -1) if row_black[y] > w * 0.3), h-1)
    left = next((x for x in range(w) if col_black[x] > h * 0.3), 0)
    right = next((x for x in range(w-1, -1, -1) if col_black[x] > h * 0.3), w-1)
    margin = max(30, h // 50)
    if top < margin: top = 0
    if bottom > h - margin - 1: bottom = h - 1
    if left < margin: left = 0
    if right > w - margin - 1: right = w - 1

    edge_maze = (top == 0 and bottom == h-1 and left == 0 and right == w-1)
    maze = np.zeros((h, w), dtype=np.uint8)
    maze[top:bottom+1, left:right+1] = binary[top:bottom+1, left:right+1]
    border_thick = 3

    if not edge_maze:
        def measure_margin_side(binary, side, top, bottom, left, right):
            if side == 'top':
                for y in range(top, min(top+50, binary.shape[0])):
                    if np.sum(binary[y, left:right+1] == 0) > (right-left) * 0.3: return y - top
            elif side == 'bottom':
                for y in range(bottom, max(bottom-50, 0), -1):
                    if np.sum(binary[y, left:right+1] == 0) > (right-left) * 0.3: return bottom - y
            elif side == 'left':
                for x in range(left, min(left+50, binary.shape[1])):
                    if np.sum(binary[top:bottom+1, x] == 0) > (bottom-top) * 0.3: return x - left
            elif side == 'right':
                for x in range(right, max(right-50, 0), -1):
                    if np.sum(binary[top:bottom+1, x] == 0) > (bottom-top) * 0.3: return right - x
            return border_thick
        tm = max(border_thick, measure_margin_side(binary, 'top', top, bottom, left, right) + 2)
        bm = max(border_thick, measure_margin_side(binary, 'bottom', top, bottom, left, right) + 2)
        lm = max(border_thick, measure_margin_side(binary, 'left', top, bottom, left, right) + 2)
        rm = max(border_thick, measure_margin_side(binary, 'right', top, bottom, left, right) + 2)
        maze[top:top+tm, left:right+1] = 0
        maze[bottom-bm+1:bottom+1, left:right+1] = 0
        maze[top:bottom+1, left:left+lm] = 0
        maze[top:bottom+1, right-rm+1:right+1] = 0

    if edge_maze:
        border_thick = 1
        if manual_start and manual_end:
            for x in range(w):
                col = binary[:, x]; idx = np.argmax(col == 0)
                if idx > 0: maze[:idx, x] = 0
            for x in range(w):
                col = binary[::-1, x]; idx = np.argmax(col == 0)
                if idx > 0: maze[h-idx:, x] = 0
            for y in range(h):
                row = binary[y, :]; idx = np.argmax(row == 0)
                if idx > 0: maze[y, :idx] = 0
            for y in range(h):
                row = binary[y, ::-1]; idx = np.argmax(row == 0)
                if idx > 0: maze[y, w-idx:] = 0
            corners = [(0, 0), (0, w-1), (h-1, 0), (h-1, w-1)]
            for cy, cx in corners:
                if maze[cy, cx] == 255:
                    q = deque([(cy, cx)]); seen = set(); seen.add((cy, cx))
                    while q:
                        fy, fx = q.popleft(); maze[fy, fx] = 0
                        for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                            ny, nx = fy+dy, fx+dx
                            if 0<=ny<h and 0<=nx<w and (ny,nx) not in seen and maze[ny,nx]==255:
                                seen.add((ny, nx)); q.append((ny, nx))
        else:
            maze[0, :] = 0; maze[h-1, :] = 0; maze[:, 0] = 0; maze[:, w-1] = 0

    # 입출구 찾기
    if manual_start and manual_end:
        scale_applied = h / cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_GRAYSCALE).shape[0]
        start = (int(manual_start[0] * scale_applied), int(manual_start[1] * scale_applied))
        finish = (int(manual_end[0] * scale_applied), int(manual_end[1] * scale_applied))

        if not edge_maze:
            maze = binary.copy()
        protect_radius = max(80, int(h * 0.07))
        temp_wall = maze.copy()
        for pt in [start, finish]:
            cv2.circle(temp_wall, (pt[1], pt[0]), protect_radius, 0, 2)
        outside = np.zeros((h, w), dtype=np.uint8)
        q = deque()
        for cy, cx in [(0,0),(0,w-1),(h-1,0),(h-1,w-1)]:
            if 0<=cy<h and 0<=cx<w and temp_wall[cy, cx] == 255 and outside[cy, cx] == 0:
                q.append((cy, cx)); outside[cy, cx] = 255
        while q:
            fy, fx = q.popleft()
            for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                ny, nx = fy+dy, fx+dx
                if 0<=ny<h and 0<=nx<w and outside[ny,nx]==0 and temp_wall[ny,nx]==255:
                    outside[ny,nx] = 255; q.append((ny, nx))
        protect = np.zeros((h, w), dtype=bool)
        Y, X = np.mgrid[0:h, 0:w]
        for pt in [start, finish]:
            protect |= ((Y - pt[0])**2 + (X - pt[1])**2 <= protect_radius**2)
        maze[(outside == 255) & ~protect] = 0

        def snap_to_white(pt, maze, radius=80):
            py, px = pt; best, best_d = None, float('inf')
            for dy in range(-radius, radius+1):
                for dx in range(-radius, radius+1):
                    ny, nx = py+dy, px+dx
                    if 0<=ny<h and 0<=nx<w and maze[ny,nx]==255:
                        d = abs(dy)+abs(dx)
                        if d < best_d: best_d, best = d, (ny,nx)
            return best if best else pt
        start = snap_to_white(start, maze)
        finish = snap_to_white(finish, maze)

        def restore_connected(pt, binary, maze, max_pixels=5000):
            py, px = pt
            if not (0<=py<h and 0<=px<w): return
            if maze[py, px] != 255:
                found = False
                for r in range(1, 50):
                    for dy in range(-r, r+1):
                        for dx in range(-r, r+1):
                            ny, nx = py+dy, px+dx
                            if 0<=ny<h and 0<=nx<w and maze[ny,nx]==255:
                                py, px = ny, nx; found = True; break
                        if found: break
                    if found: break
                if not found: return
            q = deque([(py, px)]); seen = set(); seen.add((py, px)); count = 0
            while q and count < max_pixels:
                cy, cx = q.popleft(); maze[cy, cx] = 255; count += 1
                for dy, dx in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ny, nx = cy+dy, cx+dx
                    if 0<=ny<h and 0<=nx<w and (ny,nx) not in seen and binary[ny,nx]==255:
                        if maze[ny,nx]==255:
                            seen.add((ny, nx)); q.append((ny, nx))
                        else:
                            has_n = any(0<=ny+d2<h and 0<=nx+d3<w and maze[ny+d2,nx+d3]==255 for d2,d3 in [(-1,0),(1,0),(0,-1),(0,1)])
                            if has_n: seen.add((ny, nx)); q.append((ny, nx))
        for pt in [start, finish]:
            restore_connected(pt, binary, maze)
        start = snap_to_white(start, maze)
        finish = snap_to_white(finish, maze)
    else:
        (sd, ss), (fd, fs) = find_entry_exit(binary, top, bottom, left, right, border_thick)
        start = finish = None
        def open_and_set(data, side, is_start):
            if not data: return None
            if side in ('top', 'bottom'):
                xs = data; cx = (xs[0] + xs[-1]) // 2
                if side == 'top':
                    for x in xs:
                        for y in range(max(0,top-2), top+border_thick+3):
                            if 0<=y<h: maze[y,x] = 255
                    pt = (top+border_thick, cx)
                    if maze[pt[0],pt[1]] != 255:
                        for y in range(top, top+20):
                            if maze[y,cx]==255: return (y,cx)
                    return pt
                else:
                    for x in xs:
                        for y in range(bottom-border_thick-2, min(h,bottom+3)):
                            if 0<=y<h: maze[y,x] = 255
                    pt = (bottom-border_thick, cx)
                    if maze[pt[0],pt[1]] != 255:
                        for y in range(bottom, bottom-20, -1):
                            if maze[y,cx]==255: return (y,cx)
                    return pt
            else:
                ys = data; cy = (ys[0] + ys[-1]) // 2
                if side == 'left':
                    for y in ys:
                        for x in range(max(0,left-2), left+border_thick+3):
                            if 0<=x<w: maze[y,x] = 255
                    pt = (cy, left+border_thick)
                    if maze[pt[0],pt[1]] != 255:
                        for x in range(left, left+20):
                            if maze[cy,x]==255: return (cy,x)
                    return pt
                else:
                    for y in ys:
                        for x in range(right-border_thick-2, min(w,right+3)):
                            if 0<=x<w: maze[y,x] = 255
                    pt = (cy, right-border_thick)
                    if maze[pt[0],pt[1]] != 255:
                        for x in range(right, right-20, -1):
                            if maze[cy,x]==255: return (cy,x)
                    return pt
        start = open_and_set(sd, ss, True)
        finish = open_and_set(fd, fs, False)
        if start is None or finish is None:
            radial = find_entry_radial(binary)
            if len(radial) >= 2:
                def snap_r(pt, m, radius=30):
                    py, px = pt; best, best_d = None, float('inf')
                    for dy in range(-radius, radius+1):
                        for dx in range(-radius, radius+1):
                            ny, nx = py+dy, px+dx
                            if 0<=ny<h and 0<=nx<w and m[ny,nx]==255:
                                d = abs(dy)+abs(dx)
                                if d < best_d: best_d, best = d, (ny,nx)
                    return best
                s = snap_r(radial[0][:2], maze)
                f = snap_r(radial[1][:2], maze)
                if s and f: start, finish = s, f

    if start is None or finish is None:
        return None, "입구/출구를 찾을 수 없습니다."

    # 스켈레톤 + BFS
    try:
        skeleton = cv2.ximgproc.thinning(maze, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    except Exception:
        skeleton = None

    def find_nearest(pt, skel, radius=50):
        py, px = pt; best, best_d = None, float('inf')
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                ny, nx = py+dy, px+dx
                if 0<=ny<h and 0<=nx<w and skel[ny,nx]==255:
                    d = abs(dy)+abs(dx)
                    if d < best_d: best_d, best = d, (ny, nx)
        return best

    def bfs(search_map, s, f, use_8dir, check_diag):
        visited = np.zeros((h, w), dtype=bool)
        parent = {}; queue = deque([s]); visited[s[0], s[1]] = True
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        if use_8dir: dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
        while queue:
            cy, cx = queue.popleft()
            if (cy, cx) == f: return True, parent, s, f
            for dy, dx in dirs:
                ny, nx = cy+dy, cx+dx
                if 0<=ny<h and 0<=nx<w and not visited[ny,nx] and search_map[ny,nx]==255:
                    if check_diag and abs(dy)==1 and abs(dx)==1:
                        if maze[cy,nx]==0 and maze[ny,cx]==0: continue
                    visited[ny,nx] = True; parent[(ny,nx)] = (cy, cx); queue.append((ny, nx))
        return False, parent, s, f

    found = False
    if skeleton is not None:
        s = find_nearest(start, skeleton)
        f = find_nearest(finish, skeleton)
        if s and f:
            found, parent, s, f = bfs(skeleton, s, f, True, True)
            if not found:
                found, parent, s, f = bfs(maze, start, finish, False, False)
        else:
            found, parent, s, f = bfs(maze, start, finish, False, False)
    else:
        found, parent, s, f = bfs(maze, start, finish, False, False)

    if not found:
        if not manual_start:
            radial = find_entry_radial(binary)
            if len(radial) >= 2:
                def snap2(pt, m, radius=30):
                    py, px = pt; best, best_d = None, float('inf')
                    for dy in range(-radius, radius+1):
                        for dx in range(-radius, radius+1):
                            ny, nx = py+dy, px+dx
                            if 0<=ny<h and 0<=nx<w and m[ny,nx]==255:
                                d = abs(dy)+abs(dx)
                                if d < best_d: best_d, best = d, (ny,nx)
                    return best
                rs = snap2(radial[0][:2], maze)
                rf = snap2(radial[1][:2], maze)
                if rs and rf:
                    found, parent, s, f = bfs(maze, rs, rf, False, False)

    if not found:
        return None, "경로를 찾을 수 없습니다."

    # 경로 추출
    path = []; cur = f
    while cur != s: path.append(cur); cur = parent[cur]
    path.append(s); path.reverse()

    # 경로 그리기
    result = img.copy()
    dist = cv2.distanceTransform(maze, cv2.DIST_L2, 5)
    path_dists = [dist[y,x] for y,x in path if dist[y,x]>0]
    median_r = np.median(path_dists) if path_dists else 5
    line_thickness = max(2, int(median_r * 0.4))

    def simplify(path):
        if len(path) < 3: return path
        pts = [path[0]]
        for i in range(1, len(path)-1):
            py,px = path[i-1]; cy,cx = path[i]; ny,nx = path[i+1]
            if (cy-py, cx-px) != (ny-cy, nx-cx): pts.append(path[i])
        pts.append(path[-1]); return pts

    kp = simplify(path)
    for i in range(len(kp)-1):
        y1,x1 = kp[i]; y2,x2 = kp[i+1]
        cv2.line(result, (x1,y1), (x2,y2), (0,0,255), line_thickness, cv2.LINE_AA)
    for y,x in kp:
        cv2.circle(result, (x,y), line_thickness//2, (0,0,255), -1, cv2.LINE_AA)

    info = "미로 풀이 완료!"
    return result, info
