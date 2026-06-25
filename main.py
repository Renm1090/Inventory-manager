import flet as ft
from src.ui import main
from src.database import init_db

if __name__ == "__main__":
    init_db()
    ft.run(main)

