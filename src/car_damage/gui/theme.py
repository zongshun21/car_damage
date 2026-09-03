from __future__ import annotations


COLORS = {
    "navy": "#0B1F3A",
    "navy_light": "#12345B",
    "primary": "#176BCE",
    "cyan": "#13B8C8",
    "orange": "#F59E0B",
    "bg": "#F3F7FC",
    "card": "#FFFFFF",
    "text": "#17233C",
    "muted": "#6B7A90",
    "border": "#DCE6F2",
    "success": "#19A974",
    "danger": "#E5484D",
}


APP_STYLESHEET = f"""
* {{ font-family: 'Microsoft YaHei UI', 'Microsoft YaHei', sans-serif; }}
QMainWindow, QWidget#AppRoot {{ background: {COLORS['bg']}; color: {COLORS['text']}; }}
QFrame#Sidebar {{ background: {COLORS['navy']}; border: none; }}
QLabel#BrandTitle {{ color: white; font-size: 18px; font-weight: 700; }}
QLabel#BrandSchool {{ color: #9CCBFF; font-size: 12px; }}
QPushButton#NavButton {{
    color: #BFD3EA; background: transparent; border: none; border-radius: 8px;
    text-align: left; padding: 12px 16px; font-size: 14px;
}}
QPushButton#NavButton:hover {{ background: {COLORS['navy_light']}; color: white; }}
QPushButton#NavButton:checked {{ background: {COLORS['primary']}; color: white; font-weight: 600; }}
QFrame#Topbar {{ background: white; border-bottom: 1px solid {COLORS['border']}; }}
QLabel#PageTitle {{ color: {COLORS['text']}; font-size: 22px; font-weight: 700; }}
QLabel#Muted {{ color: {COLORS['muted']}; }}
QFrame#Card {{ background: white; border: 1px solid {COLORS['border']}; border-radius: 12px; }}
QLabel#MetricValue {{ color: {COLORS['text']}; font-size: 26px; font-weight: 700; }}
QLabel#MetricLabel {{ color: {COLORS['muted']}; font-size: 12px; }}
QPushButton {{
    background: {COLORS['primary']}; color: white; border: none; border-radius: 7px;
    padding: 8px 15px; font-weight: 600;
}}
QPushButton:hover {{ background: #0F5DB8; }}
QPushButton:disabled {{ background: #A8B7C9; }}
QPushButton[secondary='true'] {{ background: white; color: {COLORS['primary']}; border: 1px solid #9DC4EE; }}
QPushButton[danger='true'] {{ background: {COLORS['danger']}; }}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background: white; border: 1px solid #C9D8E8; border-radius: 7px; padding: 7px 9px;
    min-height: 20px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {COLORS['primary']}; }}
QTableWidget {{ background: white; border: 1px solid {COLORS['border']}; border-radius: 8px; gridline-color: #EDF2F8; }}
QHeaderView::section {{ background: #EDF4FC; color: #36516F; border: none; border-bottom: 1px solid #D6E2EF; padding: 8px; font-weight: 600; }}
QListWidget {{ background: white; border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 4px; }}
QListWidget::item {{ padding: 8px; border-radius: 5px; }}
QListWidget::item:selected {{ background: #DDEEFF; color: {COLORS['primary']}; }}
QProgressBar {{ border: none; background: #DFE8F2; border-radius: 6px; text-align: center; height: 12px; }}
QProgressBar::chunk {{ background: {COLORS['cyan']}; border-radius: 6px; }}
QTabWidget::pane {{ border: 1px solid {COLORS['border']}; background: white; border-radius: 8px; }}
QTabBar::tab {{ padding: 8px 18px; background: #E7EEF7; margin-right: 2px; }}
QTabBar::tab:selected {{ background: white; color: {COLORS['primary']}; font-weight: 600; }}
QStatusBar {{ background: white; color: {COLORS['muted']}; border-top: 1px solid {COLORS['border']}; }}
"""

