import sqlite3
import os 
import shutil
import time

STORAGE_DIR = os.environ.get("FLET_APP_STORAGE_DATA")
if not STORAGE_DIR:
    STORAGE_DIR = "data"

DB_PATH = os.path.join(STORAGE_DIR, "database.db")
BACKUPS_DIR = os.path.join(STORAGE_DIR, "backups")

def connect():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)
    return sqlite3.connect(DB_PATH)

def init_db():
    con = connect()
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS products(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                stock_actual INTEGER DEFAULT 0,
                unidad TEXT NOT NULL,
                stock_min INTEGER DEFAULT 5
                )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS movements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                quantity_movement INTEGER NOT NULL,
                tipo TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                responsable TEXT,
                FOREIGN KEY (product_name) REFERENCES products(name)
                )""")
    
    con.commit()

    # Migración automática para base de datos existente
    try:
        cur.execute("ALTER TABLE products ADD COLUMN stock_min INTEGER DEFAULT 5")
        con.commit()
    except sqlite3.OperationalError:
        # La columna ya existe
        pass

    con.close()
    print("Database initialized successfully.")

def get_all_products():
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT id, name, stock_actual, unidad, stock_min FROM products")
    result = []
    for row in cur.fetchall():
        result.append({
            "id": row[0],
            "name": row[1],
            "quantity": row[2],
            "unidad": row[3],
            "critical": row[4]
        })
    con.close()
    return result
    
def update_product_quantity(product_name, quantity):
    con = connect()
    cur = con.cursor()
    cur.execute("UPDATE products SET stock_actual = ? WHERE name = ?", (quantity, product_name))
    con.commit()
    con.close()

def add_product(name, stock_actual, unidad="Unidades", stock_min=5):
    con = connect()
    cur = con.cursor()
    try:
        cur.execute("BEGIN TRANSACTION")
        cur.execute("INSERT INTO products (name, stock_actual, unidad, stock_min) VALUES (?, ?, ?, ?)", 
                    (name, stock_actual, unidad, stock_min))
        
        # Registrar movimiento de inventario inicial si es mayor a cero
        if stock_actual > 0:
            cur.execute("""
                INSERT INTO movements (product_name, quantity_movement, tipo, responsable) 
                VALUES (?, ?, ?, ?)
            """, (name, stock_actual, "Entrada", "Inventario Inicial"))
            
        con.commit()
        return True
    except Exception as e:
        con.rollback()
        print("Error in add_product:", e)
        return False
    finally:
        con.close()

def add_movement(product_name, quantity_movement, tipo, responsable):
    con = connect()
    cur = con.cursor()
    try:
        cur.execute("BEGIN TRANSACTION")
        # Registrar el movimiento
        cur.execute("""
            INSERT INTO movements (product_name, quantity_movement, tipo, responsable) 
            VALUES (?, ?, ?, ?)
        """, (product_name, quantity_movement, tipo, responsable))
        
        # Actualizar stock de producto según el tipo de movimiento
        if tipo == "Entrada":
            cur.execute("UPDATE products SET stock_actual = stock_actual + ? WHERE name = ?", (quantity_movement, product_name))
        elif tipo == "Salida":
            cur.execute("UPDATE products SET stock_actual = stock_actual - ? WHERE name = ?", (quantity_movement, product_name))
            
        con.commit()
        return True
    except Exception as e:
        con.rollback()
        print("Error in add_movement:", e)
        return False
    finally:
        con.close()

def get_dashboard_stats():
    con = connect()
    cur = con.cursor()
    
    # Total de artículos
    cur.execute("SELECT COUNT(*) FROM products")
    total_articles = cur.fetchone()[0]
    
    # Artículos con stock crítico (menos del stock mínimo)
    cur.execute("SELECT COUNT(*) FROM products WHERE stock_actual < stock_min")
    critical_stock = cur.fetchone()[0]
    
    # Último movimiento
    cur.execute("SELECT product_name, tipo, quantity_movement FROM movements ORDER BY date DESC LIMIT 1")
    last_row = cur.fetchone()
    
    if last_row:
        ultimo = (last_row[0], f"{last_row[1]} ({last_row[2]})")
    else:
        ultimo = ("Sin movimientos", "N/A")
    
    con.close()
    
    return {
        "total": total_articles,
        "criticos": critical_stock,
        "ultimo": ultimo
    }

def get_weekly_activity():
    import datetime
    con = connect()
    cur = con.cursor()
    
    # Obtener sumatoria de movimientos agrupados por fecha y tipo de los últimos 7 días
    cur.execute("""
        SELECT date(date) as day_date, tipo, SUM(quantity_movement) 
        FROM movements 
        WHERE date >= date('now', '-6 days')
        GROUP BY day_date, tipo
    """)
    rows = cur.fetchall()
    con.close()
    
    # Generar los últimos 7 días con nombres en español
    today = datetime.date.today()
    wday_names = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    activity = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        day_str = d.strftime("%Y-%m-%d")
        py_wday = d.weekday() # 0 = Lunes, 6 = Domingo
        activity.append({
            "date_str": day_str,
            "dia": wday_names[py_wday],
            "entradas": 0,
            "salidas": 0
        })
        
    for day_date, tipo, total in rows:
        for day in activity:
            if day["date_str"] == day_date:
                if tipo == "Entrada":
                    day["entradas"] = total
                elif tipo == "Salida":
                    day["salidas"] = total
                break
                
    return activity

def get_movements_data():
    con = connect()
    cur = con.cursor()
    cur.execute("SELECT * FROM movements ORDER BY date DESC")
    columns = [col[0] for col in cur.description]
    movimientos = [dict(zip(columns, row)) for row in cur.fetchall()]
    con.close()
    return movimientos

def create_backup():
    if not os.path.exists(BACKUPS_DIR):
        os.makedirs(BACKUPS_DIR)
    shutil.copy(DB_PATH, os.path.join(BACKUPS_DIR, f"backup_{time.strftime('%Y%m%d_%H%M%S')}.db"))

def get_backups_list():
    if not os.path.exists(BACKUPS_DIR):
        return []
    files = [f for f in os.listdir(BACKUPS_DIR) if f.startswith("backup_") and f.endswith(".db")]
    return sorted(files, reverse=True)

def restore_backup(backup_name):
    backup_path = os.path.join(BACKUPS_DIR, backup_name)
    if os.path.exists(backup_path):
        # Crear copia temporal del actual por si falla la restauración
        shutil.copy(DB_PATH, DB_PATH + ".tmp")
        try:
            shutil.copy(backup_path, DB_PATH)
            if os.path.exists(DB_PATH + ".tmp"):
                os.remove(DB_PATH + ".tmp")
            return True
        except Exception as e:
            if os.path.exists(DB_PATH + ".tmp"):
                shutil.copy(DB_PATH + ".tmp", DB_PATH)
                os.remove(DB_PATH + ".tmp")
            print("Error restoring backup:", e)
            return False
    return False

def optimize_db():
    con = connect()
    con.execute("VACUUM") 
    con.close()

if __name__ == "__main__":
    init_db()