import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Conversation, Message
from services.ai_service import AIService

# Create Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'
login_manager.init_app(app)

# Initialize Gemini AI Service
ai_service = AIService()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_now():
    return {'datetime': datetime}

# Ensure database tables are created
with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def index():
    """Public landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student Registration Route."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation
        if not all([full_name, username, email, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        # Check duplicate username
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            flash('Username is already taken. Please choose another one.', 'danger')
            return render_template('register.html')

        # Check duplicate email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email is already registered. Please choose another one.', 'danger')
            return render_template('register.html')

        # Create new user and hash password
        new_user = User(full_name=full_name, username=username, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            print(f"Register Error: {e}")

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Student Login Route."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip() # can be username or email
        password = request.form.get('password')

        if not identifier or not password:
            flash('Please enter both email/username and password.', 'danger')
            return render_template('login.html')

        # Search by username or email
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Student Logout Route."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Simple Student Dashboard showing statistics and recent conversations."""
    # Query database for statistics
    total_conversations = Conversation.query.filter_by(user_id=current_user.id).count()
    
    # Query total messages across all user's conversations
    total_messages = Message.query.join(Conversation).filter(Conversation.user_id == current_user.id).count()
    
    # Get 5 most recent conversations
    recent_conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).limit(5).all()

    return render_template('dashboard.html', 
                           total_conversations=total_conversations,
                           total_messages=total_messages,
                           recent_conversations=recent_conversations)


@app.route('/chat')
@login_required
def chat_home():
    """Main Chat UI, defaults to starting a new chat session."""
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    return render_template('chat.html', conversations=conversations, active_conversation=None, messages=[])


@app.route('/chat/<int:conversation_id>')
@login_required
def chat_session(conversation_id):
    """View an existing conversation."""
    # Ownership Check: Ensure this conversation belongs to the logged-in user
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user_id != current_user.id:
        flash("You are not authorized to access this conversation.", "danger")
        return redirect(url_for('dashboard'))

    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).all()

    return render_template('chat.html', conversations=conversations, active_conversation=conversation, messages=messages)


@app.route('/new-chat')
@login_required
def new_chat():
    """Redirect to main chat UI to start a fresh chat."""
    return redirect(url_for('chat_home'))


@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """API endpoint to receive and process user chat requests."""
    data = request.get_json() or {}
    message_content = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')

    if not message_content:
        return jsonify({"success": False, "error": "Message content cannot be empty."}), 400

    conversation = None
    if conversation_id:
        # Ownership Check: Ensure this conversation belongs to the logged-in user
        conversation = Conversation.query.get(conversation_id)
        if not conversation or conversation.user_id != current_user.id:
            return jsonify({"success": False, "error": "Unauthorized conversation access."}), 403
    else:
        # Create a new conversation if it does not exist
        # Limit title to first 40 characters
        title = message_content[:40] + "..." if len(message_content) > 40 else message_content
        conversation = Conversation(user_id=current_user.id, title=title)
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id

    # Retrieve context: Fetch last 8 messages before adding the new user message
    history_messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.desc()).limit(8).all()
    history_messages.reverse() # Sort in chronological order

    # Save user message to database
    user_message = Message(conversation_id=conversation_id, role='user', content=message_content)
    conversation.updated_at = datetime.utcnow() # Touch updated_at time
    db.session.add(user_message)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": "Failed to save user message to database."}), 500

    # Call Gemini API
    ai_result = ai_service.generate_response(message_content, history_messages)

    if ai_result.get("success"):
        ai_response_content = ai_result.get("text")
        # Save AI response to database
        ai_message = Message(conversation_id=conversation_id, role='assistant', content=ai_response_content)
        db.session.add(ai_message)
        
        try:
            db.session.commit()
            return jsonify({
                "success": True,
                "conversation_id": conversation_id,
                "response": ai_response_content,
                "title": conversation.title
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": "Failed to save AI response to database."}), 500
    else:
        return jsonify({
            "success": False,
            "error": ai_result.get("error", "An unknown error occurred during AI processing.")
        })


@app.route('/delete-chat/<int:conversation_id>', methods=['POST'])
@login_required
def delete_chat(conversation_id):
    """Delete a conversation after owner check."""
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user_id != current_user.id:
        flash("You are not authorized to delete this conversation.", "danger")
        return redirect(url_for('dashboard'))

    try:
        db.session.delete(conversation)
        db.session.commit()
        flash("Conversation deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred. Could not delete the conversation.", "danger")
        print(f"Delete Error: {e}")

    # Redirect to dashboard or chat home
    return redirect(url_for('dashboard'))


@app.route('/search')
@login_required
def search():
    """Search logged-in user's conversations by title."""
    query = request.args.get('q', '').strip()
    if not query:
        # Return all user's conversations if query is empty
        results = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    else:
        results = Conversation.query.filter_by(user_id=current_user.id).filter(Conversation.title.ilike(f"%{query}%")).order_by(Conversation.updated_at.desc()).all()

    # Return search results as a JSON list for dynamic UI updates in the sidebar
    conversations_list = []
    for conv in results:
        conversations_list.append({
            "id": conv.id,
            "title": conv.title,
            "updated_at": conv.updated_at.strftime("%Y-%m-%d %H:%M")
        })
    return jsonify(conversations_list)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User Profile page with view and updates."""
    # Stats
    total_conversations = Conversation.query.filter_by(user_id=current_user.id).count()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()

        if not full_name or not username:
            flash("Full Name and Username cannot be empty.", "danger")
            return render_template('profile.html', total_conversations=total_conversations)

        # Check for username duplicates (excluding current user)
        existing_username = User.query.filter(User.username == username, User.id != current_user.id).first()
        if existing_username:
            flash("Username is already taken by another student.", "danger")
            return render_template('profile.html', total_conversations=total_conversations)

        current_user.full_name = full_name
        current_user.username = username
        
        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred. Profile details could not be updated.", "danger")
            print(f"Profile Update Error: {e}")

    return render_template('profile.html', total_conversations=total_conversations)


@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 handler."""
    return render_template('404.html'), 404


if __name__ == '__main__':
    # Run the application locally on default port 5000
    app.run(debug=True)
