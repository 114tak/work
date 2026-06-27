
class Calculator:
    def add(self, x, y):
        return x + y

    def subtract(self, x, y):
        return x - y

    def multiply(self, x, y):
        return x * y

    def divide(self, x, y):
        if y == 0:
            raise ValueError("0で割ることはできません")
        return x / y

if __name__ == "__main__":
    calculator = Calculator()

    while True:
        print("\n操作を選択してください:")
        print("1. 足し算")
        print("2. 引き算")
        print("3. 掛け算")
        print("4. 割り算")
        print("5. 終了")

        choice = input("選択 (1/2/3/4/5): ")

        if choice == '5':
            print("電卓を終了します。")
            break

        try:
            num1 = float(input("最初の数値を入力してください: "))
            num2 = float(input("2番目の数値を入力してください: "))
        except ValueError:
            print("無効な入力です。数値を入力してください。")
            continue

        if choice == '1':
            print("結果:", calculator.add(num1, num2))
        elif choice == '2':
            print("結果:", calculator.subtract(num1, num2))
        elif choice == '3':
            print("結果:", calculator.multiply(num1, num2))
        elif choice == '4':
            try:
                print("結果:", calculator.divide(num1, num2))
            except ValueError as e:
                print(e)
        else:
            print("無効な選択です。1から5の間の数字を入力してください。")
