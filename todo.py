import imaplib
import email
import sys
import sqlite3
import os
import datetime
import pygame
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QDateEdit,
    QLabel,
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QMessageBox,
)
from PySide6.QtCore import QDateTime, QTimer
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtGui import QIcon
from dotenv import load_dotenv
from datetime import datetime
from PySide6.QtCore import Qt

# Load Roboto font files
# QFontDatabase.addApplicationFont("./fonts/Roboto-Regular.ttf")
# QFontDatabase.addApplicationFont("./fonts/Roboto-Bold.ttf")

due_date = 1 / 1 / 2023
current_date = datetime.now()

# Load environment variables from .env file
load_dotenv()

# Retrieve email credentials from environment variables
EMAIL = os.environ.get("EMAIL_USER")
PASSWORD = os.environ.get("EMAIL_PASS")
IMAP_SERVER = os.environ.get("IMAP_URL")


def email_header_decode(header_text):
    """Decode email header text."""
    decoded_header = email.header.decode_header(header_text)
    return " ".join(
        [
            str(text, charset or "utf-8") if isinstance(text, bytes) else text
            for text, charset in decoded_header
        ]
    )


class EditTaskDialog(QDialog):
    def __init__(self, parent=None):
        super(EditTaskDialog, self).__init__(parent)
        self.setWindowTitle("Edit Task")
        self.layout = QVBoxLayout()

        self.task_input = QLineEdit(self)
        self.layout.addWidget(self.task_input)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.accept)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def setTaskText(self, task_text):
        self.task_input.setText(task_text)

    def getEditedTask(self):
        return self.task_input.text()

    def resizeEvent(self, event):
        # Adjust the size of the dialog if needed
        desired_width = 400  # Set your desired width
        desired_height = 200  # Set your desired height
        self.resize(desired_width, desired_height)


class ToDoApp(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize the database
        self.init_db()

        # Initialize the UI
        self.init_ui()

        # Setup email integration
        self.setup_email_integration()

        # Initialize pygame mixer
        pygame.mixer.init()

        # Initialize the QTimer for hourly reminders
        self.hourly_timer = QTimer(self)
        self.hourly_timer.timeout.connect(self.play_hourly_reminder)
        self.hourly_timer.start(3600000)  # 3600000 milliseconds = 1 hour

    def init_db(self):
        self.conn = sqlite3.connect("todo.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            added_date TEXT NOT NULL,
            due_date DATE
        );
        """
        )
        self.conn.commit()

    def init_ui(self):
        # Set the font size for the whole app
        # self.setStyleSheet("font-size: 16px;")
        font = QFont("Roboto", 16)
        self.setFont(font)

        self.layout = QVBoxLayout()

        # Add Task input field
        self.task_input = QLineEdit(self)
        self.task_input.setPlaceholderText("Enter a new task...")
        self.layout.addWidget(self.task_input)

        # Due date input
        self.due_date_label = QLabel("Due Date:", self)
        self.layout.addWidget(self.due_date_label)
        self.due_date_input = QDateEdit(self)
        self.due_date_input.setDate(QDateTime.currentDateTime().date())
        self.due_date_input.setCalendarPopup(True)
        self.layout.addWidget(self.due_date_input)

        # List of tasks
        self.tasks_list = QListWidget(self)
        self.load_tasks()
        self.layout.addWidget(self.tasks_list)

        # Add and Delete buttons
        self.add_btn = QPushButton("Add Task", self)
        self.add_btn.clicked.connect(self.add_task)
        self.layout.addWidget(self.add_btn)

        # Add an "Edit" button to the UI in the init_ui method
        self.edit_btn = QPushButton("Edit Selected Task", self)
        self.edit_btn.clicked.connect(self.edit_task)
        self.layout.addWidget(self.edit_btn)

        self.del_btn = QPushButton("Delete Selected Task", self)
        self.del_btn.clicked.connect(self.delete_task)
        self.layout.addWidget(self.del_btn)

        # Apply Nord color scheme
        self.setStyleSheet(
            """
            QMainWindow {
                font-size: 16px;
                font-family: 'Roboto', sans-serif;
                background-color: #2E3440; /* Polar Night 1 */
                color: #D8DEE9; /* Snow Storm 1 */
            }
            QWidget {
                font-size: 16px;
                font-family: 'Roboto', sans-serif;
                background-color: #2E3440; /* Polar Night 1 */
                color: #D8DEE9; /* Snow Storm 1 */
            }
            QLineEdit, QDateEdit, QListWidget {
                background-color: #3B4252; /* Polar Night 2 */
                color: #D8DEE9; /* Snow Storm 1 */
                border: 1px solid #434C5E; /* Polar Night 3 */
            }
            QPushButton {
                background-color: #88C0D0; /* Frost 1 */
                color: #2E3440; /* Polar Night 1 */
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #81A1C1; /* Frost 2 */
            }
            """
        )

        self.setLayout(self.layout)
        self.setWindowTitle("To-Do App")
        self.setFixedSize(800, 600)

    def load_tasks(self):
        self.tasks_list.clear()
        current_date = QDateTime.currentDateTime().date()
        rows = self.cursor.execute(
            "SELECT task, added_date, due_date FROM tasks"
        ).fetchall()

        # Define the alternating colors
        color1 = QColor("#434C5E")
        color2 = QColor("#4C566A")

        for index, row in enumerate(rows):
            task, added_date, due_date = row
            if due_date:
                due_date_obj = QDateTime.fromString(due_date, "dd/MM/yyyy").date()
                if due_date_obj == current_date:
                    fg_color = "#EBCB8B"
                elif due_date_obj < current_date:
                    fg_color = "#BF616A"
                else:
                    fg_color = "#A3BE8C"
            else:
                fg_color = "#A3BE8C"

            display_text = f"{task} ADDED: {added_date}"
            if due_date:
                display_text += f" | DUE: {due_date}"

            list_item = QListWidgetItem(display_text)
            list_item.setForeground(QColor(fg_color))

            # Set alternating background color
            if index % 2 == 0:
                list_item.setBackground(color1)
            else:
                list_item.setBackground(color2)

            self.tasks_list.addItem(list_item)

    def add_task(self):
        task = self.task_input.text()
        current_time = QDateTime.currentDateTime().toString("dd/MM/yyyy")
        due_date = self.due_date_input.date().toString("dd/MM/yyyy")
        if task:
            self.cursor.execute(
                "INSERT INTO tasks (task, added_date, due_date) VALUES (?, ?, ?)",
                (task, current_time, due_date),
            )
            self.conn.commit()
            self.load_tasks()
            self.task_input.clear()
            self.play_sound()

    def edit_task(self):
        current_item = self.tasks_list.currentItem()
        if current_item:
            task_text = current_item.text().split(" ADDED:")[0]

            edit_dialog = EditTaskDialog(self)
            edit_dialog.setTaskText(task_text)
            if edit_dialog.exec() == QDialog.Accepted:
                new_task = edit_dialog.getEditedTask()
                if new_task:
                    self.cursor.execute(
                        "UPDATE tasks SET task = ? WHERE task = ?",
                        (new_task, task_text),
                    )
                    self.conn.commit()
                    self.load_tasks()

    def delete_task(self):
        current_item = self.tasks_list.currentItem()
        if current_item:
            task_text = current_item.text().split(" ADDED:")[0]
            self.cursor.execute("DELETE FROM tasks WHERE task = ?", (task_text,))
            self.conn.commit()
            self.load_tasks()

    def setup_email_integration(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_email_for_todos)
        self.timer.start(60000)  # check every minute

    def check_email_for_todos(self):
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL, PASSWORD)
            mail.select("inbox")
            status, response = mail.search(None, '(UNSEEN SUBJECT "todo")')
            unread_msg_nums = response[0].split()
            for email_num in unread_msg_nums:
                status, msg_data = mail.fetch(email_num, "(RFC822)")
                email_msg = email.message_from_bytes(msg_data[0][1])
                subject = email_header_decode(email_msg["Subject"])
                task_body = self.get_first_text_block(email_msg)
                due_date = None
                if "," in subject:
                    _, due_date_str = subject.split(",", 1)
                    due_date = (
                        datetime.strptime(due_date_str.strip(), "%d/%m/%Y")
                        .date()
                        .strftime("%d/%m/%Y")
                    )
                self.add_task_from_email(task_body, due_date)
                mail.store(email_num, "+FLAGS", "\\Seen")  # Mark as read
            mail.logout()
        except Exception as e:
            print(f"Error checking email: {e}")

    def get_first_text_block(self, email_message_instance):
        maintype = email_message_instance.get_content_maintype()
        if maintype == "multipart":
            for part in email_message_instance.get_payload():
                if part.get_content_maintype() == "text":
                    return part.get_payload()
        elif maintype == "text":
            return email_message_instance.get_payload()

    def add_task_from_email(self, task, due_date=None):
        if task:
            current_time = QDateTime.currentDateTime().toString("dd/MM/yyyy")
            self.cursor.execute(
                "INSERT INTO tasks (task, added_date, due_date) VALUES (?, ?, ?)",
                (task, current_time, str(due_date)),
            )
            self.conn.commit()
            self.load_tasks()
            self.play_sound()

    def closeEvent(self, event):
        # Override the close event to display a warning message
        reply = QMessageBox.question(
            self,
            "Warning",
            "Are you sure you want to close the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # If the user confirms, close the application
            event.accept()
        else:
            # If the user cancels, ignore the close event
            event.ignore()

    def play_hourly_reminder(self):
        if due_date == current_date:
            hourly_reminder_sound = "notification.wav"
            pygame.mixer.music.load(hourly_reminder_sound)
            pygame.mixer.music.play()

    def play_sound(self):
        sound = "notification.wav"
        pygame.mixer.music.load(sound)
        pygame.mixer.music.play()


def main():
    app = QApplication(sys.argv)
    app_icon = QIcon()
    app_icon.addFile("icon.ico")
    app.setWindowIcon(app_icon)
    window = ToDoApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
