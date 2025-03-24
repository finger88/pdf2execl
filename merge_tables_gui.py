import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog,
                             QVBoxLayout, QWidget, QLabel, QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pdfplumber
import pandas as pd

class PDFProcessThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, pdf_path, output_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path
    
    def run(self):
        try:
            # 从PDF中提取所有表格
            all_tables = []
            
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            df = pd.DataFrame(table[1:], columns=table[0])
                            all_tables.append(df)
                    # 更新进度
                    progress = int((i + 1) / total_pages * 100)
                    self.progress_signal.emit(progress)
            
            if not all_tables:
                self.finished_signal.emit(False, "未在PDF中找到任何表格！")
                return
            
            # 合并所有表格
            merged_df = pd.concat(all_tables, ignore_index=True)
            
            # 删除完全重复的行
            merged_df = merged_df.drop_duplicates()
            
            # 保存到Excel文件
            merged_df.to_excel(self.output_path, index=False)
            self.finished_signal.emit(True, "处理完成！")
            
        except Exception as e:
            self.finished_signal.emit(False, f"处理过程中发生错误：{str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('PDF表格提取工具')
        self.setGeometry(300, 300, 500, 300)
        
        # 创建主窗口部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加说明标签
        intro_label = QLabel('本工具可以从PDF文件中提取所有表格并合并到Excel文件中。\n使用方法：\n1. 点击"选择PDF文件"按钮选择要处理的PDF文件\n2. 点击"选择保存位置"按钮选择输出的Excel文件位置\n3. 点击"开始处理"按钮开始提取表格')
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)
        
        # 添加PDF文件选择按钮和标签
        self.pdf_label = QLabel('未选择PDF文件')
        layout.addWidget(self.pdf_label)
        
        pdf_btn = QPushButton('选择PDF文件', self)
        pdf_btn.clicked.connect(self.select_pdf)
        layout.addWidget(pdf_btn)
        
        # 添加输出文件选择按钮和标签
        self.output_label = QLabel('未选择保存位置')
        layout.addWidget(self.output_label)
        
        output_btn = QPushButton('选择保存位置', self)
        output_btn.clicked.connect(self.select_output)
        layout.addWidget(output_btn)
        
        # 添加进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # 添加开始处理按钮
        self.process_btn = QPushButton('开始处理', self)
        self.process_btn.clicked.connect(self.start_process)
        layout.addWidget(self.process_btn)
    
    def select_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择PDF文件', '', 'PDF文件 (*.pdf)')
        if file_path:
            self.pdf_path = file_path
            self.pdf_label.setText(f'已选择: {os.path.basename(file_path)}')
            
            # 自动设置默认输出路径
            default_output = os.path.splitext(file_path)[0] + '_merged.xlsx'
            self.output_path = default_output
            self.output_label.setText(f'将保存到: {os.path.basename(default_output)}')
    
    def select_output(self):
        file_path, _ = QFileDialog.getSaveFileName(self, '选择保存位置', '', 'Excel文件 (*.xlsx)')
        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            self.output_path = file_path
            self.output_label.setText(f'将保存到: {os.path.basename(file_path)}')
    
    def start_process(self):
        if not self.pdf_path:
            QMessageBox.warning(self, '警告', '请先选择PDF文件！')
            return
        
        if not self.output_path:
            QMessageBox.warning(self, '警告', '请选择保存位置！')
            return
        
        # 禁用按钮
        self.process_btn.setEnabled(False)
        
        # 创建并启动处理线程
        self.process_thread = PDFProcessThread(self.pdf_path, self.output_path)
        self.process_thread.progress_signal.connect(self.update_progress)
        self.process_thread.finished_signal.connect(self.process_finished)
        self.process_thread.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def process_finished(self, success, message):
        self.process_btn.setEnabled(True)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            QMessageBox.information(self, '完成', message)
        else:
            QMessageBox.critical(self, '错误', message)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()