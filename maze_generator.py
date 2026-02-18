"""미로 생성기 (반복 DFS)"""
import random
import numpy as np
import cv2


def create_maze(width, height, seed=None):
    if seed is not None:
        random.seed(seed)
    maze = [[1] * (2 * width + 1) for _ in range(2 * height + 1)]
    stack = [(0, 0)]
    maze[1][1] = 0
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    while stack:
        x, y = stack[-1]
        neighbors = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and maze[2*ny+1][2*nx+1] == 1:
                neighbors.append((nx, ny, dx, dy))
        if neighbors:
            nx, ny, dx, dy = random.choice(neighbors)
            maze[2*y+1+dy][2*x+1+dx] = 0
            maze[2*ny+1][2*nx+1] = 0
            stack.append((nx, ny))
        else:
            stack.pop()
    maze[1][0] = 0
    maze[-2][-1] = 0
    return np.array(maze, dtype=np.uint8)


def maze_to_image(maze_grid, target_size=2000):
    """미로를 이미지로 변환. target_size에 맞춰 셀 크기 자동 조정"""
    h, w = maze_grid.shape
    cell_size = max(1, target_size // max(h, w))
    img = np.ones((h * cell_size, w * cell_size), dtype=np.uint8) * 255
    for y in range(h):
        row = maze_grid[y]
        for x in range(w):
            if row[x] == 1:
                img[y*cell_size:(y+1)*cell_size, x*cell_size:(x+1)*cell_size] = 0
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
