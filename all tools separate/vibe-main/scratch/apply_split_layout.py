import os
import re

css_file = r"c:\Users\AkankshaKhandare\Downloads\vibe-main\vibe-main\frontend\src\components\CompanySelector.css"

with open(css_file, "r") as f:
    content = f.read()

# Remove old hero-section layout
content = re.sub(
    r'/\* Hero Section \*/\s*\.hero-section\s*{.*?}\s*\.hero-content\s*{.*?}',
    '',
    content,
    flags=re.DOTALL
)

# Add split layout CSS
split_css = """
/* Split Screen Layout */
.split-layout {
    flex: 1;
    display: flex;
    flex-direction: row;
    align-items: center;
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem 4rem;
    gap: 4rem;
    min-height: calc(100vh - 80px);
}

.split-left {
    flex: 1.2;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding-right: 2rem;
}

.split-right {
    flex: 0.8;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.hero-content {
    text-align: left;
}

.hero-badge {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    border-radius: 50px;
    background: rgba(6, 182, 212, 0.1);
    border: 1px solid rgba(6, 182, 212, 0.2);
    color: #06b6d4;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    margin-bottom: 1.5rem;
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 1.5rem;
    color: #ffffff;
    letter-spacing: -1.5px;
}

.hero-subtitle {
    font-size: 1.125rem;
    color: #9ca3af;
    line-height: 1.6;
    max-width: 90%;
}

@media (max-width: 968px) {
    .split-layout {
        flex-direction: column;
        padding: 2rem;
        gap: 2rem;
    }
    .split-left, .split-right {
        flex: 1;
        width: 100%;
        padding-right: 0;
    }
    .hero-title {
        font-size: 2.5rem;
    }
}
"""

content = content + split_css

with open(css_file, "w") as f:
    f.write(content)
print("Split-layout CSS applied.")
