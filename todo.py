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
    QMessageBox,
)
from PySide6.QtCore import QDateTime, QTimer
from PySide6.QtGui import QColor
from PySide6.QtGui import QIcon
from dotenv import load_dotenv

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

        self.del_btn = QPushButton("Delete Selected Task", self)
        self.del_btn.clicked.connect(self.delete_task)
        self.layout.addWidget(self.del_btn)

        self.setLayout(self.layout)
        self.setWindowTitle("To-Do App")
        self.resize(800, 600)

    # Play a sound when a new task is added
    def play_sound(self):
        pygame.mixer.music.load("notification.wav")
        pygame.mixer.music.play()

    def load_tasks(self):
        self.tasks_list.clear()
        current_date = QDateTime.currentDateTime().date()
        rows = self.cursor.execute(
            "SELECT task, added_date, due_date FROM tasks"
        ).fetchall()

        # Define the alternating colors
        color1 = QColor("#f2f2f2")
        color2 = QColor("#e6e6e6")

        for index, row in enumerate(rows):
            task, added_date, due_date = row
            if due_date:
                due_date_obj = QDateTime.fromString(due_date, "dd/MM/yyyy").date()
                if due_date_obj == current_date:
                    fg_color = "orange"
                elif due_date_obj < current_date:
                    fg_color = "red"
                else:
                    fg_color = "green"
            else:
                fg_color = "green"

            display_text = f"{task} (Added: {added_date})"
            if due_date:
                display_text += f" | Due: {due_date}"

            list_item = QListWidgetItem(display_text)
            list_item.setForeground(QColor(fg_color))

            # Set alternating background color
            if index % 2 == 0:
                list_item.setBackground(color1)
            else:
                list_item.setBackground(color2)

            self.tasks_list.addItem(list_item)

            # Play notification every hour if there are tasks due
            if due_date_obj == current_date:
                if current_date.hour % 1 == 0:
                    self.play_sound()

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
            # self.play_sound()

    def delete_task(self):
        current_item = self.tasks_list.currentItem()
        if current_item:
            task_text = current_item.text().split(" (Added:")[0]
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
                        datetime.datetime.strptime(due_date_str.strip(), "%d/%m/%Y")
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
