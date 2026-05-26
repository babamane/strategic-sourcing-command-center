import os

css_file = r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src\components\CompanySelector.css"

with open(css_file, "r") as f:
    content = f.read()

# 1. Update landing page background to a dot-grid
content = content.replace(
    "background-color: var(--bg-color);", 
    "background-color: #ffffff;\n    background-image: radial-gradient(#e5e7eb 1px, transparent 1px);\n    background-size: 24px 24px;"
)

# 2. Update Header
content = content.replace(
    "background: var(--secondary-bg);", 
    "background: rgba(255, 255, 255, 0.8);"
)
content = content.replace(
    "backdrop-filter: blur(10px);",
    "backdrop-filter: blur(12px);\n    -webkit-backdrop-filter: blur(12px);"
)

# 3. Update Hero Title and Gradient Text to Monochromatic
content = content.replace(
    "color: var(--accent-color);\n    background: linear-gradient(135deg, var(--accent-color) 0%, #a855f7 100%);",
    "color: #111827;\n    background: linear-gradient(135deg, #111827 0%, #4b5563 100%);"
)

# 4. Update the Selection Form card (Glassmorphic)
content = content.replace(
    "box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);",
    "box-shadow: 0 10px 40px -10px rgba(0,0,0,0.08);\n    backdrop-filter: blur(16px);\n    -webkit-backdrop-filter: blur(16px);"
)

# 5. Update primary buttons (Login, View Briefing)
# Sign Up
content = content.replace(
    "background: var(--accent-color);",
    "background: #111827;"
)
content = content.replace(
    "border-radius: 24px;",
    "border-radius: 6px;"
)
content = content.replace(
    "box-shadow: 0 4px 12px rgba(66, 133, 244, 0.3);",
    "box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);"
)
content = content.replace(
    "background: var(--accent-hover);",
    "background: #000000;"
)

# View Briefing
content = content.replace(
    "box-shadow: 0 4px 12px rgba(66, 133, 244, 0.35);",
    "box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);"
)
content = content.replace(
    "box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.15);",
    "box-shadow: 0 0 0 2px rgba(17, 24, 39, 0.2);"
)
content = content.replace(
    "border-color: var(--accent-color);",
    "border-color: #111827;"
)

# Other accents
content = content.replace(
    "color: var(--accent-color);",
    "color: #111827;"
)

with open(css_file, "w") as f:
    f.write(content)
print("Option B: Glass & Grid applied to CompanySelector.css")
