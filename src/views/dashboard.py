import flet as ft
from src.database import get_dashboard_stats, get_weekly_activity
from src.theme import get_theme_colors, border_all

def dashboard_view(page: ft.Page):
    colors = get_theme_colors(page)
    stats = get_dashboard_stats()
    
    # --- Definición de gradientes premium ---
    gradient_articles = ft.LinearGradient([ft.Colors.BLUE_800, ft.Colors.TEAL_400])
    gradient_critical = ft.LinearGradient([ft.Colors.RED_800, ft.Colors.ORANGE_500])
    gradient_movement = ft.LinearGradient([ft.Colors.PURPLE_800, ft.Colors.DEEP_PURPLE_400])

    # --- Tarjetas ---
    card_total_articles = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, color=ft.Colors.WHITE, size=28),
            ft.Text("Total de Artículos", size=13, color=ft.Colors.WHITE70),
            ft.Text(str(stats.get('total', 0)), size=24, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        ], spacing=4),
        gradient=gradient_articles, 
        padding=12, 
        border_radius=16, 
        expand=1,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))
    )

    card_critical_stock = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.WHITE, size=28),
            ft.Text("Stock Crítico", size=13, color=ft.Colors.WHITE70),
            ft.Text(str(stats.get('criticos', 0)), size=24, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        ], spacing=4),
        gradient=gradient_critical, 
        padding=12, 
        border_radius=16, 
        expand=1,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))
    )

    ultimo = stats.get('ultimo', ('Sin movimientos', 'N/A'))    
    card_last_movement = ft.Container(
        content=ft.Column([
            ft.Text("Último Movimiento", size=12, color=ft.Colors.WHITE70),
            ft.Row([
                ft.Icon(ft.Icons.SWAP_HORIZ_ROUNDED, color=ft.Colors.WHITE, size=20),
                ft.Text(f"{ultimo[0]}", size=15, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS),
            ], spacing=6),
            ft.Text(f"Acción: {ultimo[1]}", size=10, color=ft.Colors.WHITE70)
        ], spacing=4),
        gradient=gradient_movement, 
        padding=12, 
        border_radius=16,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=6, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK))
    )

    # --- Gráfica Dinámica Escalar ---
    semana = get_weekly_activity()
    chart_columns = []
    
    # Calcular el valor máximo real de movimientos para escalar el gráfico de forma dinámica
    max_val = max(10, max((day["entradas"] for day in semana), default=0), max((day["salidas"] for day in semana), default=0))
    
    for day in semana:
        h_entradas = max(6, int((day["entradas"] / max_val) * 100))
        h_salidas = max(6, int((day["salidas"] / max_val) * 100))
        
        chart_columns.append(
            ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=8, height=h_entradas, bgcolor=ft.Colors.TEAL_400, border_radius=4),
                        ft.Container(width=8, height=h_salidas, bgcolor=ft.Colors.ORANGE_400, border_radius=4),
                    ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.END),
                    height=110, alignment=ft.Alignment.BOTTOM_CENTER
                ),
                ft.Text(day["dia"], size=10, color=colors["text_sub"], weight=ft.FontWeight.BOLD)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
        )

    chart_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Actividad Semanal", size=15, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
                ft.Row([
                    ft.Container(width=8, height=8, bgcolor=ft.Colors.TEAL_400, border_radius=2),
                    ft.Text("Entradas", size=9, color=colors["text_sub"]),
                    ft.Container(width=8, height=8, bgcolor=ft.Colors.ORANGE_400, border_radius=2),
                    ft.Text("Salidas", size=9, color=colors["text_sub"]),
                ], spacing=6)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=4),
            ft.Container(
                content=ft.Row(controls=chart_columns, alignment=ft.MainAxisAlignment.SPACE_AROUND, vertical_alignment=ft.CrossAxisAlignment.END), 
                padding=2
            )
        ]),
        bgcolor=colors["card_bg"], 
        padding=14, 
        border_radius=20,
        border=border_all(1, colors["border"]),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK))
    )

    # --- Vista Final ---
    return ft.Column([
        ft.Row([
            ft.Text("Inicio", size=24, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            ft.IconButton(
                icon=ft.Icons.NOTIFICATIONS_NONE_ROUNDED, 
                icon_color=colors["text_main"],
                on_click=lambda _: page.show_dialog(
                    ft.SnackBar(content=ft.Text("No hay notificaciones nuevas."), bgcolor=ft.Colors.BLUE_GREY_700)
                )
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.ResponsiveRow([card_total_articles, card_critical_stock], spacing=12),
        card_last_movement,
        chart_card
    ], spacing=14, scroll=ft.ScrollMode.ADAPTIVE, alignment=ft.MainAxisAlignment.START, key=f"dashboard_view_{page.theme_mode}")