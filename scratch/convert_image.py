import base64
import os

img_path = r"C:\Users\alvaro.mendes\.gemini\antigravity-ide\brain\03b48198-01ed-4d48-9935-0d740decb019\media__1782475135628.png"

try:
    from PIL import Image
    has_pil = True
except ImportError:
    has_pil = False

print("PIL installed:", has_pil)

if os.path.exists(img_path):
    with open(img_path, 'rb') as f:
        data = f.read()
    print("Image size:", len(data))
else:
    print("Image not found at path.")
