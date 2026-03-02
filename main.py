import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import log

def main():
    """
    Entry point for the application.
    Initializes the PySide6 app, creates the main window, and executes the event loop.
    All Dependency Injection is lazily resolved when start is pressed inside the GUI.
    """
    log.info("--- Starting DBF to CSV Consolidator App ---")
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # To give it a modern look across OS
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
