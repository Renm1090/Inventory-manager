import flet as ft
from src.views.dashboard import dashboard_view
from src.views.inventory import inventory_view
from src.views.movements import movements_view
from src.views.settings import settings_view
from src.theme import get_theme_colors

def main(page: ft.Page):
    save_file_dialog = ft.FilePicker()
    page.services.append(save_file_dialog)
    page.save_file_dialog = save_file_dialog
    page.title = "Gestor de Inventario"
    try:
        page.window.width = 410
        page.window.height = 800
        page.window.resizable = True
    except AttributeError:
        page.window_width = 410
        page.window_height = 800
        page.window_resizable = True

    # Estética y Temas
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.TEAL,
        use_material3=True,
    )
    
    # colores iniciales
    colors = get_theme_colors(page)
    page.bgcolor = colors["bg"]
    page.padding = 16
    page.vertical_alignment = ft.MainAxisAlignment.START

    contenidor = ft.Container(
        content=dashboard_view(page),
        expand=True,
        alignment=ft.Alignment.TOP_CENTER
    )

    # auxiliar para actualizar la vista activa :)
    def update_active_view(index):
        if index == 0:
            contenidor.content = dashboard_view(page)
        elif index == 1:
            contenidor.content = inventory_view(page)
        elif index == 2:
            contenidor.content = movements_view(page, save_file_dialog)
        elif index == 3:
            contenidor.content = settings_view(page)
        page.update()

    #  cambio de navegación
    def on_navigation_change(e):
        selected_index = e.control.selected_index
        update_active_view(selected_index)

    # Callback de cambio de tema global
    def toggle_theme(is_light: bool):
        page.theme_mode = ft.ThemeMode.LIGHT if is_light else ft.ThemeMode.DARK
        current_colors = get_theme_colors(page)
        page.bgcolor = current_colors["bg"]
        page.navigation_bar.bgcolor = current_colors["nav_bg"]
        page.navigation_bar.indicator_color = ft.Colors.with_opacity(0.15, ft.Colors.TEAL)
        update_active_view(page.navigation_bar.selected_index)
    page.toggle_theme = toggle_theme

    # Barra de navegación inferior 
    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_navigation_change,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.GRID_VIEW_ROUNDED, 
                selected_icon=ft.Icons.GRID_VIEW_ROUNDED, 
                label="Inicio"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.INVENTORY_2_OUTLINED, 
                selected_icon=ft.Icons.INVENTORY_2_ROUNDED, 
                label="Inventario"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SWAP_VERT_ROUNDED, 
                selected_icon=ft.Icons.SWAP_VERT_ROUNDED, 
                label="Movimientos"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icons.SETTINGS_OUTLINED, 
                selected_icon=ft.Icons.SETTINGS_ROUNDED, 
                label="Ajustes"
            )
        ],
        bgcolor=colors["nav_bg"],
        indicator_color=ft.Colors.with_opacity(0.2, ft.Colors.TEAL),
        height=70
    )

    page.add(contenidor)

if __name__ == "__main__":
    ft.run(main, port=8550, host="0.0.0.0")