import qrcode
from .models import Employee

BASE_URL = "http://localhost:8000/attendance/fichar/"  # o tu dominio real

def generate_qrs():
    for emp in Employee.objects.all():
        if emp.qr_token:
            full_url = f"{BASE_URL}{emp.qr_token}/"
            img = qrcode.make(employee.qr_token)  # SOLO el token, NO la URL completa
            filename = f"qr_{emp.user.username}.png"
            img.save(filename)
            print(f"✅ QR generado: {filename}")
        else:
            print(f"⚠️ {emp.user.username} no tiene qr_token")
