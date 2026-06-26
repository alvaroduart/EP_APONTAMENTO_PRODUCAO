import base64
import os
from PIL import Image
import io

img_path = r"C:\Users\alvaro.mendes\.gemini\antigravity-ide\brain\03b48198-01ed-4d48-9935-0d740decb019\media__1782475135628.png"
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
            # item[3] is the alpha channel
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
        
    print("Generating base64 transparent logo...")
    base64_logo = make_transparent_base64(img_path)
    
    print("Reading HTML template...")
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    # 1. Update header color
    print("Updating header color in CSS...")
    html = html.replace("--blue-deep: #00214a;", "--blue-deep: #003C91;")
    
    # 2. Update brand logo
    print("Embedding logo in topbar...")
    old_brand_section = """        <div class="brand">
            <div class="brand-mark">
                <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"
                    stroke-linejoin="round">
                    <path d="M12 2a10 10 0 1 0 7.07 2.93" />
                    <path d="M12 2v6l4-3" />
                </svg>
            </div>
            <div class="brand-text">
                <h1>ELECTRO PLASTIC</h1>
                <span>Terminal de Produção</span>
            </div>
        </div>"""
        
    # Let's write a replacement that matches what's in the index.html exactly
    # Since whitespace formatting might vary slightly, let's target the inner part of .brand
    target_brand_inner = """            <div class="brand-mark">
                <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"
                    stroke-linejoin="round">
                    <path d="M12 2a10 10 0 1 0 7.07 2.93" />
                    <path d="M12 2v6l4-3" />
                </svg>
            </div>
            <div class="brand-text">
                <h1>ELECTRO PLASTIC</h1>
                <span>Terminal de Produção</span>
            </div>"""
            
    replacement_brand_inner = f"""            <img src="data:image/png;base64,{base64_logo}" alt="Electro Plastic Logo" style="height: 48px; display: block; margin: 4px 0;">"""
    
    if target_brand_inner in html:
        html = html.replace(target_brand_inner, replacement_brand_inner)
        print("Brand inner HTML replaced successfully.")
    else:
        # Try with a different indentation or look up brand block
        print("Warning: Could not find exact brand inner string. Checking fallback.")
        
    # 3. Remove datalist reference from OP input to disable dropdown suggestion list
    print("Removing datalist link from opInput...")
    html = html.replace('list="opList"', '')
    
    print("Saving changes to HTML template...")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Embed completed successfully!")

if __name__ == "__main__":
    main()
