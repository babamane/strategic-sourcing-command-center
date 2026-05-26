import os
from pathlib import Path
import re

components_dir = Path(r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src\components")
index_css_path = Path(r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src\index.css")

# 1. Update index.css to Google Material Theme
material_index_css = """@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Google+Sans:wght@400;500;700&display=swap');

:root {
  /* Google Material Design Tokens */
  --bg-color: #f8f9fa;
  --secondary-bg: #ffffff;
  --text-color: #202124;
  --text-secondary: #5f6368;
  --accent-color: #1a73e8;
  --accent-hover: #174ea6;
  --border-color: #dadce0;
  --card-hover: #f1f3f4;
  --font-family: 'Google Sans', 'Roboto', -apple-system, sans-serif;
  
  /* Material shadows and radius */
  --shadow-sm: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
  --shadow-md: 0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15);
  --radius-md: 8px;
  --radius-lg: 12px;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--bg-color);
  color: var(--text-color);
  font-family: var(--font-family);
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}

a {
  text-decoration: none;
  color: inherit;
}

ul {
  list-style: none;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #dadce0;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9aa0a6;
}
"""
with open(index_css_path, "w") as f:
    f.write(material_index_css)

# 2. Revert dark mode and remove glassmorphism in Dashboard.css
dashboard_css_path = components_dir / "Dashboard.css"
if dashboard_css_path.exists():
    with open(dashboard_css_path, "r") as f:
        content = f.read()

    # Remove glassmorphism
    content = re.sub(r'backdrop-filter:\s*blur\([^)]+\);', '', content)
    content = re.sub(r'-webkit-backdrop-filter:\s*blur\([^)]+\);', '', content)
    
    # Restore white backgrounds and fix rgba issues
    content = re.sub(r'rgba\(17,\s*24,\s*39,\s*0\.[78]\)', 'var(--secondary-bg)', content)
    content = re.sub(r'rgba\(31,\s*41,\s*55,\s*0\.9[5]?\)', 'var(--secondary-bg)', content)
    
    # Re-apply Google material border and shadow logic
    content = content.replace("border-radius: 16px;", "border-radius: 12px;")
    content = content.replace("border-radius: 12px;", "border-radius: var(--radius-md);")
    
    # Fix the Topic Badges with Google Colors
    # Amber/Yellow -> Google Yellow
    content = re.sub(r'\.border-amber\s*{[^}]+}', '.border-amber { border-color: #fce8b2; }', content)
    content = re.sub(r'\.bg-amber-soft\s*{[^}]+}', '.bg-amber-soft { background: #fef7e0; }', content)
    content = re.sub(r'\.amber-badge\s*{[^}]+}', '.amber-badge { background: #fef7e0; color: #f29900; }', content)
    content = re.sub(r'\.text-amber\s*{[^}]+}', '.text-amber { color: #f29900; }', content)
    content = re.sub(r'\.bg-amber-bubble\s*{[^}]+}', '.bg-amber-bubble { background: #fef7e0; color: #ea8600; }', content)

    # Purple -> Google Purple
    content = re.sub(r'\.border-purple\s*{[^}]+}', '.border-purple { border-color: #e8d2ff; }', content)
    content = re.sub(r'\.bg-purple-soft\s*{[^}]+}', '.bg-purple-soft { background: #f3e8fd; }', content)
    content = re.sub(r'\.purple-badge\s*{[^}]+}', '.purple-badge { background: #f3e8fd; color: #a142f4; }', content)
    content = re.sub(r'\.text-purple\s*{[^}]+}', '.text-purple { color: #a142f4; }', content)
    content = re.sub(r'\.bg-purple-bubble\s*{[^}]+}', '.bg-purple-bubble { background: #f3e8fd; color: #9334e6; }', content)

    # Blue -> Google Blue
    content = re.sub(r'\.border-blue\s*{[^}]+}', '.border-blue { border-color: #d2e3fc; }', content)
    content = re.sub(r'\.bg-blue-soft\s*{[^}]+}', '.bg-blue-soft { background: #e8f0fe; }', content)
    content = re.sub(r'\.blue-badge\s*{[^}]+}', '.blue-badge { background: #e8f0fe; color: #1a73e8; }', content)
    content = re.sub(r'\.text-blue\s*{[^}]+}', '.text-blue { color: #1a73e8; }', content)
    content = re.sub(r'\.bg-blue-bubble\s*{[^}]+}', '.bg-blue-bubble { background: #e8f0fe; color: #174ea6; }', content)

    # Coral/Red -> Google Red
    content = re.sub(r'\.border-coral\s*{[^}]+}', '.border-coral { border-color: #fad2cf; }', content)
    content = re.sub(r'\.bg-coral-soft\s*{[^}]+}', '.bg-coral-soft { background: #fce8e6; }', content)
    content = re.sub(r'\.coral-badge\s*{[^}]+}', '.coral-badge { background: #fce8e6; color: #d93025; }', content)
    content = re.sub(r'\.text-coral\s*{[^}]+}', '.text-coral { color: #d93025; }', content)
    content = re.sub(r'\.bg-coral-bubble\s*{[^}]+}', '.bg-coral-bubble { background: #fce8e6; color: #c5221f; }', content)

    # Emerald/Green -> Google Green
    content = re.sub(r'\.border-emerald\s*{[^}]+}', '.border-emerald { border-color: #ceead6; }', content)
    content = re.sub(r'\.bg-emerald-soft\s*{[^}]+}', '.bg-emerald-soft { background: #e6f4ea; }', content)
    content = re.sub(r'\.emerald-badge\s*{[^}]+}', '.emerald-badge { background: #e6f4ea; color: #188038; }', content)
    content = re.sub(r'\.text-emerald\s*{[^}]+}', '.text-emerald { color: #188038; }', content)
    content = re.sub(r'\.bg-emerald-bubble\s*{[^}]+}', '.bg-emerald-bubble { background: #e6f4ea; color: #137333; }', content)

    # Make topic cards pure white
    content = content.replace("background: rgba(255, 255, 255, 0.7);", "background: var(--secondary-bg);")
    
    with open(dashboard_css_path, "w") as f:
        f.write(content)

# 3. Clean up Sidebar
sidebar_css_path = components_dir / "Sidebar.css"
if sidebar_css_path.exists():
    with open(sidebar_css_path, "r") as f:
        sb_content = f.read()
    sb_content = sb_content.replace("background-color: rgba(255, 255, 255, 0.05);", "background-color: #e8f0fe;")
    sb_content = sb_content.replace("color: var(--accent-color);", "color: #1a73e8;")
    # Fix the active item so it looks like Google material nav item
    sb_content = sb_content.replace("border: 1px solid var(--border-color);", "border: none;")
    with open(sidebar_css_path, "w") as f:
        f.write(sb_content)

print("Applied Google Material Dashboard styling successfully.")
