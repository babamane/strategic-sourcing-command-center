import os
from pathlib import Path
import re

frontend_src = Path(r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src")
components_dir = frontend_src / "components"

# 1. Update index.css to Premium Midnight Dark Mode
midnight_index = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  /* Premium Midnight Dark Mode Tokens */
  --bg-color: #0b0f19;
  --secondary-bg: #111827;
  --text-color: #f3f4f6;
  --text-secondary: #9ca3af;
  --accent-color: #06b6d4;
  --accent-hover: #0891b2;
  --border-color: rgba(255, 255, 255, 0.1);
  --card-hover: rgba(255, 255, 255, 0.03);
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  
  /* Additional shadow and radius tokens */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
  --radius-md: 0.75rem;
  --radius-lg: 1rem;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background-color: var(--bg-color);
  color: var(--text-color);
  font-family: var(--font-family);
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}
a { text-decoration: none; color: inherit; }
ul { list-style: none; }

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }
"""
(frontend_src / "index.css").write_text(midnight_index)

# 2. Update Dashboard.css
dashboard_path = components_dir / "Dashboard.css"
if dashboard_path.exists():
    content = dashboard_path.read_text()
    
    # Re-apply dark backgrounds
    content = content.replace("background-color: white;", "background-color: var(--secondary-bg);")
    content = content.replace("background: white;", "background: var(--secondary-bg);")
    content = content.replace("background: #ffffff;", "background: var(--secondary-bg);")
    
    # Re-apply glassmorphism for topic cards
    content = re.sub(
        r'\.topic-card\s*{[^}]+}', 
        '.topic-card {\n    background: rgba(17, 24, 39, 0.7);\n    backdrop-filter: blur(12px);\n    -webkit-backdrop-filter: blur(12px);\n    border-radius: 16px;\n    border: 1px solid var(--border-color);\n    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);\n    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);\n    overflow: hidden;\n    display: flex;\n    flex-direction: row;\n    align-items: stretch;\n    min-height: 120px;\n}', 
        content
    )
    
    content = re.sub(
        r'\.topic-card:hover\s*{[^}]+}', 
        '.topic-card:hover {\n    transform: translateY(-2px);\n    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);\n    background: rgba(31, 41, 55, 0.95);\n}', 
        content
    )
    
    # Revert topic badges to neon dark mode colors
    content = re.sub(r'\.border-amber\s*{[^}]+}', '.border-amber { border-color: rgba(217, 119, 6, 0.2); }', content)
    content = re.sub(r'\.bg-amber-soft\s*{[^}]+}', '.bg-amber-soft { background: rgba(217, 119, 6, 0.1); }', content)
    content = re.sub(r'\.amber-badge\s*{[^}]+}', '.amber-badge { background: rgba(217, 119, 6, 0.2); color: #fbbf24; }', content)
    content = re.sub(r'\.text-amber\s*{[^}]+}', '.text-amber { color: #fbbf24; }', content)
    content = re.sub(r'\.bg-amber-bubble\s*{[^}]+}', '.bg-amber-bubble { background: rgba(217, 119, 6, 0.1); color: #fbbf24; }', content)

    content = re.sub(r'\.border-purple\s*{[^}]+}', '.border-purple { border-color: rgba(124, 58, 237, 0.2); }', content)
    content = re.sub(r'\.bg-purple-soft\s*{[^}]+}', '.bg-purple-soft { background: rgba(124, 58, 237, 0.1); }', content)
    content = re.sub(r'\.purple-badge\s*{[^}]+}', '.purple-badge { background: rgba(124, 58, 237, 0.2); color: #a78bfa; }', content)
    content = re.sub(r'\.text-purple\s*{[^}]+}', '.text-purple { color: #a78bfa; }', content)
    content = re.sub(r'\.bg-purple-bubble\s*{[^}]+}', '.bg-purple-bubble { background: rgba(124, 58, 237, 0.1); color: #a78bfa; }', content)

    content = re.sub(r'\.border-blue\s*{[^}]+}', '.border-blue { border-color: rgba(29, 78, 216, 0.2); }', content)
    content = re.sub(r'\.bg-blue-soft\s*{[^}]+}', '.bg-blue-soft { background: rgba(29, 78, 216, 0.1); }', content)
    content = re.sub(r'\.blue-badge\s*{[^}]+}', '.blue-badge { background: rgba(29, 78, 216, 0.2); color: #60a5fa; }', content)
    content = re.sub(r'\.text-blue\s*{[^}]+}', '.text-blue { color: #60a5fa; }', content)
    content = re.sub(r'\.bg-blue-bubble\s*{[^}]+}', '.bg-blue-bubble { background: rgba(29, 78, 216, 0.1); color: #60a5fa; }', content)

    content = re.sub(r'\.border-coral\s*{[^}]+}', '.border-coral { border-color: rgba(239, 68, 68, 0.2); }', content)
    content = re.sub(r'\.bg-coral-soft\s*{[^}]+}', '.bg-coral-soft { background: rgba(239, 68, 68, 0.1); }', content)
    content = re.sub(r'\.coral-badge\s*{[^}]+}', '.coral-badge { background: rgba(239, 68, 68, 0.2); color: #f87171; }', content)
    content = re.sub(r'\.text-coral\s*{[^}]+}', '.text-coral { color: #f87171; }', content)
    content = re.sub(r'\.bg-coral-bubble\s*{[^}]+}', '.bg-coral-bubble { background: rgba(239, 68, 68, 0.1); color: #f87171; }', content)

    content = re.sub(r'\.border-emerald\s*{[^}]+}', '.border-emerald { border-color: rgba(16, 185, 129, 0.2); }', content)
    content = re.sub(r'\.bg-emerald-soft\s*{[^}]+}', '.bg-emerald-soft { background: rgba(16, 185, 129, 0.1); }', content)
    content = re.sub(r'\.emerald-badge\s*{[^}]+}', '.emerald-badge { background: rgba(16, 185, 129, 0.2); color: #34d399; }', content)
    content = re.sub(r'\.text-emerald\s*{[^}]+}', '.text-emerald { color: #34d399; }', content)
    content = re.sub(r'\.bg-emerald-bubble\s*{[^}]+}', '.bg-emerald-bubble { background: rgba(16, 185, 129, 0.1); color: #34d399; }', content)

    dashboard_path.write_text(content)

# 3. Update Sidebar.css
sidebar_path = components_dir / "Sidebar.css"
if sidebar_path.exists():
    content = sidebar_path.read_text()
    content = content.replace("background-color: #e8f0fe;", "background-color: rgba(255, 255, 255, 0.05);")
    content = content.replace("color: #1a73e8;", "color: var(--accent-color);")
    content = content.replace("border: none;", "border: 1px solid var(--border-color);")
    content = content.replace("box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);", "box-shadow: 0 4px 12px rgba(6, 182, 212, 0.35);")
    sidebar_path.write_text(content)

# 4. AppCard.css (Fix the tag backgrounds)
app_card_path = components_dir / "AppCard.css"
if app_card_path.exists():
    content = app_card_path.read_text()
    content = content.replace("background-color: #f1f3f4;", "background-color: rgba(255, 255, 255, 0.05);")
    content = content.replace("border: 1px solid #dadce0;", "border: none;")
    app_card_path.write_text(content)

# 5. Fix remaining components
for fname in ["PromptSettingsModal.css", "ChatWidget.css"]:
    fpath = components_dir / fname
    if fpath.exists():
        content = fpath.read_text()
        content = content.replace("background: white;", "background: var(--secondary-bg);")
        content = content.replace("background-color: white;", "background-color: var(--secondary-bg);")
        fpath.write_text(content)

print("Applied Global Midnight Theme completely.")
