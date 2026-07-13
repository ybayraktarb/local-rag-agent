import json
import os
from src.config import settings

class Theme:
    """
    Data class representing a stylesheet theme instance.
    """
    def __init__(self, name: str, is_dark: bool, colors: dict):
        self.name = name
        self.is_dark = is_dark
        self.colors = colors

# central color palettes (generic naming, brand-free)
LIGHT_COLORS = {
    "primary": "#00693E",       # corporate green
    "accent": "#C9A227",        # accent gold
    "background": "#F5F6F5",    # off-white background
    "surface": "#FFFFFF",       # white card backgrounds
    "text_primary": "#1E1E1E",  # dark charcoal text
    "text_secondary": "#6B6B6B",# gray secondary text
    "border": "#E0E0E0",        # light divider gray
    "success": "#1E824C",       # positive trust green
    "warning": "#D35400",       # warning orange
    "error": "#C0392B",         # low confidence red
    "sidebar_bg": "#ECECEC",    # light gray sidebar
}

DARK_COLORS = {
    "primary": "#2FA86A",       # vibrant light green
    "accent": "#E0B93C",        # vibrant gold
    "background": "#121212",    # dark charcoal background
    "surface": "#1E1E1E",       # dark card backgrounds
    "text_primary": "#F0F0F0",  # light off-white text
    "text_secondary": "#A0A0A0",# light gray secondary text
    "border": "#333333",        # dark divider gray
    "success": "#27AE60",       # bright trust green
    "warning": "#E67E22",       # bright orange
    "error": "#E74C3C",         # bright red
    "sidebar_bg": "#1A1A1A",    # dark sidebar
}

THEMES = {
    "light": Theme("Açık Tema", False, LIGHT_COLORS),
    "dark": Theme("Koyu Tema", True, DARK_COLORS)
}

QSS_TEMPLATE = """
QMainWindow {
    background-color: @background;
    color: @text_primary;
}

QWidget {
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 13px;
    background-color: transparent;
    color: @text_primary;
}

/* Header Bar Styling */
#HeaderBar {
    background-color: @surface;
    border-bottom: 1px solid @border;
}

#AppTitle {
    font-size: 15px;
    font-weight: bold;
    color: @primary;
}

/* Sidebar Panel */
#Sidebar {
    background-color: @sidebar_bg;
    border-right: 1px solid @border;
}

#SidebarTitle {
    font-weight: bold;
    font-size: 12px;
    color: @text_secondary;
    padding: 8px;
    border-bottom: 1px solid @border;
}

QListWidget {
    background-color: transparent;
    border: none;
}

QListWidget::item {
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 4px;
    padding: 6px;
    margin: 4px;
}

QListWidget::item:hover {
    background-color: @background;
}

/* Scroll Area & Chat Stream */
QScrollArea {
    background-color: @background;
    border: none;
}

#ChatStream {
    background-color: @background;
}

/* Chat Card bubble styling */
#ChatCard {
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 6px;
}

#UserQueryLabel {
    font-weight: bold;
    color: @primary;
}

#BotAnswerLabel {
    color: @text_primary;
}

#SourcesLabel {
    font-size: 11px;
    color: @text_secondary;
}

#ConfidenceBadge {
    font-size: 10px;
    font-weight: bold;
    color: #FFFFFF;
    border-radius: 3px;
    padding: 2px 6px;
}

/* Inputs & Actions */
#InputArea {
    background-color: @surface;
    border-top: 1px solid @border;
}

QLineEdit#QueryInput {
    background-color: @background;
    border: 1px solid @border;
    border-radius: 4px;
    padding: 6px;
    color: @text_primary;
}

QLineEdit#QueryInput:focus {
    border: 1px solid @primary;
}

QPushButton {
    background-color: @primary;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: @accent;
}

QPushButton:disabled {
    background-color: @border;
    color: @text_secondary;
}

QPushButton#ThemeToggle {
    background-color: transparent;
    color: @text_secondary;
    border: 1px solid @border;
    border-radius: 3px;
    padding: 3px 8px;
}

QPushButton#ThemeToggle:hover {
    background-color: @background;
    color: @text_primary;
}

QPushButton#ExportButton {
    background-color: transparent;
    color: @primary;
    border: 1px solid @primary;
    border-radius: 3px;
    padding: 3px 10px;
}

QPushButton#ExportButton:hover {
    background-color: @primary;
    color: #FFFFFF;
}

/* Status Bar */
QStatusBar {
    background-color: @surface;
    border-top: 1px solid @border;
    color: @text_secondary;
}
"""

def generate_qss(theme_name: str) -> str:
    """
    Generates QSS stylesheet by substituting variables in template.
    """
    theme = THEMES.get(theme_name, THEMES["light"])
    qss = QSS_TEMPLATE
    for key, val in theme.colors.items():
        qss = qss.replace(f"@{key}", val)
    return qss

SETTINGS_FILE = os.path.join(settings.DB_DIR, "ui_settings.json")

def load_theme_preference() -> str:
    """
    Loads saved UI theme name preference from local settings json.
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                return data.get("theme", "light")
        except:
            pass
    return "light"

def save_theme_preference(theme_name: str):
    """
    Saves theme choice to configuration path.
    """
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"theme": theme_name}, f)
    except:
        pass
