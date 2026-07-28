# EduMind AI – Student Learning Assistant

EduMind AI is a clean, fully-functional, intermediate-level student learning assistant chatbot. It is designed to help students clarify computer science concepts, write and debug code, get placement preparation tips, prepare study schedules, and ask academic queries in both English and Telugu.

This project is built using a lightweight stack suitable for a B.Tech Final Year CSE project, utilizing a Flask backend, SQLAlchemy with a SQLite database, and the Google Gemini API (using the official modern `google-genai` Python SDK).

---

## 🌟 Key Features

1. **User Management**: Secured user registration, login, profile updates, and logout utilizing `Flask-Login` and `Werkzeug` secure password hashing.
2. **AI-Powered Study Chat**: Real Gemini-powered response generations answering queries on programming, databases, network layers, and general syllabus.
3. **Conversational Memory Context**: Maintains a rolling context window of the last 8 messages in the active conversation to support follow-up questions (e.g., "Explain Python lists" followed by "Give me an example").
4. **Chat History Management**: Automatically saves all user and AI responses. Students can search chat titles, open old conversations, continue them, or delete them.
5. **Code & Response Formatting**: Formats code syntax in monospace dark-themed cards, provides a copy-to-clipboard button for AI answers, and formats lists and bold highlights dynamically.
6. **Suggested Questions**: Clickable suggestion cards on new chats to help students start instantly (e.g., "Explain DBMS Normalization").
7. **Personalized Dashboard**: Visual statistics showing total conversations created, total messages exchanged, and a feed of recent chats.
8. **Dark & Light Mode**: Instantly toggle application appearance, synced and persisted via browser `localStorage`.
9. **Responsive Design**: Mobile-friendly sidebar drawer panel, auto-scrolling chats, responsive input areas, and horizontal scrollable code cards.
10. **Backend Security Guards**: Strict ownership check prevent User A from accessing or deleting User B's chats simply by changing the ID in the URL path.

---

## 🛠️ Technology Stack

* **Backend**: Python 3.x, Flask, Flask-SQLAlchemy, Flask-Login, python-dotenv
* **Frontend**: HTML5, CSS3 (Vanilla CSS variables), Vanilla JavaScript, Jinja2 Templates, FontAwesome Icons
* **Database**: SQLite (SQLAlchemy ORM)
* **AI Engine**: Google Gemini API (via modern `google-genai` SDK)

---

## 📂 Project Folder Structure

```text
edumind-ai/
│
├── app.py                  # Main Flask application with routers & security checks
├── models.py               # Database Models (User, Conversation, Message)
├── config.py               # App configuration loaders
├── requirements.txt        # Package dependencies
├── README.md               # User-friendly project documentation
├── .env.example            # Environment variables configuration template
├── .gitignore              # Files ignored by git repository tracking
│
├── services/
│   ├── __init__.py         # Package indicator
│   └── ai_service.py       # Gemini API communication agent & error handler
│
├── templates/
│   ├── base.html           # Core layout header/navbar/footer skeleton
│   ├── index.html          # Professional landing home screen
│   ├── register.html       # Student sign up form
│   ├── login.html          # Student authentication form
│   ├── dashboard.html      # Visual student statistics and shortcuts
│   ├── chat.html           # Main AI Chat UI and suggestions grid
│   ├── profile.html        # Settings details and profile update form
│   └── 404.html            # Error page template
│
└── static/
    ├── css/
    │   └── style.css       # Core styling sheets, color tokens, responsive media queries
    │
    └── js/
        ├── chat.js         # Fetch requests, autoscroll, copy helper, markdown compiler
        └── theme.js        # Theme toggling controller (Dark/Light mode)
```

---

## 🚀 Setup & Installation Instructions

Follow these instructions to run the application on your local machine:

### 1. Prerequisite Installations
* Ensure you have **Python 3.8+** installed. You can check your version in a terminal using:
  ```bash
  python --version
  ```

### 2. Set Up Virtual Environment
Initialize a clean Python virtual environment to manage dependencies locally.

* **On Windows (Command Prompt)**:
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```
* **On macOS/Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies
Run the package installation command to download web and database drivers:
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Keys (`.env`)
1. Create a copy of `.env.example` and rename it to `.env`:
   * **On Windows**: `copy .env.example .env`
   * **On macOS/Linux**: `cp .env.example .env`
2. Open the `.env` file in a text editor and fill in your details:
   ```text
   SECRET_KEY=any_random_secret_string_here
   GEMINI_API_KEY=your_real_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```
   > 💡 **Where to get a Gemini API Key?** Go to [Google AI Studio](https://aistudio.google.com/), log in with your Google account, and click **Create API Key**. It is completely free for study and development.

### 5. Initialize the SQLite Database
The SQLite database tables are automatically initialized during the first application launch. You don't need any manual commands to configure SQLite!

### 6. Run the Application
Start the local Flask development server:
```bash
python app.py
```

Open your browser and navigate to:
👉 **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**

---

## 📈 Future Scope Improvements
For your viva discussion, you can mention these points as future enhancements:
1. **Chat Export**: Allow students to export chat transcript logs as PDF or Markdown text reports.
2. **Text-to-Speech**: Add audio read-outs of Gemini explanations for enhanced accessibility.
3. **Multi-Model Selector**: Support testing and toggling between different sizes of the Gemini models (e.g., Flash vs Pro).
4. **Code Execution Sandbox**: Integrate a lightweight Python runner to run code blocks directly inside the app.
