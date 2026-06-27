
import tkinter as tk
from tkinter import messagebox

class GUICalculator:
    def __init__(self, master):
        self.master = master
        master.title("iOS風電卓")
        master.geometry("300x400")
        master.resizable(0, 0)
        master.configure(bg="black")

        self.expression = ""
        self.result_display = tk.StringVar()
        self.result_display.set("0")

        display_frame = tk.Frame(master, bg="black")
        display_frame.pack(expand=True, fill="both")

        display_label = tk.Label(display_frame, textvariable=self.result_display, anchor="e", bg="black", fg="white",
                                 font=("Helvetica Neue", 30), wraplength=280)
        display_label.pack(expand=True, fill="both", padx=10, pady=10)

        button_frame = tk.Frame(master, bg="black")
        button_frame.pack(expand=True, fill="both")

        buttons = [
            ["C", "±", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["0", ".", "=", ""], # Empty string for the last button to span two columns
        ]

        for r_idx, row_buttons in enumerate(buttons):
            for c_idx, button_text in enumerate(row_buttons):
                if button_text == "": # Special handling for the 0 button to span two columns
                    button = tk.Button(button_frame, text="0", padx=20, pady=20, font=("Helvetica Neue", 18), bg="#505050", fg="white", command=lambda: self.num_click("0"))
                    button.grid(row=r_idx, column=c_idx, columnspan=2, sticky="nsew", padx=2, pady=2)
                else:
                    if button_text in ["/", "*", "-", "+", "="]:
                        color = "#FF9500"
                        command = lambda b=button_text: self.op_click(b)
                    elif button_text == "C":
                        color = "#D4D4D2"
                        command = lambda: self.num_click("C")
                    elif button_text == "±":
                        color = "#D4D4D2"
                        command = self.negate_number
                    elif button_text == "%":
                        color = "#D4D4D2"
                        command = self.percentage
                    else:
                        color = "#505050"
                        command = lambda b=button_text: self.num_click(b)

                    button = tk.Button(button_frame, text=button_text, padx=20, pady=20, font=("Helvetica Neue", 18), bg=color, fg="white", command=command)
                    button.grid(row=r_idx, column=c_idx, sticky="nsew", padx=2, pady=2)

        for i in range(5): button_frame.grid_rowconfigure(i, weight=1)
        for i in range(4): button_frame.grid_columnconfigure(i, weight=1)

    def num_click(self, char):
        if char == "C":
            self.expression = ""
            self.result_display.set("0")
        elif char == ".":
            if self.expression and self.expression.split()[-1] == ".": # Ensure only one dot per number
                return
            if not self.expression or self.expression.split()[-1] in ["+", "-", "*", "/"]:
                self.expression += "0."
            else:
                self.expression += char
            self.result_display.set(self.expression.split()[-1])
        else:
            if self.result_display.get() == "0" and char != ".":
                self.expression = char
            else:
                self.expression += char
            self.result_display.set(self.expression)

    def op_click(self, char):
        if char == "=":
            try:
                result = str(eval(self.expression))
                self.result_display.set(result)
                self.expression = result
            except Exception as e:
                messagebox.showerror("エラー", "無効な入力です: " + str(e))
                self.expression = ""
                self.result_display.set("0")
        else:
            if self.expression and self.expression[-1] in ["+", "-", "*", "/"]:
                self.expression = self.expression[:-1] + char
            else:
                self.expression += " " + char + " "
            self.result_display.set(char)

    def negate_number(self):
        try:
            if self.expression and self.expression.split()[-1] not in ["+", "-", "*", "/"]:
                current_num = float(self.expression.split()[-1])
                negated_num = -current_num
                self.expression = " ".join(self.expression.split()[:-1]) + " " + str(negated_num)
                self.result_display.set(str(negated_num))
        except ValueError:
            pass

    def percentage(self):
        try:
            if self.expression and self.expression.split()[-1] not in ["+", "-", "*", "/"]:
                current_num = float(self.expression.split()[-1])
                percent_val = current_num / 100
                self.expression = " ".join(self.expression.split()[:-1]) + " " + str(percent_val)
                self.result_display.set(str(percent_val))
        except ValueError:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    my_gui = GUICalculator(root)
    root.mainloop()
