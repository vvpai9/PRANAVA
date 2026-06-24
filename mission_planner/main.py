import sys
from PyQt5.QtWidgets import QApplication
from chatbot_ui import ChatbotUI

def main():
    app = QApplication(sys.argv)
    window = ChatbotUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
