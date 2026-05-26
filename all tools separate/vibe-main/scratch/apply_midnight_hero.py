import os
import re

css_file = r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src\components\CompanySelector.css"
jsx_file = r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src\components\CompanySelector.jsx"

with open(css_file, "r") as f:
    content = f.read()

# 1. Update landing page background to Midnight Onyx
content = re.sub(
    r'background-color:.*?;\n.*?background-size:.*?;',
    'background-color: #0b0f19;\n    background-image: radial-gradient(rgba(255,255,255,0.1) 1px, transparent 1px);\n    background-size: 30px 30px;',
    content,
    flags=re.DOTALL
)

# 2. Update Header to dark glass
content = content.replace(
    "background: rgba(255, 255, 255, 0.8);", 
    "background: rgba(11, 15, 25, 0.8);"
)
content = content.replace(
    "border-bottom: 1px solid var(--border-color);",
    "border-bottom: 1px solid rgba(255, 255, 255, 0.1);"
)
content = content.replace(
    "color: var(--text-color);",
    "color: #ffffff;"
)
content = content.replace(
    "color: var(--text-secondary);",
    "color: #9ca3af;"
)

# 3. Update Hero Title and Gradient Text to Neon
content = content.replace(
    "color: #111827;\n    background: linear-gradient(135deg, #111827 0%, #4b5563 100%);",
    "color: #ffffff;\n    background: linear-gradient(135deg, #06b6d4 0%, #10b981 100%);"
)
content = content.replace(
    "color: #111827;",
    "color: #ffffff;"
)

# 4. Update the Selection Form card to glowing dark glass
content = content.replace(
    "background: var(--secondary-bg);",
    "background: rgba(255, 255, 255, 0.03);"
)
content = content.replace(
    "border: 1px solid var(--border-color);",
    "border: 1px solid rgba(255, 255, 255, 0.1);"
)
content = content.replace(
    "box-shadow: 0 10px 40px -10px rgba(0,0,0,0.08);",
    "box-shadow: 0 10px 40px -10px rgba(6, 182, 212, 0.15);"
)

# 5. Fix form text colors inside the card
content = content.replace("background: #f8fafc;", "background: rgba(255,255,255,0.02);")
content = content.replace("border: 1px dashed #cbd5e1;", "border: 1px dashed rgba(255,255,255,0.2);")
content = content.replace("color: #1e293b;", "color: #ffffff;")

# Dropdown styling
content = content.replace("border: 1px solid #d1d5db;", "border: 1px solid rgba(255,255,255,0.2);")
content = content.replace("background: var(--secondary-bg);", "background: #111827;")

# 6. Buttons
content = content.replace(
    "background: #111827;",
    "background: #06b6d4;"
)
content = content.replace(
    "background: #000000;",
    "background: #0891b2;"
)
content = content.replace(
    "box-shadow: 0 0 0 2px rgba(17, 24, 39, 0.2);",
    "box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.25);"
)
content = content.replace(
    "border-color: #111827;",
    "border-color: #06b6d4;"
)
content = content.replace(
    "background: #f3f4f6;",
    "background: rgba(255,255,255,0.05);"
)
content = content.replace(
    "color: #4b5563;",
    "color: #e5e7eb;"
)
content = content.replace(
    "border: 1px solid #e5e7eb;",
    "border: 1px solid rgba(255,255,255,0.1);"
)
content = content.replace(
    "background: #e5e7eb;",
    "background: rgba(255,255,255,0.1);"
)
content = content.replace(
    "color: #1f2937;",
    "color: #ffffff;"
)

with open(css_file, "w") as f:
    f.write(content)

# We also need to add back the gradient-text class to the JSX if it was removed, or just ensure it applies
with open(jsx_file, "r") as f:
    jsx_content = f.read()
jsx_content = jsx_content.replace('className="hero-title"', 'className="hero-title"\n                        style={{ color: "#ffffff" }}')
with open(jsx_file, "w") as f:
    f.write(jsx_content)

print("Option C: Midnight Hero applied.")
