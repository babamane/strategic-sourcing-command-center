import os
from pathlib import Path

css_dir = Path(r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src\components")

for file in css_dir.glob("*.css"):
    # Skip dashboard and sidebar as they're done, or just run over them again
    if file.name.endswith(".backup"):
        continue
        
    with open(file, "r") as f:
        content = f.read()

    # Replace hardcoded whites with dark mode secondary bg
    new_content = content.replace("background: white;", "background: var(--secondary-bg);")
    new_content = new_content.replace("background-color: white;", "background-color: var(--secondary-bg);")
    new_content = new_content.replace("background: #ffffff;", "background: var(--secondary-bg);")
    new_content = new_content.replace("background-color: #ffffff;", "background-color: var(--secondary-bg);")
    
    # Also fix any modal specific hardcoded values (like 255, 255, 255)
    new_content = new_content.replace("rgba(255, 255, 255, 0.9)", "rgba(17, 24, 39, 0.9)")
    new_content = new_content.replace("rgba(255, 255, 255, 0.95)", "rgba(17, 24, 39, 0.95)")
    new_content = new_content.replace("rgba(255, 255, 255, 1)", "var(--secondary-bg)")

    if new_content != content:
        with open(file, "w") as f:
            f.write(new_content)
        print(f"Updated {file.name}")
