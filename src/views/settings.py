import flet as ft
import os
import csv
import json
from src.database import (
    create_backup, 
    optimize_db, 
    get_backups_list, 
    restore_backup, 
    get_all_products, 
    get_movements_data
)
from src.theme import get_theme_colors, border_all

def settings_view(page: ft.Page):
    colors = get_theme_colors(page)

    # Función auxiliar para crear contenedores de iconos coloridos
    def make_icon_container(icon, bgcolor):
        return ft.Container(
            content=ft.Icon(icon, color=ft.Colors.WHITE, size=20),
            bgcolor=bgcolor,
            padding=8,
            border_radius=10,
            alignment=ft.Alignment.CENTER
        )

    # Toast helper (Compatible con Flet moderno)
    def show_toast(message, color=ft.Colors.GREEN_700):
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=color,
                duration=3000
            )
        )

    # Helpers de exportación
    def generate_csv_bytes():
        import io
        products = get_all_products()
        f = io.StringIO()
        writer = csv.writer(f)
        writer.writerow(["ID", "Nombre", "Cantidad", "Unidad", "Stock Minimo"])
        for p in products:
            writer.writerow([p["id"], p["name"], p["quantity"], p["unidad"], p["critical"]])
        return f.getvalue().encode('utf-8')

    def generate_json_bytes():
        products = get_all_products()
        movements = get_movements_data()
        data = {
            "productos": products,
            "movimientos": movements
        }
        return json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')

    def close_modal(modal):
        page.pop_dialog()

    # Modal: Exportar Datos
    def show_export_modal(e):
        formats = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(value="CSV", label="Valores Separados por Comas (.csv)", fill_color=ft.Colors.TEAL_400, label_style=ft.TextStyle(color=colors["text_main"])),
                ft.Radio(value="JSON", label="Archivo JSON (.json)", fill_color=ft.Colors.TEAL_400, label_style=ft.TextStyle(color=colors["text_main"])),
            ]),
            value="CSV"
        )
        
        async def run_export(e):
            selected = formats.value
            page.pop_dialog()
            
            try:
                if selected == "CSV":
                    csv_bytes = generate_csv_bytes()
                    
                    # Intento de guardado directo en la carpeta pública "Download" de Android
                    if page.platform == ft.PagePlatform.ANDROID:
                        for possible_path in ["/storage/emulated/0/Download", "/sdcard/Download"]:
                            if os.path.exists(possible_path):
                                try:
                                    filepath = os.path.join(possible_path, "productos_inventario.csv")
                                    with open(filepath, "wb") as f:
                                        f.write(csv_bytes)
                                    show_toast(f"CSV guardado en Descargas: {filepath}", ft.Colors.BLUE_700)
                                    return
                                except Exception:
                                    pass
                    
                    path = await page.save_file_dialog.save_file(
                        file_name="productos_inventario.csv",
                        allowed_extensions=["csv"],
                        src_bytes=csv_bytes
                    )
                    if path:
                        if page.platform not in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
                            with open(path, "wb") as f:
                                f.write(csv_bytes)
                        show_toast("CSV guardado correctamente", ft.Colors.BLUE_700)
                elif selected == "JSON":
                    json_bytes = generate_json_bytes()
                    
                    # Intento de guardado directo en la carpeta pública "Download" de Android
                    if page.platform == ft.PagePlatform.ANDROID:
                        for possible_path in ["/storage/emulated/0/Download", "/sdcard/Download"]:
                            if os.path.exists(possible_path):
                                try:
                                    filepath = os.path.join(possible_path, "inventario_completo.json")
                                    with open(filepath, "wb") as f:
                                        f.write(json_bytes)
                                    show_toast(f"JSON guardado en Descargas: {filepath}", ft.Colors.BLUE_700)
                                    return
                                except Exception:
                                    pass
                    
                    path = await page.save_file_dialog.save_file(
                        file_name="inventario_completo.json",
                        allowed_extensions=["json"],
                        src_bytes=json_bytes
                    )
                    if path:
                        if page.platform not in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
                            with open(path, "wb") as f:
                                f.write(json_bytes)
                        show_toast("JSON guardado correctamente", ft.Colors.BLUE_700)
            except Exception as ex:
                show_toast(f"Error al exportar: {str(ex)}", ft.Colors.RED_700)

        modal = ft.AlertDialog(
            title=ft.Text("Exportar Inventario", size=18, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            content=ft.Column([
                ft.Text("Seleccione el formato para descargar el respaldo del inventario:", size=12, color=colors["text_sub"]),
                ft.Container(height=8),
                formats
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_modal(modal), style=ft.ButtonStyle(color=colors["text_button"])),
                ft.ElevatedButton("Exportar Ahora", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, on_click=run_export)
            ],
            bgcolor=colors["card_bg"]
        )
        page.show_dialog(modal)

    # Modal: Gestión de Base de Datos
    def show_db_modal(e):
        backups = get_backups_list()
        
        if backups:
            backup_dropdown = ft.Dropdown(
                label="Copias de Seguridad",
                options=[ft.dropdown.Option(b) for b in backups],
                value=backups[0],
                expand=True,
                border_color=colors["border"],
                label_style=ft.TextStyle(color=colors["text_sub"]),
                color=colors["text_main"]
            )
            
            def on_restore_click(e):
                selected_backup = backup_dropdown.value
                if not selected_backup:
                    return
                
                def confirm_restore(e):
                    page.pop_dialog()
                    if restore_backup(selected_backup):
                        page.pop_dialog()
                        show_toast(f"Base de datos restaurada desde '{selected_backup}' con éxito.", ft.Colors.TEAL_700)
                    else:
                        show_toast("Fallo al restaurar la base de datos.", ft.Colors.RED_700)
                
                confirm_dialog = ft.AlertDialog(
                    title=ft.Text("Confirmar Restauración", size=16, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
                    content=ft.Text(f"¿Estás seguro de que deseas reemplazar la base de datos actual con '{selected_backup}'? Esta acción no se puede deshacer.", size=12, color=colors["text_sub"]),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda _: close_modal(confirm_dialog), style=ft.ButtonStyle(color=colors["text_button"])),
                        ft.ElevatedButton("Restaurar", bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, on_click=confirm_restore)
                    ],
                    bgcolor=colors["card_bg"]
                )
                page.show_dialog(confirm_dialog)

            restore_section = ft.Column([
                ft.Text("Restaurar desde Copia de Seguridad", size=12, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
                ft.Row([
                    backup_dropdown,
                    ft.IconButton(
                        icon=ft.Icons.RESTORE_ROUNDED, 
                        icon_color=ft.Colors.RED_ACCENT_400, 
                        tooltip="Restaurar copia seleccionada",
                        on_click=on_restore_click
                    )
                ], spacing=8)
            ], spacing=6)
        else:
            restore_section = ft.Text("No hay copias de seguridad creadas.", size=11, italic=True, color=colors["text_sub"])

        def trigger_action(action_name):
            if action_name == "Respaldo de BD":
                create_backup()
                show_toast("Copia de seguridad creada correctamente.", ft.Colors.TEAL_700)
                # Cerrar y volver a abrir para refrescar dropdown
                page.pop_dialog()
                show_db_modal(None)
            elif action_name == "Optimización de BD":
                optimize_db()
                show_toast("Base de datos optimizada y compactada.", ft.Colors.TEAL_700)
                page.pop_dialog()

        modal = ft.AlertDialog(
            title=ft.Text("Gestión de Base de Datos", size=18, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            content=ft.Column([
                ft.Text("Operaciones de mantenimiento sobre SQLite:", size=12, color=colors["text_sub"]),
                ft.Container(height=6),
                ft.OutlinedButton(
                    content=ft.Row([ft.Icon(ft.Icons.BACKUP_ROUNDED, size=16, color=ft.Colors.TEAL_400), ft.Text("Crear copia de seguridad (Backup)", color=colors["text_main"])], spacing=8),
                    on_click=lambda e: trigger_action("Respaldo de BD"),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.OutlinedButton(
                    content=ft.Row([ft.Icon(ft.Icons.CLEANING_SERVICES_ROUNDED, size=16, color=ft.Colors.AMBER_400), ft.Text("Optimizar tamaño e índices", color=colors["text_main"])], spacing=8),
                    on_click=lambda e: trigger_action("Optimización de BD"),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.Divider(color=colors["divider"]),
                restore_section
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda _: close_modal(modal), style=ft.ButtonStyle(color=colors["text_button"]))
            ],
            bgcolor=colors["card_bg"]
        )
        page.show_dialog(modal)

    # Modal: Información de la App
    def show_info_modal(e):
        modal = ft.AlertDialog(
            title=ft.Text("Acerca del Sistema", size=18, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, size=54, color=ft.Colors.TEAL_400),
                    alignment=ft.Alignment.CENTER,
                    padding=10
                ),
                ft.Text("Gestor de Inventario Móvil", size=16, weight=ft.FontWeight.BOLD, color=colors["text_main"], text_align=ft.TextAlign.CENTER),
                ft.Text("Versión: 1.2.0-Estable\nTecnología: Python + Flet (Flutter)\nBase de Datos: SQLite 3", size=12, color=colors["text_sub"], text_align=ft.TextAlign.CENTER),
                ft.Divider(color=colors["divider"]),
                ft.Text("Optimizado para control de almacén rápido y responsivo en pantallas moviles.", size=11, italic=True, color=colors["text_sub"], text_align=ft.TextAlign.CENTER),
                ft.Text("Desarrollador: Renm", size=11, italic=True, color=colors["text_sub"], text_align=ft.TextAlign.CENTER)
            ], spacing=8, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Entendido", on_click=lambda _: close_modal(modal), style=ft.ButtonStyle(color=colors["text_button"]))
            ],
            bgcolor=colors["card_bg"]
        )
        page.show_dialog(modal)


    # 1. Grupo: Datos e Historial
    group_data = ft.Container(
        content=ft.Column([
            ft.Text("Datos e Historial", size=12, weight=ft.FontWeight.BOLD, color=colors["text_sub"]),
            ft.Container(height=4),
            # Opción 1: Exportar
            ft.Container(
                content=ft.Row([
                    make_icon_container(ft.Icons.DOWNLOAD_ROUNDED, ft.Colors.BLUE_700),
                    ft.Column([
                        ft.Text("Exportar Inventario Completo", size=14, weight=ft.FontWeight.W_500, color=colors["text_main"]),
                        ft.Text("Descargar en CSV o JSON", size=11, color=colors["text_sub"])
                    ], spacing=2, expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=14, color=colors["text_sub"])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=12),
                on_click=show_export_modal,
                ink=True,
                padding=8,
                border_radius=8
            ),
            ft.Divider(color=colors["divider"], height=1),
            # Opción 2: Base de Datos
            ft.Container(
                content=ft.Row([
                    make_icon_container(ft.Icons.STORAGE_ROUNDED, ft.Colors.TEAL_600),
                    ft.Column([
                        ft.Text("Gestión de Base de Datos", size=14, weight=ft.FontWeight.W_500, color=colors["text_main"]),
                        ft.Text("Copias de seguridad y optimización", size=11, color=colors["text_sub"])
                    ], spacing=2, expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=14, color=colors["text_sub"])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=12),
                on_click=show_db_modal,
                ink=True,
                padding=8,
                border_radius=8
            ),
        ], spacing=4),
        bgcolor=colors["card_bg"],
        padding=12,
        border_radius=16,
        border=border_all(1, colors["border"])
    )

    # 2. Grupo: Preferencias de Usuario
    group_preferences = ft.Container(
        content=ft.Column([
            ft.Text("Preferencias", size=12, weight=ft.FontWeight.BOLD, color=colors["text_sub"]),
            ft.Container(height=4),
            # Opción 1: Modo Claro
            ft.Container(
                content=ft.Row([
                    make_icon_container(ft.Icons.LIGHT_MODE_ROUNDED, ft.Colors.AMBER_600),
                    ft.Column([
                        ft.Text("Modo Claro", size=14, weight=ft.FontWeight.W_500, color=colors["text_main"]),
                        ft.Text("Cambiar tema de la interfaz", size=11, color=colors["text_sub"])
                    ], spacing=2, expand=True),
                    ft.Switch(
                        value=page.theme_mode == ft.ThemeMode.LIGHT,
                        active_color=ft.Colors.TEAL_400,
                        on_change=lambda e: page.toggle_theme(e.control.value)
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=12),
                padding=8
            ),
            ft.Divider(color=colors["divider"], height=1),
            # Opción 2: Notificaciones
            ft.Container(
                content=ft.Row([
                    make_icon_container(ft.Icons.NOTIFICATIONS_ROUNDED, ft.Colors.PURPLE_600),
                    ft.Column([
                        ft.Text("Notificaciones de Stock", size=14, weight=ft.FontWeight.W_500, color=colors["text_main"]),
                        ft.Text("Alertas de stock crítico activas", size=11, color=colors["text_sub"])
                    ], spacing=2, expand=True),
                    ft.Switch(
                        value=True, 
                        active_color=ft.Colors.PURPLE_500, 
                        on_change=lambda e: show_toast(
                            "Notificaciones activadas" if e.control.value else "Notificaciones desactivadas", 
                            colors["text_sub"]
                        )
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=12),
                padding=8
            ),
        ], spacing=4),
        bgcolor=colors["card_bg"],
        padding=12,
        border_radius=16,
        border=border_all(1, colors["border"])
    )

    # 3. Grupo: Acerca de
    group_about = ft.Container(
        content=ft.Column([
            ft.Text("Soporte y Aplicación", size=12, weight=ft.FontWeight.BOLD, color=colors["text_sub"]),
            ft.Container(height=4),
            ft.Container(
                content=ft.Row([
                    make_icon_container(ft.Icons.INFO_OUTLINE_ROUNDED, ft.Colors.GREY_700),
                    ft.Column([
                        ft.Text("Información de la Aplicación", size=14, weight=ft.FontWeight.W_500, color=colors["text_main"]),
                        ft.Text("Versión del sistema y créditos", size=11, color=colors["text_sub"])
                    ], spacing=2, expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=14, color=colors["text_sub"])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=12),
                on_click=show_info_modal,
                ink=True,
                padding=8,
                border_radius=8
            ),
        ], spacing=4),
        bgcolor=colors["card_bg"],
        padding=12,
        border_radius=16,
        border=border_all(1, colors["border"])
    )

    return ft.Column([
        # Encabezado
        ft.Column([
            ft.Text("Configuración", size=24, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            ft.Text("Ajustes del sistema y preferencias de usuario", size=12, color=colors["text_sub"])
        ]),
        
        ft.Container(height=4),
        
        # Opciones agrupadas
        group_data,
        group_preferences,
        group_about
    ], spacing=16, scroll=ft.ScrollMode.ADAPTIVE, alignment=ft.MainAxisAlignment.START, key=f"settings_view_{page.theme_mode}")