import os
import re
import json
import json

try:
    from kudea_guardian import KudeaGuardian
except ImportError:
    try:
        from applications.home.kudea_guardian import KudeaGuardian
    except ImportError:
        KudeaGuardian = None

class BrainSync:
    def __init__(self, base_path):
        self.base_path = base_path
        self.apps_path = os.path.join(base_path, 'applications')
        self.dynamic_knowledge = {}

    def scan_project(self):
        """Escanea todas las aplicaciones en busca de modelos y vistas."""
        if not os.path.exists(self.apps_path):
            print(f"Error: No se encuentra el directorio {self.apps_path}")
            return

        for app_name in os.listdir(self.apps_path):
            app_dir = os.path.join(self.apps_path, app_name)
            if os.path.isdir(app_dir):
                self.analyze_app(app_name, app_dir)

    def analyze_app(self, app_name, app_dir):
        """Analiza una aplicación específica."""
        knowledge = {
            "modelos": self.parse_models(os.path.join(app_dir, 'models.py')),
            "vistas": self.parse_views(os.path.join(app_dir, 'views.py')),
        }
        if knowledge["modelos"] or knowledge["vistas"]:
            self.dynamic_knowledge[app_name] = knowledge

    def parse_models(self, file_path):
        """Extrae nombres de modelos y sus campos."""
        if not os.path.exists(file_path):
            return []
        
        models = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Buscar clases de modelos
            class_matches = re.finditer(r'class\s+(\w+)\(models\.Model\):', content)
            for match in class_matches:
                model_name = match.group(1)
                # Extraer campos (búsqueda simple de asignaciones de campos de models)
                fields = re.findall(r'(\w+)\s*=\s*models\.\w+Field', content[match.end():content.find('class', match.end())] if content.find('class', match.end()) != -1 else content[match.end():])
                models.append({
                    "nombre": model_name,
                    "campos": fields
                })
        return models

    def parse_views(self, file_path):
        """Extrae nombres de vistas y docstrings."""
        if not os.path.exists(file_path):
            return []
        
        views = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Buscar clases de vistas y funciones
            view_matches = re.finditer(r'(class\s+(\w+)\(\w*View\)|def\s+(\w+)\(request)', content)
            for match in view_matches:
                view_name = match.group(2) or match.group(3)
                views.append(view_name)
        return list(set(views))

    def save_knowledge(self, output_path):
        """Guarda el conocimiento extraído en un archivo JSON para el Mentor."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.dynamic_knowledge, f, indent=4, ensure_ascii=False)
        print(f"Sincronización completada. Conocimiento guardado en {output_path}")

if __name__ == "__main__":
    # Ruta base del proyecto Kudea
    project_root = "/home/minipc/Documentos/kudea/kudea"
    scanner = BrainSync(project_root)
    scanner.scan_project()
    scanner.save_knowledge(os.path.join(project_root, 'applications/home/dynamic_brain.json'))
