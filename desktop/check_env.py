import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Site Packages: {[p for p in sys.path if 'site-packages' in p]}")
try:
    import qrcode
    print(f"QRCode module found at: {qrcode.__file__}")
except ImportError:
    print("QRCode module NOT FOUND")

try:
    import customtkinter
    print(f"CustomTkinter module found at: {customtkinter.__file__}")
except ImportError:
    print("CustomTkinter module NOT FOUND")
