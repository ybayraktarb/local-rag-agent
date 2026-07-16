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

# Slate & Indigo palette
LIGHT_COLORS = {
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "primary_soft": "#EEF2FF",
    "background": "#F8FAFC",
    "surface": "#FFFFFF",
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "border": "#E2E8F0",
    "success": "#16A34A",
    "warning": "#D97706",
    "error": "#DC2626",
    "sidebar_bg": "#F1F5F9",
}

DARK_COLORS = {
    "primary": "#818CF8",
    "primary_hover": "#6366F1",
    "primary_soft": "#312E81",
    "background": "#0F172A",
    "surface": "#1E293B",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "border": "#334155",
    "success": "#4ADE80",
    "warning": "#FBBF24",
    "error": "#F87171",
    "sidebar_bg": "#111C30",
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
    font-family: "Helvetica Neue", "Arial";
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
    font-size: 16px;
    font-weight: 700;
    color: @text_primary;
}

/* Sidebar Panel */
#Sidebar {
    background-color: @sidebar_bg;
    border-right: 1px solid @border;
}

QSplitter::handle {
    background-color: @border;
}

#SidebarTitle {
    font-weight: 700;
    font-size: 11px;
    color: @text_secondary;
    padding: 18px 16px 10px 16px;
    border-bottom: 1px solid @border;
}

QListWidget {
    background-color: transparent;
    border: none;
}

QLineEdit#DocumentSearch {
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 8px;
    margin: 10px 10px 6px 10px;
    padding: 8px 10px;
    color: @text_primary;
}

QLineEdit#DocumentSearch:focus {
    border: 1px solid @primary;
}

QListWidget::item {
    background-color: transparent;
    border: none;
    border-radius: 7px;
    padding: 9px 10px;
    margin: 2px 8px;
}

QListWidget::item:hover {
    background-color: @primary_soft;
    color: @primary;
}

QListWidget::item:selected {
    background-color: @primary_soft;
    color: @primary;
}

#DocumentDetails {
    background-color: @surface;
    border-top: 1px solid @border;
}

#DocumentDetailName {
    color: @text_primary;
    font-size: 12px;
    font-weight: 700;
}

#DocumentDetailMeta {
    color: @text_secondary;
    font-size: 11px;
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
    border-radius: 12px;
}

#UserQueryLabel {
    font-size: 14px;
    font-weight: 700;
    color: @text_primary;
}

#BotAnswerLabel {
    color: @text_primary;
    line-height: 1.45;
}

#SourceChip {
    font-size: 12px;
    color: @text_secondary;
    background-color: @background;
    border: 1px solid @border;
    border-radius: 9px;
    padding: 3px 7px;
    font-weight: 500;
}

#SourceChip:hover {
    color: @primary;
    border-color: @primary;
}

#AssistantWelcomeBubble {
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 12px;
}

#AssistantLabel {
    color: @primary;
    font-size: 11px;
    font-weight: 700;
}

#WelcomeMessage {
    color: @text_primary;
    font-size: 14px;
}

#LoadingPanel {
    background-color: @surface;
    border-bottom: 1px solid @border;
}

QProgressBar {
    background-color: @border;
    border: none;
    border-radius: 2px;
    max-height: 4px;
}

QProgressBar::chunk {
    background-color: @primary;
    border-radius: 2px;
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
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 9px;
    padding: 10px 12px;
    color: @text_primary;
    selection-background-color: @primary;
}

QLineEdit#QueryInput:focus {
    border: 1px solid @primary;
}

QPushButton {
    background-color: @primary;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 700;
}

QPushButton:hover {
    background-color: @primary_hover;
}

QPushButton:disabled {
    background-color: @border;
    color: @text_secondary;
}

QPushButton#DocumentsButton, QPushButton#NewChatButton, QPushButton#SettingsButton, QPushButton#CopyButton {
    background-color: transparent;
    color: @text_secondary;
    border: 1px solid @border;
    border-radius: 8px;
    padding: 7px 11px;
}

QPushButton#DocumentsButton:hover, QPushButton#NewChatButton:hover, QPushButton#SettingsButton:hover, QPushButton#CopyButton:hover {
    background-color: @background;
    color: @text_primary;
}

QPushButton#CopyButton {
    padding: 4px 8px;
    font-size: 11px;
}

#SettingsPopover {
    background-color: @surface;
    border: 1px solid @border;
    border-radius: 10px;
}

#SettingsSectionTitle {
    color: @text_secondary;
    font-size: 11px;
    font-weight: 700;
}

#SystemStatusCard {
    background-color: @background;
    border: 1px solid @border;
    border-radius: 9px;
}

#SystemStatusDot {
    background-color: @warning;
    border: none;
    border-radius: 4px;
}

#SystemStatusDot[state="ready"] {
    background-color: @success;
}

#SystemStatusDot[state="error"] {
    background-color: @error;
}

#SystemStatusValue {
    color: @text_primary;
    font-weight: 700;
}

#SystemStatusDescription {
    color: @text_secondary;
    font-size: 11px;
}

#SettingsSeparator {
    color: @border;
    background-color: @border;
    max-height: 1px;
}

#ThemeSelector {
    background-color: @background;
    border: 1px solid @border;
    border-radius: 9px;
}

QPushButton#ThemeOption {
    background-color: transparent;
    color: @text_secondary;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton#ThemeOption:hover {
    background-color: @primary_soft;
    color: @primary;
}

QPushButton#ThemeOption:checked {
    background-color: @primary;
    color: #FFFFFF;
}

QPushButton#ThemeOption:focus {
    border: 1px solid @primary;
}

QPushButton#PopoverExportButton, QPushButton#OpenDocumentButton {
    background-color: transparent;
    color: @text_secondary;
    border: 1px solid @border;
    padding: 7px 10px;
}

QPushButton#PopoverExportButton:hover, QPushButton#OpenDocumentButton:hover {
    background-color: @primary_soft;
    color: @primary;
    border-color: @primary;
}

/* Status Bar */
QStatusBar {
    background-color: @surface;
    border-top: 1px solid @border;
    color: @text_secondary;
    padding: 3px 8px;
}
"""

def generate_qss(theme_name: str) -> str:
    """
    Generates QSS stylesheet by substituting variables in template.
    """
    theme = THEMES.get(theme_name, THEMES["light"])
    qss = QSS_TEMPLATE
    # Replace longer tokens first (e.g. primary_hover before primary).
    for key in sorted(theme.colors, key=len, reverse=True):
        val = theme.colors[key]
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
