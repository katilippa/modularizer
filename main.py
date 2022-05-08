from app import App
from database_connection import DatabaseConnection
from console_menu import ConsoleMenu


if __name__ == '__main__':
    database_connection = DatabaseConnection(database="CodeCompass", user='postgres', host='127.0.0.1', port='5432')
    app = App(database_connection)
    menu = ConsoleMenu(app.menu_options)