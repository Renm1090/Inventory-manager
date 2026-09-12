import flet as ft
from datetime import datetime
from src.database import get_all_products, add_product, add_movement
from src.theme import get_theme_colors, border_all

def inventory_view(page: ft.Page):
    colors = get_theme_colors(page)
    
    # Estado local de la vista (cargado de la BD)
    products = get_all_products()
    current_filter = "Todos"
    search_query = ""

    # Elementos de la UI que se actualizarán dinámicamente
    table_container = ft.Container()
    
    # Notificación rápida
    def show_toast(message, color=ft.Colors.GREEN_700):
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                bgcolor=color,
                duration=3000
            )
        )

    # Función para renderizar la tabla con filtros aplicados
    def update_table():
        nonlocal products
        products = get_all_products()

        filtered_products = []
        for p in products:
            # Filtrar por búsqueda
            if search_query and search_query.lower() not in p["name"].lower():
                continue
            # Filtrar por estado
            is_crit = p["quantity"] < p["critical"]
            if current_filter == "Stock Crítico" and not is_crit:
                continue
            if current_filter == "Disponible" and is_crit:
                continue
            filtered_products.append(p)

        rows = []
        for p in filtered_products:
            is_critical = p["quantity"] < p["critical"]
            qty_color = ft.Colors.RED_ACCENT_400 if is_critical else ft.Colors.GREEN_400
            qty_weight = ft.FontWeight.BOLD if is_critical else ft.FontWeight.NORMAL
            
            # Badge de estado stock crítico
            badge_content = (
                ft.Container(
                    content=ft.Text("STOCK BAJO", size=8, color=ft.Colors.RED_300, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.RED),
                    border=border_all(1, ft.Colors.with_opacity(0.3, ft.Colors.RED)),
                    border_radius=4,
                    padding=ft.Padding(3, 3, 3, 3)
                )
                if is_critical else
                ft.Container(
                    content=ft.Text("ÓPTIMO", size=8, color=ft.Colors.GREEN_300, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                    border=border_all(1, ft.Colors.with_opacity(0.3, ft.Colors.GREEN)),
                    border_radius=4,
                    padding=ft.Padding(3, 3, 3, 3)
                )
            )

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Column([
                                ft.Text(p["name"], size=13, weight=ft.FontWeight.W_500, color=colors["text_main"]),
                                ft.Row([
                                    badge_content,
                                    ft.Text(f"{p['unidad']} (Mín: {p['critical']})", size=9, color=colors["text_sub"])
                                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                            ], alignment=ft.MainAxisAlignment.CENTER, spacing=2)
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(f"{p['quantity']}", size=13, weight=qty_weight, color=qty_color),
                                alignment=ft.Alignment.CENTER_LEFT
                            )
                        ),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_color=ft.Colors.BLUE_400,
                                icon_size=18,
                                tooltip="Actualizar stock",
                                on_click=lambda e, prod=p: open_update_stock_modal(prod)
                            )
                        )
                    ]
                )
            )

        if not rows:
            table_container.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=48, color=colors["text_sub"]),
                    ft.Text("No se encontraron productos", color=colors["text_sub"], size=14)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=40
            )
        else:
            table_container.content = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Producto", size=12, color=colors["text_sub"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Cant.", size=12, color=colors["text_sub"], weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Acción", size=12, color=colors["text_sub"], weight=ft.FontWeight.BOLD)),
                ],
                rows=rows,
                column_spacing=15,
                horizontal_margin=8,
                heading_row_height=35,
                data_row_min_height=48,
                data_row_max_height=60
            )
        try:
            table_container.update()
        except RuntimeError:
            pass

    # Formulario: Actualizar Stock Directamente
    def open_update_stock_modal(product):
        txt_new_qty = ft.TextField(
            label="Nueva Cantidad",
            value=str(product["quantity"]),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=colors["border"],
            bgcolor=colors["input_bg"],
            text_style=ft.TextStyle(color=colors["text_main"]),
            label_style=ft.TextStyle(color=colors["text_sub"]),
            autofocus=True
        )

        def save_update(e):
            try:
                new_qty = int(txt_new_qty.value)
                if new_qty < 0:
                    txt_new_qty.error_text = "No puede ser menor a 0"
                    txt_new_qty.update()
                    return

                old_qty = product["quantity"]
                diff = new_qty - old_qty
                
                if diff != 0:
                    tipo_mov = "Entrada" if diff > 0 else "Salida"
                    cant_mov = abs(diff)
                    if add_movement(product["name"], cant_mov, tipo_mov, "Ajuste de Stock"):
                        show_toast(f"Stock de '{product['name']}' actualizado a {new_qty}", ft.Colors.BLUE_700)
                    else:
                        show_toast("Fallo al actualizar stock en BD", ft.Colors.RED_700)
                
                update_table()
                page.pop_dialog()
            except ValueError:
                txt_new_qty.error_text = "Ingrese un número válido"
                txt_new_qty.update()

        modal = ft.AlertDialog(
            title=ft.Text("Actualizar Stock", size=16, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            content=ft.Column([
                ft.Text(f"Producto: {product['name']}", size=12, color=colors["text_sub"]),
                ft.Container(height=10),
                txt_new_qty
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_modal(modal), style=ft.ButtonStyle(color=colors["text_button"])),
                ft.ElevatedButton("Guardar", bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE, on_click=save_update)
            ],
            bgcolor=colors["card_bg"]
        )
        page.show_dialog(modal)

    def close_modal(modal):
        page.pop_dialog()

    # Formulario 1: Agregar Nuevo Producto
    def open_add_product_modal(e):
        txt_name = ft.TextField(
            label="Nombre del Producto", 
            border_color=colors["border"], 
            bgcolor=colors["input_bg"],
            text_style=ft.TextStyle(color=colors["text_main"]),
            label_style=ft.TextStyle(color=colors["text_sub"])
        )
        txt_qty = ft.TextField(
            label="Cantidad Inicial", 
            keyboard_type=ft.KeyboardType.NUMBER, 
            border_color=colors["border"],
            bgcolor=colors["input_bg"],
            text_style=ft.TextStyle(color=colors["text_main"]),
            label_style=ft.TextStyle(color=colors["text_sub"]),
            value="0"
        )
        txt_critical = ft.TextField(
            label="Stock Mínimo (Alerta)", 
            keyboard_type=ft.KeyboardType.NUMBER, 
            border_color=colors["border"],
            bgcolor=colors["input_bg"],
            text_style=ft.TextStyle(color=colors["text_main"]),
            label_style=ft.TextStyle(color=colors["text_sub"]),
            value="5"
        )
        dropdown_unit = ft.Dropdown(
            label="Unidad de Medida",
            options=[
                ft.dropdown.Option("Unidades"),
                ft.dropdown.Option("Kilogramos (Kg)"),
                ft.dropdown.Option("Litros (Lts)"),
                ft.dropdown.Option("Paquetes"),
                ft.dropdown.Option("Cajas"),
            ],
            value="Unidades",
            border_color=colors["border"],
            bgcolor=colors["input_bg"],
            color=colors["text_main"],
            label_style=ft.TextStyle(color=colors["text_sub"])
        )

        def save_product(e):
            name_val = txt_name.value.strip()
            if not name_val:
                txt_name.error_text = "El nombre es requerido"
                txt_name.update()
                return
            
            try:
                qty_val = int(txt_qty.value) if txt_qty.value else 0
                if qty_val < 0:
                    txt_qty.error_text = "No puede ser menor a 0"
                    txt_qty.update()
                    return
            except ValueError:
                txt_qty.error_text = "Ingrese un número válido"
                txt_qty.update()
                return

            try:
                crit_val = int(txt_critical.value) if txt_critical.value else 5
                if crit_val < 0:
                    txt_critical.error_text = "No puede ser menor a 0"
                    txt_critical.update()
                    return
            except ValueError:
                txt_critical.error_text = "Ingrese un número válido"
                txt_critical.update()
                return

            # Agregar a base de datos
            if add_product(name_val, qty_val, dropdown_unit.value, crit_val):
                update_table()
                page.pop_dialog()
                show_toast(f"Producto '{name_val}' agregado con éxito.", ft.Colors.TEAL_700)
            else:
                show_toast("Error: El producto ya existe en el inventario.", ft.Colors.RED_700)

        modal = ft.AlertDialog(
            title=ft.Text("Nuevo Producto", size=18, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            content=ft.Column([
                txt_name,
                dropdown_unit,
                ft.Row([
                    ft.Container(content=txt_qty, expand=True),
                    ft.Container(content=txt_critical, expand=True)
                ], spacing=10)
            ], spacing=12, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_modal(modal), style=ft.ButtonStyle(color=colors["text_button"])),
                ft.ElevatedButton("Agregar", bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE, on_click=save_product)
            ],
            bgcolor=colors["card_bg"]
        )
        page.show_dialog(modal)

    # Formulario 2: Registrar Movimiento
    def open_register_movement_modal(e):
        nonlocal products
        products = get_all_products()
        
        if not products:
            show_toast("Primero debe agregar productos al inventario", ft.Colors.ORANGE_800)
            return

        product_options = [ft.dropdown.Option(p["name"]) for p in products]
        
        dropdown_product = ft.Dropdown(
            label="Seleccionar Producto",
            options=product_options,
            border_color=colors["border"],
            bgcolor=colors["input_bg"],
            color=colors["text_main"],
            label_style=ft.TextStyle(color=colors["text_sub"]),
            hint_text="Elija un producto"
        )
        
        txt_qty = ft.TextField(
            label="Cantidad",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=colors["border"],
            bgcolor=colors["input_bg"],
            text_style=ft.TextStyle(color=colors["text_main"]),
            label_style=ft.TextStyle(color=colors["text_sub"])
        )
        
        txt_manager = ft.TextField(
            label="Nombre del Encargado",
            border_color=colors["border"],
            bgcolor=colors["input_bg"],
            text_style=ft.TextStyle(color=colors["text_main"]),
            label_style=ft.TextStyle(color=colors["text_sub"]),
            value="Administrador"
        )

        radio_type = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="Entrada", label="Entrada (Suma)", fill_color=ft.Colors.GREEN_400, label_style=ft.TextStyle(color=colors["text_main"])),
                ft.Radio(value="Salida", label="Salida (Resta)", fill_color=ft.Colors.RED_400, label_style=ft.TextStyle(color=colors["text_main"]))
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            value="Entrada"
        )

        def save_movement(e):
            if not dropdown_product.value:
                dropdown_product.error_text = "Seleccione un producto"
                dropdown_product.update()
                return
            
            qty_str = txt_qty.value.strip()
            if not qty_str:
                txt_qty.error_text = "Cantidad requerida"
                txt_qty.update()
                return
            
            try:
                qty_val = int(qty_str)
                if qty_val <= 0:
                    txt_qty.error_text = "Debe ser mayor que 0"
                    txt_qty.update()
                    return
            except ValueError:
                txt_qty.error_text = "Número inválido"
                txt_qty.update()
                return
            
            manager_val = txt_manager.value.strip()
            if not manager_val:
                txt_manager.error_text = "Encargado requerido"
                txt_manager.update()
                return

            p_name = dropdown_product.value
            movement_type = radio_type.value
            
            # Validar stock en caso de Salida
            if movement_type == "Salida":
                prod_found = next((p for p in products if p["name"] == p_name), None)
                if prod_found and prod_found["quantity"] < qty_val:
                    txt_qty.error_text = f"Insuficiente. Stock actual: {prod_found['quantity']}"
                    txt_qty.update()
                    return

            # Ejecutar movimiento de forma transaccional en la DB
            if add_movement(p_name, qty_val, movement_type, manager_val):
                update_table()
                page.pop_dialog()
                
                toast_color = ft.Colors.GREEN_700 if movement_type == "Entrada" else ft.Colors.ORANGE_800
                show_toast(f"Movimiento de {movement_type} registrado para '{p_name}'", toast_color)
            else:
                show_toast("Fallo al registrar movimiento en la base de datos.", ft.Colors.RED_700)

        modal = ft.AlertDialog(
            title=ft.Text("Registrar Movimiento", size=18, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            content=ft.Column([
                radio_type,
                dropdown_product,
                txt_qty,
                txt_manager
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: close_modal(modal), style=ft.ButtonStyle(color=colors["text_button"])),
                ft.ElevatedButton("Registrar", bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE, on_click=save_movement)
            ],
            bgcolor=colors["card_bg"]
        )
        page.show_dialog(modal)

    # Buscador y filtros superiores
    def search_changed(e):
        nonlocal search_query
        search_query = e.control.value
        update_table()

    search_field = ft.TextField(
        label="Buscar producto...",
        prefix_icon=ft.Icons.SEARCH_ROUNDED,
        bgcolor=colors["card_bg"],
        border_color=colors["border"],
        text_style=ft.TextStyle(color=colors["text_main"]),
        label_style=ft.TextStyle(color=colors["text_sub"]),
        border_radius=12,
        on_change=search_changed,
        expand=True,
        height=48
    )

    # Filtros de Categorías por Chips
    def filter_clicked(e):
        nonlocal current_filter
        for chip in chip_row.controls:
            chip.selected = False
        e.control.selected = True
        current_filter = e.control.label.value
        chip_row.update()
        update_table()

    chip_row = ft.Row([
        ft.Chip(label=ft.Text("Todos", color=colors["text_main"]), selected=True, on_select=filter_clicked, selected_color=ft.Colors.with_opacity(0.2, ft.Colors.TEAL)),
        ft.Chip(label=ft.Text("Stock Crítico", color=colors["text_main"]), on_select=filter_clicked, selected_color=ft.Colors.with_opacity(0.2, ft.Colors.RED)),
        ft.Chip(label=ft.Text("Disponible", color=colors["text_main"]), on_select=filter_clicked, selected_color=ft.Colors.with_opacity(0.2, ft.Colors.GREEN)),
    ], alignment=ft.MainAxisAlignment.START, spacing=8)

    # Botones de acción rápida
    btn_add_product = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.ADD, size=16),
            ft.Text("Producto", size=11, weight=ft.FontWeight.BOLD)
        ], spacing=4),
        bgcolor=ft.Colors.TEAL_700,
        color=ft.Colors.WHITE,
        height=38,
        on_click=open_add_product_modal
    )

    btn_add_movement = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.SWAP_HORIZ, size=16),
            ft.Text("Movimiento", size=11, weight=ft.FontWeight.BOLD)
        ], spacing=4),
        bgcolor=ft.Colors.AMBER_600,
        color=ft.Colors.WHITE,
        height=38,
        on_click=open_register_movement_modal
    )

    # Inicializar Tabla
    update_table()

    # Layout de la vista
    return ft.Column([
        # Encabezado
        ft.Column([
            ft.Text("Inventario", size=24, weight=ft.FontWeight.BOLD, color=colors["text_main"]),
            ft.Text("Gestión de existencias y actualizaciones", size=12, color=colors["text_sub"])
        ]),
        
        # Botones de Acción Rápida
        ft.Row([
            btn_add_product,
            btn_add_movement
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10),
        
        ft.Divider(color=colors["divider"], height=1),
        
        # Buscador y filtros
        ft.Row([search_field], spacing=0),
        chip_row,
        
        # Tabla de Datos
        ft.Container(
            content=table_container,
            bgcolor=colors["card_bg"],
            border=border_all(1, colors["border"]),
            border_radius=16,
            padding=8,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK)
            )
        )
    ], spacing=14, scroll=ft.ScrollMode.ADAPTIVE, alignment=ft.MainAxisAlignment.START, key=f"inventory_view_{page.theme_mode}") 

