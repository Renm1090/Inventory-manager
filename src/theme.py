import flet as ft
import os

def get_theme_colors(page: ft.Page):
    is_light = page.theme_mode == ft.ThemeMode.LIGHT
    return {
        "bg": "#f8fafc" if is_light else "#0f172a",
        "card_bg": ft.Colors.WHITE if is_light else "#1e293b",
        "text_main": "#0f172a" if is_light else ft.Colors.WHITE,
        "text_sub": ft.Colors.BLUE_GREY_600 if is_light else ft.Colors.BLUE_GREY_300,
        "divider": ft.Colors.BLUE_GREY_100 if is_light else ft.Colors.BLUE_GREY_800,
        "input_bg": ft.Colors.BLUE_GREY_50 if is_light else ft.Colors.BLUE_GREY_900,
        "text_button": ft.Colors.BLUE_700 if is_light else ft.Colors.BLUE_300,
        "nav_bg": ft.Colors.BLUE_GREY_100 if is_light else ft.Colors.BLUE_GREY_900,
        "border": ft.Colors.BLUE_GREY_200 if is_light else ft.Colors.BLUE_GREY_700,
        "badge_bg": ft.Colors.TEAL_50 if is_light else ft.Colors.with_opacity(0.1, ft.Colors.TEAL),
        "badge_border": ft.Colors.TEAL_200 if is_light else ft.Colors.TEAL_700,
        "badge_text": ft.Colors.TEAL_700 if is_light else ft.Colors.TEAL_300,
        "danger_bg": ft.Colors.RED_50 if is_light else ft.Colors.with_opacity(0.1, ft.Colors.RED),
        "danger_border": ft.Colors.RED_200 if is_light else ft.Colors.RED_700,
        "danger_text": ft.Colors.RED_700 if is_light else ft.Colors.RED_300,
    }

def border_all(width: float, color: str):
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, bottom=side, left=side, right=side)

def get_download_directory(page: ft.Page, filename: str):
    """
    Retorna la ruta predeterminada para escritorio, 
    o None si estamos en móvil (para activar FilePicker).
    """
    # Si detectamos que no es un entorno móvil (Linux, Windows, MacOS)
    if page.platform in [ft.PagePlatform.LINUX, ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS]:
        download_dir = os.path.expanduser("~/Downloads")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        return os.path.join(download_dir, filename)
    
    # En móvil, devolvemos None para que la vista sepa que debe usar el FilePicker
    return None

