# 🧮 Inventory Management System – Shree Dwarka Agency
A lightweight Flask-based web application to manage shop inventory with features like stock tracking, user access control, item movement logs, and grouped batch entries.

# 🔧 Setup Instructions

1. Clone the Repository

```sh
git clone https://github.com/yourusername/Inventory-Management-System-Web.git
cd Inventory-Management-System-Web
```

2. Set Up a Virtual Environment

```sh
python3 -m venv venv
source venv/bin/activate
```

3. Install Dependencies

```sh
pip install -r requirements.txt
```
4. Start the Server (Production with Gunicorn)
```sh
gunicorn --timeout 90 --bind 0.0.0.0:8000 app:app
```
🛑 Stopping the Server

 - Option 1 – Kill port 8000
`sudo fuser -k 8000/tcp`

 - Option 2 – Kill all gunicorn processes
`pkill gunicorn`

🖥️ Server Utilities

 - Check disk space
`df -h`

🛠️ Git Commands

<table>
  <thead>
    <tr>
      <th>Command</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>git clone &lt;url&gt;</code></td>
      <td>Clone a remote repository</td>
    </tr>
    <tr>
      <td><code>git status</code></td>
      <td>Check the current status of the working directory</td>
    </tr>
    <tr>
      <td><code>git add &lt;file&gt;</code></td>
      <td>Stage changes for commit</td>
    </tr>
    <tr>
      <td><code>git commit -m "message"</code></td>
      <td>Commit staged changes with a message</td>
    </tr>
    <tr>
      <td><code>git push</code></td>
      <td>Push committed changes to remote repository</td>
    </tr>
    <tr>
      <td><code>git pull</code></td>
      <td>Fetch and merge changes from remote</td>
    </tr>
    <tr>
      <td><code>git branch</code></td>
      <td>List all local branches</td>
    </tr>
    <tr>
      <td><code>git branch &lt;name&gt;</code></td>
      <td>Create a new branch</td>
    </tr>
    <tr>
      <td><code>git checkout &lt;branch&gt;</code></td>
      <td>Switch to a different branch</td>
    </tr>
    <tr>
      <td><code>git merge &lt;branch&gt;</code></td>
      <td>Merge a branch into the current branch</td>
    </tr>
    <tr>
      <td><code>git fetch</code></td>
      <td>Download changes from remote (but don’t merge)</td>
    </tr>
    <tr>
      <td><code>git remote -v</code></td>
      <td>View remote repository URLs</td>
    </tr>
    <tr>
      <td><code>git log --oneline</code></td>
      <td>Show commit history in compact form</td>
    </tr>
    <tr>
      <td><code>git reset --hard &lt;commit&gt;</code></td>
      <td>Reset current branch to a specific commit (destructive)</td>
    </tr>
    <tr>
      <td><code>git stash</code></td>
      <td>Temporarily save uncommitted changes</td>
    </tr>
    <tr>
      <td><code>git stash pop</code></td>
      <td>Apply the most recent stash</td>
    </tr>
  </tbody>
</table>


📂 Project Structure
```
Inventory-Management-System-Web/
├── app.py                   # Main Flask app
├── templates/               # HTML templates
├── static/
│   └── uploads/             # Uploaded item photos
├── inventory.db             # SQLite database
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── venv/                    # Python virtual environment
```

🔐 Login Credentials

 - Default Admin Username: Admin
 - Access Levels:

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

