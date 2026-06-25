import flet as ft
from flet import FilePicker
import time
import os
from datetime import datetime
from fpdf import FPDF
from src.database import get_movements_data
from src.theme import get_theme_colors, border_all, get_download_directory

def safe_str(s):
    # FPDF2 por defecto con fuentes estándar soporta latin-1. Evita caídas de codificación unicode.
    return str(s).encode('latin-1', 'replace').decode('latin-1')

def movements_view(page: ft.Page, save_file_dialog: ft.FilePicker):
    colors = get_theme_colors(page)

    # Contenedores de las tablas
    entries_container = ft.Container()
    exits_container = ft.Container()

    # Buscador de historial
    search_query = ""

    # Función para exportar a PDF con animación
    async def export_to_pdf(table_name):
        fresh_movements = get_movements_data()
        data_to_export = [m for m in fresh_movements if m['tipo'] == ('Entrada' if table_name == "Entradas" else 'Salida')]
        
        if not data_to_export:
            page.show_dialog(ft.SnackBar(content=ft.Text(f"No hay registros de {table_name.lower()}.")))
            return

        # Abrimos el selector de archivos
        try:
            path = await save_file_dialog.save_file(
                file_name=f"{table_name}_reporte.pdf",
                allowed_extensions=["pdf"]
            )
            if path:
                # Generamos el PDF directamente en la ruta elegida por el usuario
                generate_pdf(data_to_export, table_name, path)
                page.show_dialog(ft.SnackBar(content=ft.Text("PDF guardado correctamente")))
        except Exception as ex:
            import traceback
            traceback.print_exc()

    # Actualizar la renderización de las tablas
    def update_tables():
        # Recargar para buscar con datos frescos
        fresh_all = get_movements_data()
        fresh_entries = [m for m in fresh_all if m['tipo'] == 'Entrada']
        fresh_exits = [m for m in fresh_all if m['tipo'] == 'Salida']

        filtered_entries = [
            e for e in fresh_entries 
            if not search_query or search_query.lower() in e["product_name"].lower() or search_query.lower() in e["responsable"].lower()
        ]
        
        filtered_exits = [
            e for e in fresh_exits 
            if not search_query or search_query.lower() in e["product_name"].lower() or search_query.lower() in e["responsable"].lower()
        ]

        # Renderizar Entradas
        entry_rows = []
        for e in filtered_entries:
            # Formatear la fecha para móvil (ej: 25-06 14:32)
            try:
                dt = datetime.strptime(e["date"], "%Y-%m-%d %H:%M:%S")
                date_display = dt.strftime("%d-%m %H:%M")
            except Exception:
                date_display = e["date"][5:16] if len(e["date"]) >= 16 else e["date"]

            entry_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(date_display, size=11, color=colors["text_sub"])),
                        ft.DataCell(ft.Text(e["product_name"], size=11, weight=ft.FontWeight.W_500, color=colors["text_main"])),
                        ft.DataCell(ft.Text(f"+{e['quantity_movement']}", size=11, color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(e["responsable"], size=10, color=colors["text_sub"])),
                    ]
                )
            )
        
        if not entry_rows:
            entries_container.content = ft.Container(
                content=ft.Text("Sin registros de entradas", color=colors["text_sub"], size=12),
                padding=20,
                alignment=ft.Alignment.CENTER
            )
        else:
            entries_container.content = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Fecha", size=10, color=colors["text_sub"])),
                    ft.DataColumn(ft.Text("Producto", size=10, color=colors["text_sub"])),
                    ft.DataColumn(ft.Text("Cant.", size=10, color=colors["text_sub"])),
                    ft.DataColumn(ft.Text("Encargado", size=10, color=colors["text_sub"])),
                ],
                rows=entry_rows,
                column_spacing=12,
                horizontal_margin=6,
                heading_row_height=30,
                data_row_min_height=40,
                data_row_max_height=48
            )

        # Renderizar Salidas
        exit_rows = []
        for e in filtered_exits:
            try:
                dt = datetime.strptime(e["date"], "%Y-%m-%d %H:%M:%S")
                date_display = dt.strftime("%d-%m %H:%M")
            except Exception:
                date_display = e["date"][5:16] if len(e["date"]) >= 16 else e["date"]

            exit_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(date_display, size=11, color=colors["text_sub"])),
                        ft.DataCell(ft.Text(e["product_name"], size=11, weight=ft.FontWeight.W_500, color=colors["text_main"])),
                        ft.DataCell(ft.Text(f"-{e['quantity_movement']}", size=11, color=ft.Colors.RED_ACCENT_400, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(e["responsable"], size=10, color=colors["text_sub"])),
                    ]
                )
            )

        if not exit_rows:
            exits_container.content = ft.Container(
                content=ft.Text("Sin registros de salidas", color=colors["text_sub"], size=12),
                padding=20,
                alignment=ft.Alignment.CENTER
            )
        else:
            exits_container.content = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Fecha", size=10, color=colors["text_sub"])),
                    ft.DataColumn(ft.Text("Producto", size=10, color=colors["text_sub"])),
                    ft.DataColumn(ft.Text("Cant.", size=10, color=colors["text_sub"])),
                    ft.DataColumn(ft.Text("Encargado", size=10, color=colors["text_sub"])),
                ],
                rows=exit_rows,
                column_spacing=12,
                horizontal_margin=6,
                heading_row_height=30,
                data_row_min_height=40,
                data_row_max_height=48
            )

        try:
            entries_container.update()
        except RuntimeError:
            pass
        try:
            exits_container.update()
        except RuntimeError:
            pass

    def search_changed(e):
        nonlocal search_query
        search_query = e.control.value
        update_tables()

    search_bar = ft.TextField(
        label="Buscar en historial...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        bgcolor=colors["card_bg"],
        border_color=colors["border"],
        text_style=ft.TextStyle(color=colors["text_main"]),
        label_style=ft.TextStyle(color=colors["text_sub"]),
        border_radius=12,
        on_change=search_changed,
        height=48
    )

    # Inicializar tablas
    update_tables()

    # Layout estructurado para pantallas móviles
    return ft.Column([
        # Encabezado
        ft.Column([
            ft.Text("Movimientos", size=24, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            ft.Text("Historial cronológico de entradas y salidas", size=12, color=colors["text_sub"])
        ]),
        
        # Buscador superior
        search_bar,
        
        # Sección de Entradas
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.ARROW_UPWARD_ROUNDED, color=ft.Colors.GREEN_400, size=18),
                        ft.Text("Entradas", size=15, weight=ft.FontWeight.BOLD, color=colors["text_main"])
                    ], spacing=6),
                    ft.IconButton(
                        icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                        icon_color=ft.Colors.RED_400,
                        icon_size=18,
                        tooltip="Exportar Entradas a PDF",
                        on_click=lambda _: page.run_task(export_to_pdf, "Entradas")
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=colors["divider"], height=1),
                entries_container
            ]),
            bgcolor=colors["card_bg"],
            border=border_all(1, colors["border"]),
            border_radius=16,
            padding=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK)
            )
        ),
        
        # Sección de Salidas
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.ARROW_DOWNWARD_ROUNDED, color=ft.Colors.RED_ACCENT_400, size=18),
                        ft.Text("Salidas", size=15, weight=ft.FontWeight.BOLD, color=colors["text_main"])
                    ], spacing=6),
                    ft.IconButton(
                        icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                        icon_color=ft.Colors.RED_400,
                        icon_size=18,
                        tooltip="Exportar Salidas a PDF",
                        on_click=lambda _: page.run_task(export_to_pdf, "Salidas")
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=colors["divider"], height=1),
                exits_container
            ]),
            bgcolor=colors["card_bg"],
            border=border_all(1, colors["border"]),
            border_radius=16,
            padding=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK)
            )
        )
    ], spacing=16, scroll=ft.ScrollMode.ADAPTIVE, alignment=ft.MainAxisAlignment.START, key=f"movements_view_{page.theme_mode}")

def generate_pdf(data, table_name, path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=safe_str(f"Reporte de {table_name}"), ln=True, align='C')
    pdf.ln(10)
    
    # Encabezados
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, safe_str("Fecha"), 1)
    pdf.cell(80, 10, safe_str("Producto"), 1)
    pdf.cell(30, 10, safe_str("Cant."), 1)
    pdf.cell(40, 10, safe_str("Responsable"), 1, ln=True)
    
    # Filas
    pdf.set_font("Arial", size=10)
    for e in data:
        pdf.cell(40, 10, safe_str(e['date'][:10]), 1)
        pdf.cell(80, 10, safe_str(e['product_name']), 1)
        pdf.cell(30, 10, safe_str(f"{e['quantity_movement']}"), 1)
        pdf.cell(40, 10, safe_str(e['responsable']), 1, ln=True)
        
    pdf.output(path)
    return True