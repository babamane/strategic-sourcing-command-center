import os
import re

css_file = r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src\components\Dashboard.css"

with open(css_file, "r") as f:
    content = f.read()

# Force all h1, h2, h3, h4 tags to use --text-color in the dashboard container if they don't already
# Let's just find specific known bad colors and replace them
content = re.sub(r'color:\s*#1a73e8;', 'color: var(--accent-color);', content)
content = re.sub(r'color:\s*#444;', 'color: var(--text-color);', content)
content = re.sub(r'color:\s*#333;', 'color: var(--text-color);', content)
content = re.sub(r'color:\s*#222;', 'color: var(--text-color);', content)
content = re.sub(r'color:\s*#000;', 'color: var(--text-color);', content)
content = re.sub(r'color:\s*black;', 'color: var(--text-color);', content)

# Check accordion title group explicitly
content = re.sub(
    r'\.accordion-title-group\s*h3\s*{[^}]+}', 
    '.accordion-title-group h3 {\n    margin: 0;\n    font-size: 1.15rem;\n    font-weight: 700;\n    color: var(--text-color);\n    letter-spacing: -0.2px;\n}', 
    content
)

# Highlights text h3
content = re.sub(
    r'\.highlights-text\s*h3[^}]*{[^}]+}', 
    '.highlights-text h3, .summary-content-text h3 {\n    font-size: 1.1rem;\n    color: var(--text-color);\n    margin-top: 1.5rem;\n    margin-bottom: 0.75rem;\n}', 
    content
)

# Card titles
content = re.sub(
    r'\.card-header\s*h3\s*{[^}]+}', 
    '.card-header h3 {\n    margin: 0;\n    font-size: 1.1rem;\n    font-weight: 700;\n    color: var(--text-color);\n    letter-spacing: -0.2px;\n}', 
    content
)

# Add a catch-all at the end
content += """
/* Catch all for dark mode text */
.dashboard-container h1,
.dashboard-container h2,
.dashboard-container h3,
.dashboard-container h4,
.dashboard-container strong,
.dashboard-container b {
    color: var(--text-color);
}
"""

with open(css_file, "w") as f:
    f.write(content)
print("Updated h3 text colors.")
