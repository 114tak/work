
import tkinter as tk
from tkinter import messagebox
import random
import math

class MonteCarloPiApp:
    def __init__(self, master):
        self.master = master
        master.title("モンテカルロ法による円周率計算")

        # 試行回数入力
        self.label_trials = tk.Label(master, text="試行回数:")
        self.label_trials.grid(row=0, column=0, padx=5, pady=5)

        self.entry_trials = tk.Entry(master)
        self.entry_trials.grid(row=0, column=1, padx=5, pady=5)
        self.entry_trials.insert(0, "10000") # デフォルト値

        # 計算開始ボタン
        self.calculate_button = tk.Button(master, text="計算開始", command=self.calculate_pi)
        self.calculate_button.grid(row=1, column=0, columnspan=2, pady=10)

        # 結果表示
        self.result_frame = tk.LabelFrame(master, text="計算結果")
        self.result_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.label_pi_estimate_text = tk.Label(self.result_frame, text="推定円周率:")
        self.label_pi_estimate_text.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.label_pi_estimate_value = tk.Label(self.result_frame, text="N/A")
        self.label_pi_estimate_value.grid(row=0, column=1, padx=5, pady=2, sticky="w")

        self.label_inside_circle_text = tk.Label(self.result_frame, text="円内点数:")
        self.label_inside_circle_text.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.label_inside_circle_value = tk.Label(self.result_frame, text="N/A")
        self.label_inside_circle_value.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        self.label_total_points_text = tk.Label(self.result_frame, text="総点数:")
        self.label_total_points_text.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.label_total_points_value = tk.Label(self.result_frame, text="N/A")
        self.label_total_points_value.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        # キャンバス (後で実装)
        self.canvas = tk.Canvas(master, width=600, height=600, bg="white")
        self.canvas.grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        self.draw_circle_on_canvas()

    def draw_circle_on_canvas(self):
        # 正方形の範囲を (-1, -1) から (1, 1) とすると、キャンバスの中央が (0, 0)
        # キャンバスのサイズを600x600とした場合、中心は (300, 300)
        # 半径1の円を描画するために、キャンバス上では 半径=300 とする
        center_x, center_y = 300, 300
        radius = 300
        self.canvas.create_oval(center_x - radius, center_y - radius,
                                center_x + radius, center_y + radius,
                                outline="blue", width=2)
        # 正方形の境界線
        self.canvas.create_rectangle(center_x - radius, center_y - radius,
                                     center_x + radius, center_y + radius,
                                     outline="red")


    def calculate_pi(self):
        try:
            num_trials = int(self.entry_trials.get())
            if num_trials <= 0:
                messagebox.showerror("入力エラー", "試行回数は正の整数を入力してください。")
                return
        except ValueError:
            messagebox.showerror("入力エラー", "試行回数には数値を入力してください。")
            return

        points_inside_circle = 0
        self.canvas.delete("points") # 前回の点をクリア

        for _ in range(num_trials):
            x = random.uniform(-1, 1)
            y = random.uniform(-1, 1)

            distance = x**2 + y**2
            
            canvas_x = (x + 1) * 300 # -1から1の範囲を0から600にマッピング
            canvas_y = (1 - y) * 300 # y軸は反転させる (Tkinterの座標系は上が0)

            if distance <= 1:
                points_inside_circle += 1
                self.canvas.create_oval(canvas_x - 1, canvas_y - 1, canvas_x + 1, canvas_y + 1, fill="green", outline="green", tags="points")
            else:
                self.canvas.create_oval(canvas_x - 1, canvas_y - 1, canvas_x + 1, canvas_y + 1, fill="red", outline="red", tags="points")

        pi_estimate = 4 * (points_inside_circle / num_trials)

        self.label_pi_estimate_value.config(text=f"{pi_estimate:.6f}")
        self.label_inside_circle_value.config(text=str(points_inside_circle))
        self.label_total_points_value.config(text=str(num_trials))

root = tk.Tk()
app = MonteCarloPiApp(root)
root.mainloop()
