import os
import platform
import subprocess

def open_image(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", path])
    else:  # Linux
        subprocess.run(["xdg-open", path])

def delete_image(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"Файл удалён: {path}")
        else:
            print(f"Файл не найден: {path}")
    except Exception as e:
        print(f"Ошибка при удалении: {e}")