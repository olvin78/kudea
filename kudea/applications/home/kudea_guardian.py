import os
import json
import sqlite3
import re
from datetime import datetime

class KudeaGuardian:
    def __init__(self, project_root):
        self.project_root = project_root
        self.db_path = os.path.join(project_root, 'db.sqlite3')
        self.anomalies_path = os.path.join(project_root, 'applications/home/anomalies.json')
        self.anomalies = []

    def check_database_integrity(self):
        """Busca anomalías de negocio en la base de datos."""
        if not os.path.exists(self.db_path):
            return

        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        except Exception as e:
            self.add_anomaly("sistema", f"No pude conectar a la base de datos: {str(e)}")
            return

        # 1. Stock Negativo — columnas reales: nombre, stock
        try:
            cursor.execute("SELECT nombre, stock FROM product_producto WHERE stock < 0;")
            for nombre, stock in cursor.fetchall():
                self.add_anomaly("negocio", f"El producto '{nombre}' tiene stock negativo ({stock}). ¡Eso es físicamente imposible!")
        except Exception:
            pass

        # 2. Productos con precio 0 o negativo — columna real: precio
        try:
            cursor.execute("SELECT nombre FROM product_producto WHERE precio <= 0;")
            for (nombre,) in cursor.fetchall():
                self.add_anomaly("negocio", f"El producto '{nombre}' tiene precio 0€ o negativo. ¡Cuidado, esto significa pérdidas!")
        except Exception:
            pass

        # 3. Cajas abiertas de días anteriores
        try:
            cursor.execute("SELECT id, fecha FROM cash_aperturacaja WHERE estado = 'abierta';")
            for cid, fecha in cursor.fetchall():
                if str(datetime.now().date()) not in str(fecha):
                    self.add_anomaly("operativo", f"La caja #{cid} lleva abierta desde {fecha}. Deberías cerrarla para que el arqueo cuadre.")
        except Exception:
            pass

        conn.close()


    def check_code_health(self):
        """Busca errores groseros en el código (SyntaxErrors)."""
        apps_dir = os.path.join(self.project_root, 'applications')
        for root, dirs, files in os.walk(apps_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            compile(f.read(), file_path, 'exec')
                    except SyntaxError as e:
                        self.add_anomaly("ingenieria", f"He detectado un error de sintaxis en el archivo '{file}': {e.msg} (Línea {e.lineno}). El sistema podría fallar.")

    def add_anomaly(self, tipo, mensaje):
        self.anomalies.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": tipo.upper(),
            "mensaje": mensaje
        })

    def save_report(self):
        """Guarda las anomalías para que el Mentor las lea."""
        with open(self.anomalies_path, 'w', encoding='utf-8') as f:
            json.dump(self.anomalies, f, indent=4, ensure_ascii=False)
        print(f"Centinela Guardian: {len(self.anomalies)} anomalías detectadas. Reporte guardado.")

if __name__ == "__main__":
    project_root = "/home/minipc/Documentos/kudea/kudea"
    guardian = KudeaGuardian(project_root)
    guardian.check_database_integrity()
    guardian.check_code_health()
    guardian.save_report()
