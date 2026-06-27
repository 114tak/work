import concurrent.futures
import os
import threading

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle



def _mandelbrot_chunk(xmin, xmax, ymin, ymax, width, height, max_iter, row_start, row_end):
    real = np.linspace(xmin, xmax, width)
    imag = np.linspace(ymin, ymax, height)
    c = real[np.newaxis, :] + 1j * imag[row_start:row_end, np.newaxis]

    z = np.zeros_like(c)
    div_time = np.full(c.shape, max_iter, dtype=int)
    mask = np.ones(c.shape, dtype=bool)

    for i in range(max_iter):
        z[mask] = z[mask] * z[mask] + c[mask]
        escaped = np.abs(z) > 2
        newly_escaped = escaped & mask
        div_time[newly_escaped] = i
        mask &= ~escaped
        if not mask.any():
            break

    return row_start, div_time


def create_mandelbrot(xmin, xmax, ymin, ymax, width, height, max_iter, progress_callback=None):
    num_threads = min(8, max(1, os.cpu_count() or 4))
    rows_per_chunk = max(1, height // num_threads)
    chunks = []

    for row_start in range(0, height, rows_per_chunk):
        row_end = min(height, row_start + rows_per_chunk)
        chunks.append((xmin, xmax, ymin, ymax, width, height, max_iter, row_start, row_end))

    mandelbrot_set = np.empty((height, width), dtype=int)
    total_chunks = len(chunks)
    completed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(_mandelbrot_chunk, *chunk) for chunk in chunks]
        for future in concurrent.futures.as_completed(futures):
            row_start, result = future.result()
            mandelbrot_set[row_start:row_start + result.shape[0], :] = result
            completed += 1
            if progress_callback is not None:
                progress_callback(completed, total_chunks)

    return mandelbrot_set


class MandelbrotExplorer:
    def __init__(self, xmin=-2.0, xmax=1.0, ymin=-1.5, ymax=1.5, width=800, height=600, max_iter=100):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.width = width
        self.height = height
        self.max_iter = max_iter

        self.press_event = None
        self.rect_patch = None
        self.colorbar = None

        self.fig, self.ax = plt.subplots(figsize=(10, 7.5))
        self.fig.subplots_adjust(bottom=0.14)
        self.image = None
        self.status_text = None
        self.progress_bar_bg = None
        self.progress_bar_fg = None
        self.toolbar_connected = False
        self._render_thread = None
        self._rendering = False

        self._connect_events()
        self.fig.canvas.mpl_connect('draw_event', self._connect_toolbar_home)
        self._connect_toolbar_home()
        self.redraw(initial=True)
        plt.show()

    def _connect_events(self):
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

    def _connect_toolbar_home(self, event=None):
        toolbar = getattr(self.fig.canvas.manager, 'toolbar', None)
        if toolbar is None:
            return

        if hasattr(toolbar, '_buttons') and 'Home' in toolbar._buttons:
            try:
                toolbar._buttons['Home'].configure(command=self.reset_view)
            except Exception:
                pass

        if hasattr(toolbar, 'home'):
            try:
                toolbar.home = self.reset_view
            except Exception:
                pass

    def redraw(self, initial=False):
        if self._rendering:
            return

        if self.image is None or initial:
            self.ax.clear()
            self.colorbar = None
            self.status_text = self.ax.text(
                0.01, 0.01, 'Rendering...',
                transform=self.ax.transAxes,
                color='white', fontsize=10,
                va='bottom', ha='left',
                bbox=dict(facecolor='black', alpha=0.6, pad=0.3)
            )
            self.progress_bar_bg = Rectangle((0.01, 0.04), 0.3, 0.02,
                                            transform=self.ax.transAxes,
                                            color='white', alpha=0.4)
            self.progress_bar_fg = Rectangle((0.01, 0.04), 0.0, 0.02,
                                            transform=self.ax.transAxes,
                                            color='lime', alpha=0.9)
            self.ax.add_patch(self.progress_bar_bg)
            self.ax.add_patch(self.progress_bar_fg)
        else:
            self._set_status('Rendering...')
            self._set_progress(0, 1)

        self.fig.canvas.draw_idle()
        self._rendering = True
        self._render_thread = threading.Thread(target=self._render_background, args=(initial,), daemon=True)
        self._render_thread.start()

    def _call_in_gui(self, func):
        manager = getattr(self.fig.canvas, 'manager', None)
        if manager is not None and hasattr(manager, 'window') and hasattr(manager.window, 'after'):
            manager.window.after(0, func)
        else:
            timer = self.fig.canvas.new_timer(interval=1)
            timer.add_callback(func)
            timer.start()

    def _render_background(self, initial):
        mandelbrot_set = create_mandelbrot(
            self.xmin, self.xmax, self.ymin, self.ymax,
            self.width, self.height, self.max_iter,
            progress_callback=self._update_progress
        )
        self._call_in_gui(lambda: self._finish_render(mandelbrot_set, initial))

    def _finish_render(self, mandelbrot_set, initial):
        self._rendering = False
        if self.image is None or initial:
            self.image = self.ax.imshow(
                mandelbrot_set,
                extent=[self.xmin, self.xmax, self.ymin, self.ymax],
                cmap='inferno',
                origin='lower',
                interpolation='nearest'
            )
            self.colorbar = self.ax.figure.colorbar(self.image, ax=self.ax, label='Iteration count')
            self.ax.set_title('Mandelbrot Set')
            self.ax.set_xlabel('Real axis')
            self.ax.set_ylabel('Imaginary axis')
        else:
            self.image.set_data(mandelbrot_set)
            self.image.set_extent([self.xmin, self.xmax, self.ymin, self.ymax])
            self.image.set_clim(0, self.max_iter)
            self.ax.set_xlim(self.xmin, self.xmax)
            self.ax.set_ylim(self.ymin, self.ymax)

        self._set_status('Done')
        self._set_progress(1, 1)
        self.fig.canvas.draw_idle()

    def _set_status(self, text):
        if self.status_text is not None:
            self.status_text.set_text(text)

    def _set_progress(self, completed, total):
        if self.progress_bar_fg is None:
            return
        width = 0.3 * (completed / total) if total else 0.0
        self.progress_bar_fg.set_width(width)

    def _update_progress(self, completed, total):
        self._call_in_gui(lambda: self._update_progress_gui(completed, total))

    def _update_progress_gui(self, completed, total):
        self._set_status(f'Rendering... {completed}/{total} chunks')
        self._set_progress(completed, total)
        self.fig.canvas.draw_idle()

    def on_press(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        self.press_event = event
        if self.rect_patch is None:
            self.rect_patch = Rectangle((event.xdata, event.ydata), 0, 0,
                                        linewidth=1.2, edgecolor='white', facecolor='none', linestyle='--')
            self.ax.add_patch(self.rect_patch)

    def on_motion(self, event):
        if self.press_event is None or event.inaxes != self.ax:
            return
        x0, y0 = self.press_event.xdata, self.press_event.ydata
        x1, y1 = event.xdata, event.ydata
        if x0 is None or y0 is None or x1 is None or y1 is None:
            return
        self.rect_patch.set_bounds(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
        self.fig.canvas.draw_idle()

    def on_release(self, event):
        if self.press_event is None or event.inaxes != self.ax or event.button != 1:
            self._clear_rectangle()
            return

        x0, y0 = self.press_event.xdata, self.press_event.ydata
        x1, y1 = event.xdata, event.ydata
        self.press_event = None

        if x0 is None or y0 is None or x1 is None or y1 is None:
            self._clear_rectangle()
            return

        if abs(x1 - x0) < 1e-6 or abs(y1 - y0) < 1e-6:
            self._clear_rectangle()
            return

        self.xmin, self.xmax = sorted([x0, x1])
        self.ymin, self.ymax = sorted([y0, y1])
        self.redraw()
        self._clear_rectangle()

    def on_key(self, event):
        if event.key == 'r':
            self.reset_view()

    def zoom(self, center_x, center_y, scale=0.5):
        width = (self.xmax - self.xmin) * scale
        height = (self.ymax - self.ymin) * scale
        self.xmin = center_x - width / 2
        self.xmax = center_x + width / 2
        self.ymin = center_y - height / 2
        self.ymax = center_y + height / 2
        self.redraw()

    def reset_view(self):
        self.xmin, self.xmax = -2.0, 1.0
        self.ymin, self.ymax = -1.5, 1.5
        self.redraw()

    def _clear_rectangle(self):
        if self.rect_patch is not None:
            self.rect_patch.remove()
            self.rect_patch = None
            self.fig.canvas.draw_idle()


def main():
    MandelbrotExplorer(width=900, height=650, max_iter=150)


if __name__ == '__main__':
    main()
