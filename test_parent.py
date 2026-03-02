import sys
from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QHBoxLayout, QFormLayout, QGroupBox

app = QApplication(sys.argv)
group = QGroupBox()
layout = QFormLayout(group)
edit = QLineEdit()
hlayout = QHBoxLayout()
hlayout.addWidget(edit)
layout.addRow("Label:", hlayout)

print("Parent widget of edit:", edit.parentWidget())
print("Expected group:", group)