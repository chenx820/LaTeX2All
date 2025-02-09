import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog, QComboBox, QLabel
from latex2html.latex2html import convert_latex_to_html


def save_to_file(content, file_type):
    file_name, _ = QFileDialog.getSaveFileName(None, "保存文件", "", f"{file_type} Files (*.{file_type.lower()});;All Files (*)")
    if file_name:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(content)

class LatexConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.latex_content = None
        self.converted_content = None

    def initUI(self):
        layout = QVBoxLayout()
        
        self.label = QLabel("选择 LaTeX 文件:")
        layout.addWidget(self.label)
        
        self.button_open = QPushButton("打开文件")
        self.button_open.clicked.connect(self.open_file)
        layout.addWidget(self.button_open)
        
        self.combo_format = QComboBox()
        self.combo_format.addItems(["Text", "Markdown", "HTML"])
        layout.addWidget(self.combo_format)
        
        self.button_convert = QPushButton("转换")
        self.button_convert.clicked.connect(self.convert_file)
        layout.addWidget(self.button_convert)
        
        self.text_output = QTextEdit()
        layout.addWidget(self.text_output)
        
        self.button_save = QPushButton("导出文件")
        self.button_save.clicked.connect(self.save_file)
        layout.addWidget(self.button_save)
        
        self.setLayout(layout)
        self.setWindowTitle("LaTeX 转换工具")
        self.resize(600, 400)
    
    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择 LaTeX 文件", "", "LaTeX Files (*.tex);;All Files (*)")
        if file_name:
            with open(file_name, "r", encoding="utf-8") as file:
                self.latex_content = file.read()
                self.label.setText(f"已选择: {file_name}")
    
    def convert_file(self):
        if hasattr(self, 'latex_content'):
            format_type = self.combo_format.currentText()
            
            if  format_type == "HTML":
                self.converted_content = convert_latex_to_html(self.latex_content)
            else:
                self.converted_content = "功能还没写完！"
            
            self.text_output.setText(self.converted_content)
        else:
            self.text_output.setText("请先选择一个 LaTeX 文件！")

    def save_file(self):
        if self.combo_format.currentText().lower() == "text":
            format_type = "txt"
        elif self.combo_format.currentText().lower() == "markdown":
            format_type = "md"
        elif self.combo_format.currentText().lower() == "html":
            format_type = "html"
        else:
            raise ValueError("Unknown format type")
        save_to_file(self.converted_content, format_type)

if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = LatexConverterApp()
    window.show()
    sys.exit(app.exec())

