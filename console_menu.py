class ConsoleMenu:
    def __init__(self, options: list, title: str = "Options"):
        self.title = title
        self.options = options
        self.print_options()
        self.handle_response()

    def print_options(self) -> None:
        print(f"------------------ {self.title} ------------------")
        for i in range(0, len(self.options)):
            print("\t\t" + str(i+1) + ". " + self.options[i][0])
        i += 1
        print("\t\t" + str(i + 1) + ". " + "Exit")

    def get_selected_item(self) -> int:
        str_response = input("option: ")
        while not str_response.isdigit():
            print("Enter the number of an option")
            self.print_options()
            str_response = input("option: ")
        return int(str_response)

    def handle_response(self) -> None:
        item = self.get_selected_item()
        while item < 1 or item > len(self.options) + 1:
            print("Invalid option")
            self.print_options()
            self.get_selected_item()

        if item <= len(self.options):
            self.options[item-1][1]()
            self.print_options()
            self.handle_response()