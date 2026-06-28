import concurrent.futures
import os
import threading
import time
import tkinter as tk
import tkinter.messagebox as messagebox
import numpy as np
from PIL import Image, ImageTk


def _compute_mandelbrot_tile(x_min, x_max, y_min, y_max, width, height, max_iter, x_start, x_end, y_start, y_end):
    real = np.linspace(x_min, x_max, width, dtype=np.float64)[x_start:x_end]
    imag = np.linspace(y_min, y_max, height, dtype=np.float64)[y_start:y_end]
    c = real[np.newaxis, :] + imag[:, np.newaxis] * 1j

    z = np.zeros_like(c)
    div_time = np.full(c.shape, max_iter, dtype=np.int32)
    mask = np.ones(c.shape, dtype=bool)

    for i in range(max_iter):
        z[mask] = z[mask] * z[mask] + c[mask]
        escaped = np.abs(z) > 2
        newly_escaped = escaped & mask
        div_time[newly_escaped] = i
        mask &= ~escaped
        if not mask.any():
            break

    return x_start, y_start, div_time


class MandelbrotApp:
    def __init__(self, master):
        self.master = master
        master.title("Mandelbrot Viewer")

        self.width = 800
        self.height = 800
        self.max_iter = 100

        self.x_min, self.x_max = -2.0, 1.0
        self.y_min, self.y_max = -1.5, 1.5

        self.canvas = tk.Canvas(master, width=self.width, height=self.height, bg="black")
        self.canvas.pack()

        top_frame = tk.Frame(master)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        reset_button = tk.Button(top_frame, text="🏠", command=self.reset_view)
        reset_button.pack(side=tk.LEFT, padx=(0, 10))

        max_cpus = max(1, os.cpu_count() or 1)
        self.thread_count_var = tk.IntVar(value=max_cpus)
        tk.Label(top_frame, text="スレッド数:", fg="black", font=("Arial", 10)).pack(side=tk.LEFT)
        self.thread_spinbox = tk.Spinbox(top_frame, from_=1, to=max_cpus, width=4, textvariable=self.thread_count_var, state="readonly")
        self.thread_spinbox.pack(side=tk.LEFT, padx=(0, 10))

        self.benchmark_button = tk.Button(top_frame, text="ベンチ", command=self.start_benchmark)
        self.benchmark_button.pack(side=tk.LEFT, padx=(0, 10))

        self.thread_label = tk.Label(top_frame, text=f"使用スレッド: {self.thread_count_var.get()}", fg="black", font=("Arial", 10))
        self.thread_label.pack(side=tk.LEFT, padx=(0, 10))

        self.time_label = tk.Label(top_frame, text="処理時間: --", fg="black", font=("Arial", 10))
        self.time_label.pack(side=tk.LEFT)

        self.benchmark_label = tk.Label(top_frame, text="ベンチ結果: --", fg="black", font=("Arial", 10))
        self.benchmark_label.pack(side=tk.LEFT, padx=(10, 0))

        # Bind 'r' key to reset
        self.master.bind('r', self.reset_view)

        # Mouse events for zooming
        self.canvas.bind("<Button-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        self.start_x = None
        self.start_y = None
        self.rect_id = None

        self.drawing_text_id = None
        self.progress_bar_bg = None
        self.progress_bar_fg = None
        self.progress_text_id = None
        self.start_time = None

        self.draw_mandelbrot()

    def reset_view(self, event=None):
        self.x_min, self.x_max = -2.0, 1.0
        self.y_min, self.y_max = -1.5, 1.5
        self.draw_mandelbrot()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = None

    def _aspect_corrected_coords(self, x0, y0, x1, y1):
        dx = x1 - x0
        dy = y1 - y0
        if dx == 0 or dy == 0:
            return x1, y1

        aspect = self.width / self.height
        if abs(dx) > abs(dy) * aspect:
            dx = np.sign(dx) * abs(dy) * aspect
        else:
            dy = np.sign(dy) * abs(dx) / aspect

        return int(x0 + dx), int(y0 + dy)

    def on_mouse_drag(self, event):
        cur_x, cur_y = self._aspect_corrected_coords(self.start_x, self.start_y, event.x, event.y)
        cur_x = max(0, min(self.width, cur_x))
        cur_y = max(0, min(self.height, cur_y))

        if not self.rect_id:
            self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline="white", dash=(2,2))
        else:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x, end_y = self._aspect_corrected_coords(self.start_x, self.start_y, event.x, event.y)
        end_x = max(0, min(self.width, end_x))
        end_y = max(0, min(self.height, end_y))

        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

        # Ensure the selection is valid and has some size
        if abs(end_x - self.start_x) < 2 or abs(end_y - self.start_y) < 2:
            return
        
        # Calculate new min/max values based on selection
        new_x_min = self.x_min + (min(self.start_x, end_x) / self.width) * (self.x_max - self.x_min)
        new_x_max = self.x_min + (max(self.start_x, end_x) / self.width) * (self.x_max - self.x_min)
        new_y_min = self.y_min + (min(self.start_y, end_y) / self.height) * (self.y_max - self.y_min)
        new_y_max = self.y_min + (max(self.start_y, end_y) / self.height) * (self.y_max - self.y_min)

        self.x_min, self.x_max = new_x_min, new_x_max
        self.y_min, self.y_max = new_y_min, new_y_max

        self.draw_mandelbrot()

    def _clear_progress_ui(self):
        for attr in ("drawing_text_id", "progress_bar_bg", "progress_bar_fg", "progress_text_id"):
            item_id = getattr(self, attr)
            if item_id is not None:
                self.canvas.delete(item_id)
                setattr(self, attr, None)

    def _update_progress(self, completed, total, elapsed, finished=False):
        if self.progress_bar_bg is None or self.progress_bar_fg is None or self.progress_text_id is None:
            return

        width = self.width - 300
        bar_top = self.height - 60
        bar_bottom = self.height - 40
        fill_width = int(150 + width * (completed / total))
        self.canvas.coords(self.progress_bar_fg, 150, bar_top, fill_width, bar_bottom)

        percent = completed / total * 100
        text = f"進捗 {completed}/{total} ({percent:.1f}%)  {elapsed:.1f}s"
        self.canvas.itemconfig(self.progress_text_id, text=text)

        if finished and self.drawing_text_id is not None:
            self.canvas.itemconfig(self.drawing_text_id, text=f"描画完了 ({elapsed:.2f}s)")

    def mandelbrot(self, c):
        z = 0
        n = 0
        while abs(z) <= 2 and n < self.max_iter:
            z = z*z + c
            n += 1
        return n

    def _draw_mandelbrot_background(self):
        tile_size = 128
        tile_width = max(1, (self.width + tile_size - 1) // tile_size)
        tile_height = max(1, (self.height + tile_size - 1) // tile_size)

        colors = np.empty((self.height, self.width, 3), dtype=np.uint8)
        tiles = []
        for ty in range(tile_height):
            y_start = ty * tile_size
            y_end = min(self.height, y_start + tile_size)
            for tx in range(tile_width):
                x_start = tx * tile_size
                x_end = min(self.width, x_start + tile_size)
                tiles.append((self.x_min, self.x_max, self.y_min, self.y_max, self.width, self.height, self.max_iter, x_start, x_end, y_start, y_end))

        total_tiles = len(tiles)
        selected_threads = max(1, min(self.thread_count_var.get(), total_tiles))
        self.master.after(0, self.thread_label.config, {"text": f"使用スレッド: {selected_threads}"})
        max_workers = selected_threads
        start_time = time.perf_counter()

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_compute_mandelbrot_tile, *tile) for tile in tiles]
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                x_start, y_start, div_time = future.result()
                tile_h, tile_w = div_time.shape
                tile_colors = np.empty((tile_h, tile_w, 3), dtype=np.uint8)
                tile_colors[..., 0] = (div_time % 8) * 32
                tile_colors[..., 1] = (div_time % 16) * 16
                tile_colors[..., 2] = (div_time % 32) * 8
                colors[y_start:y_start + tile_h, x_start:x_start + tile_w, :] = tile_colors

                completed += 1
                elapsed = time.perf_counter() - start_time
                self.master.after(0, self._update_progress, completed, total_tiles, elapsed)

        elapsed = time.perf_counter() - start_time
        self.last_elapsed = elapsed
        self.master.after(0, self._update_progress, total_tiles, total_tiles, elapsed, True)
        self.master.after(0, self._finish_draw, colors)

    def start_benchmark(self):
        if hasattr(self, '_benchmark_running') and self._benchmark_running:
            return
        self._benchmark_running = True
        threading.Thread(target=self._run_benchmark, daemon=True).start()

    def _run_benchmark(self):
        max_cpus = max(1, os.cpu_count() or 1)
        results = []
        original_threads = self.thread_count_var.get()
        for workers in range(1, max_cpus + 1):
            self.thread_count_var.set(workers)
            self.thread_label.config(text=f"使用スレッド: {workers}")
            start_time = time.perf_counter()
            self._compute_benchmark_once(workers)
            duration = time.perf_counter() - start_time
            results.append((workers, duration))

        self.thread_count_var.set(original_threads)
        self.thread_label.config(text=f"使用スレッド: {original_threads}")
        self._display_benchmark_results(results)
        self._benchmark_running = False

    def _compute_benchmark_once(self, workers):
        tile_size = 128
        tile_width = max(1, (self.width + tile_size - 1) // tile_size)
        tile_height = max(1, (self.height + tile_size - 1) // tile_size)

        tiles = []
        for ty in range(tile_height):
            y_start = ty * tile_size
            y_end = min(self.height, y_start + tile_size)
            for tx in range(tile_width):
                x_start = tx * tile_size
                x_end = min(self.width, x_start + tile_size)
                tiles.append((self.x_min, self.x_max, self.y_min, self.y_max, self.width, self.height, self.max_iter, x_start, x_end, y_start, y_end))

        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_compute_mandelbrot_tile, *tile) for tile in tiles]
            for future in concurrent.futures.as_completed(futures):
                future.result()

    def _display_benchmark_results(self, results):
        best_workers, best_time = min(results, key=lambda x: x[1])
        display_text = ", ".join([f"{w}:{t:.2f}s" for w, t in results])
        self.benchmark_label.config(text=f"最速: {best_workers}T {best_time:.2f}s")
        messagebox.showinfo("ベンチ結果", f"スレッド数ごとの実行時間:\n{display_text}\n\n最速: {best_workers}T {best_time:.2f}s")

    def _finish_draw(self, colors):
        image = Image.fromarray(colors, mode="RGB")
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        if self.drawing_text_id:
            self.canvas.delete(self.drawing_text_id)
            self.drawing_text_id = None

        if self.time_label is not None and hasattr(self, 'last_elapsed'):
            self.time_label.config(text=f"処理時間: {self.last_elapsed:.2f}秒")

    def draw_mandelbrot(self):
        self._clear_progress_ui()
        self.drawing_text_id = self.canvas.create_text(self.width/2, self.height/2 - 10, text="描画中...", fill="white", font=("Arial", 24))
        self.progress_bar_bg = self.canvas.create_rectangle(150, self.height - 60, self.width - 150, self.height - 40, fill="#444", outline="white")
        self.progress_bar_fg = self.canvas.create_rectangle(150, self.height - 60, 150, self.height - 40, fill="#00ff00", outline="")
        self.progress_text_id = self.canvas.create_text(self.width/2, self.height - 20, text="進捗 0/0 (0.0%) 0.0s", fill="white", font=("Arial", 12))
        self.thread_label.config(text=f"使用スレッド: {self.thread_count_var.get()}")
        self.time_label.config(text="処理時間: --")
        self.benchmark_label.config(text="ベンチ結果: --")
        self.master.update_idletasks()

        threading.Thread(target=self._draw_mandelbrot_background, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = MandelbrotApp(root)
    root.mainloop()
