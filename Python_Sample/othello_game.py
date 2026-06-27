
import tkinter as tk
from tkinter import messagebox
import math

class OthelloGame:
    def __init__(self, master):
        self.master = master
        self.master.title("オセロゲーム")
        self.board = self.create_initial_board()
        self.current_player = "black"
        self.canvases = [] # ボタンの代わりにCanvasを使用
        self.create_widgets()
        self.update_board_display()

    def create_initial_board(self):
        board = [["empty" for _ in range(8)] for _ in range(8)]
        board[3][3] = "white"
        board[3][4] = "black"
        board[4][3] = "black"
        board[4][4] = "white"
        return board

    def create_widgets(self):
        self.score_label = tk.Label(self.master, text="黒: 2 白: 2", font=("Arial", 16))
        self.score_label.pack()

        self.turn_label = tk.Label(self.master, text="現在のターン: 黒", font=("Arial", 16))
        self.turn_label.pack()

        self.game_frame = tk.Frame(self.master)
        self.game_frame.pack()

        for r in range(8):
            row_canvases = []
            for c in range(8):
                canvas = tk.Canvas(self.game_frame, width=60, height=60, bg="#006400", highlightbackground="gray", highlightthickness=1) # 盤面の色を濃い緑に
                canvas.grid(row=r, column=c, padx=1, pady=1)
                canvas.bind("<Button-1>", lambda event, r=r, c=c: self.on_canvas_click(r, c))
                row_canvases.append(canvas)
            self.canvases.append(row_canvases)

    def on_canvas_click(self, r, c):
        self.on_button_click(r, c) # 既存のロジックを再利用

    def update_board_display(self):
        black_count = 0
        white_count = 0
        for r in range(8):
            for c in range(8):
                self.canvases[r][c].delete("all") # 既存の描画をクリア
                piece = self.board[r][c]
                if piece == "black":
                    self.canvases[r][c].create_oval(5, 5, 55, 55, fill="black", outline="black") # 駒を大きく描画
                    black_count += 1
                elif piece == "white":
                    self.canvases[r][c].create_oval(5, 5, 55, 55, fill="white", outline="white") # 駒を大きく描画
                    white_count += 1
                else:
                    if self.is_valid_move(r, c):
                        # 円で星を描画
                        center_x, center_y = 30, 30
                        radius = 15
                        points = []
                        for i in range(5):
                            angle = i * (2 * 3.14159 / 5) - (3.14159 / 2) #上向きの星
                            x = center_x + radius * 0.9 * (1.5 if i % 2 == 0 else 0.5) * (1.5 if i % 2 == 0 else 0.5) * math.cos(angle)
                            y = center_y + radius * 0.9 * (1.5 if i % 2 == 0 else 0.5) * (1.5 if i % 2 == 0 else 0.5) * math.sin(angle)
                            points.append(x)
                            points.append(y)
                        self.canvases[r][c].create_polygon(points, fill="blue", outline="blue") # 星形

        self.score_label.config(text=f"黒: {black_count} 白: {white_count}")
        self.turn_label.config(text=f"現在のターン: { "黒" if self.current_player == "black" else "白"}")

    def on_button_click(self, r, c):
        if self.is_valid_move(r, c):
            self.make_move(r, c)
            self.current_player = self.get_opponent(self.current_player)
            self.handle_turn_change()
        else:
            self.show_invalid_move_error()

    def handle_turn_change(self):
        if not self.has_valid_moves("black") and not self.has_valid_moves("white"):
            self.end_game()
        elif not self.has_valid_moves(self.current_player):
            messagebox.showinfo("オセロ", f"{ "黒" if self.current_player == "black" else "白"} は置ける場所がないためスキップします")
            self.current_player = self.get_opponent(self.current_player)
            self.handle_turn_change() # スキップ後も再度チェック
        self.update_board_display()

    def show_invalid_move_error(self):
        messagebox.showerror("オセロ", "無効な手です。")

    def is_valid_move(self, r, c):
        if self.board[r][c] != "empty":
            return False

        # Check all 8 directions
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                if self.check_direction(r, c, dr, dc):
                    return True
        return False

    def check_direction(self, r, c, dr, dc):
        player = self.current_player
        opponent = self.get_opponent(player)

        i, j = r + dr, c + dc
        found_opponent = False

        while 0 <= i < 8 and 0 <= j < 8:
            if self.board[i][j] == opponent:
                found_opponent = True
            elif self.board[i][j] == player and found_opponent:
                return True
            else:
                break
            i, j = i + dr, j + dc
        return False

    def make_move(self, r, c):
        player = self.current_player
        opponent = self.get_opponent(player)
        self.board[r][c] = player

        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                if self.check_direction(r, c, dr, dc):
                    self.flip_pieces(r, c, dr, dc)

    def flip_pieces(self, r, c, dr, dc):
        player = self.current_player
        opponent = self.get_opponent(player)
        
        i, j = r + dr, c + dc
        pieces_to_flip = []
        while 0 <= i < 8 and 0 <= j < 8 and self.board[i][j] == opponent:
            pieces_to_flip.append((i, j))
            i, j = i + dr, j + dc
        
        if 0 <= i < 8 and 0 <= j < 8 and self.board[i][j] == player:
            for piece_r, piece_c in pieces_to_flip:
                self.animate_flip(piece_r, piece_c, player) # アニメーションを追加
                self.board[piece_r][piece_c] = player

    def animate_flip(self, r, c, new_player):
        # アニメーションのステップ数
        steps = 5
        # アニメーションの遅延（ミリ秒）
        delay = 50
        
        original_color = self.canvases[r][c].itemcget(self.canvases[r][c].find_all()[0], "fill")
        target_color = "black" if new_player == "black" else "white"

        for step in range(steps + 1):
            # 中間色を計算
            if new_player == "black":
                # 白から黒へ
                color_val = int(255 * (steps - step) / steps)
                color = f"#{color_val:02x}{color_val:02x}{color_val:02x}"
            else:
                # 黒から白へ
                color_val = int(255 * step / steps)
                color = f"#{color_val:02x}{color_val:02x}{color_val:02x}"
            
            self.canvases[r][c].delete("all")
            self.canvases[r][c].create_oval(5, 5, 55, 55, fill=color, outline=color)
            self.master.update_idletasks()
            self.master.after(delay)
        
        # 最終的な色を設定
        self.canvases[r][c].delete("all")
        self.canvases[r][c].create_oval(5, 5, 55, 55, fill=target_color, outline=target_color)


    def get_opponent(self, player):
        return "white" if player == "black" else "black"

    def has_valid_moves(self, player):
        original_player = self.current_player
        self.current_player = player # Temporarily set current player to check for valid moves
        for r in range(8):
            for c in range(8):
                if self.is_valid_move(r, c):
                    self.current_player = original_player # Restore original player
                    return True
        self.current_player = original_player # Restore original player
        return False

    def end_game(self):
        black_count = sum(row.count("black") for row in self.board)
        white_count = sum(row.count("white") for row in self.board)
        
        winner = ""
        if black_count > white_count:
            winner = "黒の勝ち！"
        elif white_count > black_count:
            winner = "白の勝ち！"
        else:
            winner = "引き分け！"
            
        messagebox.showinfo("ゲーム終了", f"ゲーム終了！\n黒: {black_count} 白: {white_count}\n{winner}")
        self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    game = OthelloGame(root)
    root.mainloop()

    def get_opponent(self, player):
        return "white" if player == "black" else "black"

    def has_valid_moves(self, player):
        original_player = self.current_player
        self.current_player = player # Temporarily set current player to check for valid moves
        for r in range(8):
            for c in range(8):
                if self.is_valid_move(r, c):
                    self.current_player = original_player # Restore original player
                    return True
        self.current_player = original_player # Restore original player
        return False

    def end_game(self):
        black_count = sum(row.count("black") for row in self.board)
        white_count = sum(row.count("white") for row in self.board)
        
        winner = ""
        if black_count > white_count:
            winner = "黒の勝ち！"
        elif white_count > black_count:
            winner = "白の勝ち！"
        else:
            winner = "引き分け！"
            
        messagebox.showinfo("ゲーム終了", f"ゲーム終了！\n黒: {black_count} 白: {white_count}\n{winner}")
        self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    game = OthelloGame(root)
    root.mainloop()
