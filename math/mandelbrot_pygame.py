import concurrent.futures
import os
import queue
import threading

import numpy as np
import pygame


def compute_mandelbrot_chunk(xmin, xmax, ymin, ymax, width, height, max_iter, row_start, row_end, col_start, col_end):
    x = np.linspace(xmin, xmax, width, dtype=np.float64)[col_start:col_end]
    y = np.linspace(ymin, ymax, height, dtype=np.float64)[row_start:row_end]
    C = x[np.newaxis, :] + 1j * y[:, np.newaxis]
    Z = np.zeros_like(C, dtype=np.complex128)
    output = np.full(C.shape, max_iter, dtype=np.uint16)
    mask = np.ones(C.shape, dtype=bool)

    for i in range(max_iter):
        Z[mask] = Z[mask] * Z[mask] + C[mask]
        escaped = np.abs(Z) > 2
        output[escaped & mask] = i
        mask &= ~escaped
        if not mask.any():
            break

    return row_start, col_start, output


class MandelbrotPygame:
    def __init__(self, width=900, height=650, max_iter=200):
        pygame.init()
        self.width = width
        self.height = height
        self.max_iter = max_iter
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Mandelbrot Explorer (pygame)')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 20)

        self.xmin = -2.0
        self.xmax = 1.0
        self.ymin = -1.5
        self.ymax = 1.5

        self.dragging = False
        self.drag_start = None
        self.drag_end = None
        self.selection_rect = None

        self.render_surface = pygame.Surface((self.width, self.height))
        self.render_thread = None
        self.rendering = False
        self.progress = 0
        self.status = 'Ready'
        self._progress_lock = threading.Lock()
        self.chunk_queue = queue.Queue()
        self.mesh_rows = 8
        self.mesh_cols = 8

        self._start_render()
        self._main_loop()

    def _start_render(self):
        if self.rendering:
            return
        self.rendering = True
        self.status = 'Rendering...'
        self.progress = 0
        self.chunk_queue = queue.Queue()
        self.render_surface.fill((0, 0, 0))
        self.render_thread = threading.Thread(target=self._render_worker, daemon=True)
        self.render_thread.start()

    def _render_worker(self):
        num_threads = min(16, max(2, os.cpu_count() or 4))
        if num_threads % 2 != 0:
            num_threads -= 1
        mesh_rows = 8
        mesh_cols = 8
        row_height = self.height // mesh_rows
        col_width = self.width // mesh_cols

        chunk_ranges = []
        for row_index in range(mesh_rows):
            row_start = row_index * row_height
            row_end = self.height if row_index == mesh_rows - 1 else (row_start + row_height)
            for col_index in range(mesh_cols):
                col_start = col_index * col_width
                col_end = self.width if col_index == mesh_cols - 1 else (col_start + col_width)
                chunk_ranges.append((row_start, row_end, col_start, col_end))

        total = len(chunk_ranges)
        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(
                    compute_mandelbrot_chunk,
                    self.xmin,
                    self.xmax,
                    self.ymin,
                    self.ymax,
                    self.width,
                    self.height,
                    self.max_iter,
                    row_start,
                    row_end,
                    col_start,
                    col_end,
                )
                for row_start, row_end, col_start, col_end in chunk_ranges
            ]
            for future in concurrent.futures.as_completed(futures):
                row_start, col_start, chunk = future.result()
                self.chunk_queue.put((row_start, col_start, chunk))
                completed += 1
                self._update_progress(completed, total)

        self.chunk_queue.put(('done', None, None))

    def _update_progress(self, step, total):
        with self._progress_lock:
            self.progress = int(step / total * 100)

    def _draw_status(self):
        status_text = f'{self.status}'
        if self.rendering:
            with self._progress_lock:
                status_text += f' ({self.progress}%)'
        text_surface = self.font.render(status_text, True, (255, 255, 255))
        self.screen.blit(text_surface, (10, 10))

    def _draw_selection(self):
        if self.dragging and self.drag_start and self.drag_end:
            x0, y0 = self.drag_start
            x1, y1 = self.drag_end
            rect = pygame.Rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)

    def _draw_grid(self):
        line_color = (255, 255, 255)
        alpha = 64
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        row_height = self.height // self.mesh_rows
        col_width = self.width // self.mesh_cols
        for row_index in range(1, self.mesh_rows):
            y = row_index * row_height
            pygame.draw.line(overlay, (*line_color, alpha), (0, y), (self.width, y), 1)
        for col_index in range(1, self.mesh_cols):
            x = col_index * col_width
            pygame.draw.line(overlay, (*line_color, alpha), (x, 0), (x, self.height), 1)
        self.screen.blit(overlay, (0, 0))

    def _blit_chunk(self, iter_chunk, row_start, col_start):
        normalized = iter_chunk.astype(np.float32) / self.max_iter
        normalized = np.sqrt(normalized)
        colors = np.empty(iter_chunk.shape + (3,), dtype=np.uint8)
        colors[..., 0] = np.clip((np.sin(normalized * 3.0) * 0.5 + 0.5) * 255, 0, 255)
        colors[..., 1] = np.clip((np.sin(normalized * 4.0 + 2.0) * 0.5 + 0.5) * 255, 0, 255)
        colors[..., 2] = np.clip((np.sin(normalized * 5.0 + 4.0) * 0.5 + 0.5) * 255, 0, 255)
        colors[iter_chunk == self.max_iter] = (0, 0, 0)
        chunk_surface = pygame.surfarray.make_surface(np.transpose(colors, (1, 0, 2)))
        self.render_surface.blit(chunk_surface, (col_start, row_start))

    def _main_loop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self._reset_view()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.dragging = True
                        self.drag_start = event.pos
                        self.drag_end = event.pos
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        self.drag_end = event.pos
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.dragging:
                        self.dragging = False
                        self._apply_zoom_selection()

            while not self.chunk_queue.empty():
                row_start, col_start, chunk = self.chunk_queue.get()
                if row_start == 'done':
                    self.rendering = False
                    self.status = 'Done'
                else:
                    self._blit_chunk(chunk, row_start, col_start)

            self.screen.fill((0, 0, 0))
            self.screen.blit(self.render_surface, (0, 0))
            if self.rendering:
                self._draw_grid()
            self._draw_selection()
            self._draw_status()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def _apply_zoom_selection(self):
        if not self.drag_start or not self.drag_end:
            return

        x0, y0 = self.drag_start
        x1, y1 = self.drag_end
        if abs(x1 - x0) < 5 or abs(y1 - y0) < 5:
            self.drag_start = None
            self.drag_end = None
            return

        left = min(x0, x1)
        right = max(x0, x1)
        top = min(y0, y1)
        bottom = max(y0, y1)

        new_xmin = self.xmin + (left / self.width) * (self.xmax - self.xmin)
        new_xmax = self.xmin + (right / self.width) * (self.xmax - self.xmin)
        new_ymin = self.ymin + (top / self.height) * (self.ymax - self.ymin)
        new_ymax = self.ymin + (bottom / self.height) * (self.ymax - self.ymin)

        self.xmin, self.xmax = new_xmin, new_xmax
        self.ymin, self.ymax = new_ymin, new_ymax
        self.drag_start = None
        self.drag_end = None
        self._start_render()

    def _reset_view(self):
        self.xmin, self.xmax = -2.0, 1.0
        self.ymin, self.ymax = -1.5, 1.5
        self._start_render()


def main():
    MandelbrotPygame(width=900, height=650, max_iter=200)


if __name__ == '__main__':
    main()
