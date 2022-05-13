import logging

from app import App
from user_interface.consolse import Console

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    ui = Console()
    app = App(ui)
