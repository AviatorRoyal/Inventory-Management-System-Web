🧮 Inventory Management System – Shree Dwarka Agency
A lightweight Flask-based web application to manage shop inventory with features like stock tracking, user access control, item movement logs, and grouped batch entries.

🔧 Setup Instructions

1. Clone the Repository

git clone https://github.com/yourusername/Inventory-Management-System-Web.git
cd Inventory-Management-System-Web

2. Set Up a Virtual Environment

python3 -m venv venv
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

4. Start the Server (Production with Gunicorn)

gunicorn --timeout 90 --bind 0.0.0.0:8000 app:app

🛑 Stopping the Server

# Option 1 – Kill port 8000
sudo fuser -k 8000/tcp

# Option 2 – Kill all gunicorn processes
pkill gunicorn

🖥️ Server Utilities

# Check disk space
df -h

🛠️ Git Commands

Task	Command
Fetch all from GitHub	git fetch origin
List all branches	git branch -a
Track and checkout remote branch	git checkout -u origin/<branch_name>
Switch to a branch	git checkout <branch_name>
Delete a branch	git branch -d <branch_name>
Pull latest changes	git pull
Restore a file	git restore app.py

📂 Project Structure
csharp
Copy
Edit
Inventory-Management-System-Web/
├── app.py                   # Main Flask app
├── templates/               # HTML templates
├── static/
│   └── uploads/             # Uploaded item photos
├── inventory.db             # SQLite database
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── venv/                    # Python virtual environment
🔐 Login Credentials
Default Admin Username: Admin

Password: Bhaskar123

Access Levels:

🛠️ Admin – Full access

✍️ Write – Add/edit items & stock

👁️ Read – View only

✨ Features

📦 Add/Edit/Delete items with optional photo

🔄 Track Incoming and Outgoing stock entries

🧠 Autocomplete suggestions for items and types

🧾 Group-wise entry and editing

👥 User login system with access levels

📜 License
This project is licensed under the MIT License. See LICENSE for details.

