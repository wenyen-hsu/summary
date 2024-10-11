import sys
import pyperclip
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal
import concurrent.futures  # 用於超時處理
import ollama
import time


class SummarizeThread(QThread):
    # 定義信號來發送摘要結果或錯誤訊息
    summary_ready = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        # 使用 concurrent.futures 來設置超時機制
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self.summarize, self.text)
            try:
                result = future.result(timeout=300)  # 設置超時 120 秒
                self.summary_ready.emit(result)
            except concurrent.futures.TimeoutError:
                self.error_signal.emit("The request timed out. Please try again.")

    def summarize(self, text):
        # 模型摘要請求部分
        prompt = f"Please provide an outline and summary for the following text:\n\n{text}\n\nOutline:\n\nSummary:"
        try:
            response = ollama.chat(model='llama3', messages=[
                {
                    'role': 'user',
                    'content': prompt,
                }
            ])
            return response['message']['content']
        except Exception as e:
            return str(e)


class TextSummarizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Text Summarizer')
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Summarize button
        self.summarize_button = QPushButton('Summarize from Clipboard')
        self.summarize_button.clicked.connect(self.summarize_from_clipboard)
        layout.addWidget(self.summarize_button)

        # Result label
        self.result_label = QLabel("Summary will appear here.")
        layout.addWidget(self.result_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        central_widget.setLayout(layout)

    def summarize_from_clipboard(self):
        # 獲取剪貼簿中的文字
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            print(f"Current clipboard content: {clipboard_content[:50]}...")  # 顯示前 50 個字符
        else:
            self.result_label.setText("Clipboard is empty.")
            return

        # 清空剪貼簿
        pyperclip.copy('')  # 清空剪貼簿
        print("Clipboard has been cleared.")

        # 繼續摘要操作，限制文字長度
        text = clipboard_content
        max_length = 1000
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # 創建一個執行緒來處理摘要生成
        self.thread = SummarizeThread(text)
        self.thread.summary_ready.connect(self.display_summary)
        self.thread.error_signal.connect(self.display_error)
        self.thread.progress_signal.connect(self.update_progress_bar)
        self.thread.start()

        # 在等待時可以提示正在處理
        self.result_label.setText("Summarizing...")
        self.progress_bar.setValue(0)  # 重置進度條

    def display_summary(self, result):
        self.result_label.setText(f"Summary: {result}")
        self.progress_bar.setValue(100)  # 完成進度條

    def display_error(self, error):
        self.result_label.setText(f"Error: {error}")
        self.progress_bar.setValue(0)  # 進度條重置

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)


def main():
    app = QApplication(sys.argv)
    ex = TextSummarizerApp()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()



#another terminal to run ollama llama3
#execute .py
#make sure choose words and use ctrl c