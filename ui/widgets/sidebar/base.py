from PyQt5.QtWidgets import QWidget, QVBoxLayout
from .panels import LocationPreviewPanel, SettingsPanel, SourcesPanel

class SidebarWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.locationPreveiwWidget = LocationPreviewPanel()
        self.settingsWidget        = SettingsPanel()
        self.sourceWidget          = SourcesPanel()

        layout.addWidget(self.locationPreveiwWidget, stretch=3)
        layout.addWidget(self.settingsWidget, stretch=3)
        layout.addWidget(self.sourceWidget, stretch=4)