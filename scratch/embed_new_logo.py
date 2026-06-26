import base64
import os
from PIL import Image
import io

img_path = r"C:\Users\alvaro.mendes\.gemini\antigravity-ide\brain\03b48198-01ed-4d48-9935-0d740decb019\media__1782477144688.png"
html_path = r"producao/templates/producao/index.html"

def make_transparent_base64(path):
    img = Image.open(path)
    img = img.convert("RGBA")
    
    datas = img.getdata()
    new_data = []
    
    for item in datas:
        # Check if pixel is black (R, G, B all below 35)
        if item[0] < 35 and item[1] < 35 and item[2] < 35:
            # Replace with transparent pixel
            new_data.append((0, 0, 0, 0))
        else:
            # Force it to pure white to look sharp and clean on the blue topbar
            new_data.append((255, 255, 255, item[3]))
            
    img.putdata(new_data)
    
    # Save to buffer and base64 encode
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def main():
    if not os.path.exists(img_path):
        print(f"Image not found at: {img_path}")
        return
        
    if not os.path.exists(html_path):
        print(f"HTML template not found at: {html_path}")
        return
        
    print("Generating base64 transparent logo from new image...")
    base64_logo = make_transparent_base64(img_path)
    
    print("Reading HTML template...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    # Find the current image tag and replace its src
    # The current tag looks like: <img src="data:image/png;base64,..." alt="Electro Plastic Logo" style="height: 48px; display: block; margin: 4px 0;">
    import re
    
    pattern = r'<img src="data:image/png;base64,[^"]+" alt="Electro Plastic Logo"[^>]*>'
    matches = list(re.finditer(pattern, html))
    
    if matches:
        print(f"Found {len(matches)} logo match(es). Replacing...")
        replacement = f'<img src="data:image/png;base64,{base64_logo}" alt="Electro Plastic Logo" style="height: 48px; display: block; margin: 4px 0;">'
        html = re.sub(pattern, replacement, html)
    else:
        print("Warning: Logo image tag matching pattern not found. Trying fallback search.")
        # Fallback to replace the entire <div class="brand"> contents if needed
        
    print("Saving changes to HTML template...")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("New logo embed completed successfully!")

if __name__ == "__main__":
    main()
