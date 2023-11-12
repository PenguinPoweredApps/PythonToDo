# ToDo App

## Overview

The ToDo App is a simple and intuitive desktop application designed to help users manage their tasks efficiently. Written in Python with PySide6, this app offers a traditional to-do list experience with an innovative twist — the ability to receive tasks via email from co-workers or family members. The application aims to streamline task management and enhance user productivity by providing timely notifications and a pleasant user experience.

## Features

1. **Traditional To-Do List:**

   - Create tasks easily with a completion by date. Colour coded to ease identification at a glance.
   - All tasks are stored in a SQLite database for reliable day to day use.
   - Delete tasks on completion.

2. **Email Integration:**

   - Receive tasks via email from co-workers or family members.
   - Automatically adds emailed tasks to your to-do list.

3. **Notification Sound:**

   - Get notified with a friendly sound on the receipt of new tasks.
   - Hourly reminders for existing tasks to ensure nothing gets overlooked.

4. **User-Friendly Interface:**
   - Intuitive design for a smooth user experience.
   - Easy navigation and quick access to essential features.

## Installation

To run the ToDo App, ensure you have Python and PySide6 installed on your machine. You can install the necessary dependencies using the following command:

```bash
pip install PySide6 pygame dotenv
```

Clone the ToDo App repository to your local machine:

```bash
git clone https://github.com/PenguinPoweredApps/PythonToDo.git
cd PythonToDo
```

Run the application:

```bash
python todo.py
```

## Usage

1. **Adding Tasks:**

   - Fill in the task details, completion date and click "Add Task" to include it in your to-do list.

2. **Email Integration:**

   - Configure your email settings in the .env file.
   - Receive tasks automatically by email effortlessly.

3. **Notifications:**

   - Enjoy a notification sound on the receipt of new tasks.
   - Hourly reminders will keep you on track with your existing tasks.

4. **Task Management:**
   - Add or delete tasks as needed.
   - Delete tasks on completion to maintain an organized task list.

## Configuration

To set up your email integration, navigate to the .env file in the app. Enter your email credentials and mail server address.
Configure your email settings in a .env file, in the format as below.

EMAIL_USER=username
EMAIL_PASS=password
IMAP_URL=imap.example.com

## Contributing

If you would like to contribute to the development of the ToDo App, feel free to fork the repository and submit a pull request. Bug reports and feature requests are welcome in the "Issues" section.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any inquiries or assistance, please contact the project maintainer at [info@penguinpowered.co.uk](mailto:info@penguinpowered.co.uk).

Happy task managing! 🚀
