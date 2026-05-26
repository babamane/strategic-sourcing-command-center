import os

css_file = r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src\components\Dashboard.css"

with open(css_file, "r") as f:
    content = f.read()

# Replace hardcoded whites with dark mode slate grays
content = content.replace("rgba(255, 255, 255, 0.7)", "rgba(17, 24, 39, 0.7)")
content = content.replace("rgba(255, 255, 255, 0.8)", "rgba(17, 24, 39, 0.8)")
content = content.replace("rgba(255, 255, 255, 0.9)", "rgba(31, 41, 55, 0.9)")
content = content.replace("rgba(255, 255, 255, 0.95)", "rgba(31, 41, 55, 0.95)")
content = content.replace("rgba(255, 255, 255, 1)", "var(--secondary-bg)")
content = content.replace("background: white;", "background: var(--secondary-bg);")
content = content.replace("background-color: white;", "background-color: var(--secondary-bg);")
content = content.replace("background: #ffffff;", "background: var(--secondary-bg);")
content = content.replace("background-color: #ffffff;", "background-color: var(--secondary-bg);")

# Enhance shadows for dark mode
content = content.replace("rgba(0, 0, 0, 0.03)", "rgba(0, 0, 0, 0.3)")
content = content.replace("rgba(0, 0, 0, 0.04)", "rgba(0, 0, 0, 0.4)")
content = content.replace("rgba(0, 0, 0, 0.05)", "rgba(0, 0, 0, 0.4)")
content = content.replace("rgba(0, 0, 0, 0.06)", "rgba(0, 0, 0, 0.5)")
content = content.replace("rgba(0, 0, 0, 0.08)", "rgba(0, 0, 0, 0.6)")
content = content.replace("rgba(0, 0, 0, 0.1)", "rgba(0, 0, 0, 0.7)")

# Fix specific badges to pop better on dark mode
content = content.replace("background: #fef3c7; color: #d97706;", "background: rgba(217, 119, 6, 0.2); color: #fbbf24;")
content = content.replace("background: rgba(217, 119, 6, 0.05); color: #b45309;", "background: rgba(217, 119, 6, 0.1); color: #fbbf24;")

content = content.replace("background: #ede9fe; color: #7c3aed;", "background: rgba(124, 58, 237, 0.2); color: #a78bfa;")
content = content.replace("background: rgba(124, 58, 237, 0.05); color: #6d28d9;", "background: rgba(124, 58, 237, 0.1); color: #a78bfa;")

content = content.replace("background: #dbeafe; color: #1d4ed8;", "background: rgba(29, 78, 216, 0.2); color: #60a5fa;")
content = content.replace("background: rgba(29, 78, 216, 0.05); color: #1e40af;", "background: rgba(29, 78, 216, 0.1); color: #60a5fa;")

content = content.replace("background: #fee2e2; color: #ef4444;", "background: rgba(239, 68, 68, 0.2); color: #f87171;")
content = content.replace("background: rgba(239, 68, 68, 0.05); color: #b91c1c;", "background: rgba(239, 68, 68, 0.1); color: #f87171;")

content = content.replace("background: #d1fae5; color: #059669;", "background: rgba(16, 185, 129, 0.2); color: #34d399;")
content = content.replace("background: rgba(16, 185, 129, 0.05); color: #047857;", "background: rgba(16, 185, 129, 0.1); color: #34d399;")

with open(css_file, "w") as f:
    f.write(content)
print("Updated Dashboard.css")
