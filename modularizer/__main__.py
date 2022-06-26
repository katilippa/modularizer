import logging
from modularizer.app import Modularizer
from modularizer.user_interface.console import Console

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.FATAL)
    ui = Console()
    app = Modularizer(ui)
