from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'aura_social_pro_secret_key_2024'

# Use synchronous server with threading instead of async drivers
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# In-memory database (replace with real database in production)
users_db = {}
posts_db = []

class User:
    def __init__(self, username, email, password):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password = password  # In production, hash this!
        self.display_name = username
        self.bio = "Welcome to my Aura! ✨"
        self.avatar = "👤"
        self.created_at = datetime.now().isoformat()
        self.followers = []
        self.following = []

class Post:
    def __init__(self, user_id, content):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.content = content
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.likes = 0
        self.comments = []
        self.username = ""
        self.display_name = ""
        self.avatar = "👤"

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('feed.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('profile.html')

# API Routes
@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'All fields are required'})

        if username in users_db:
            return jsonify({'success': False, 'error': 'Username already exists'})

        # Create new user
        user = User(username, email, password)
        users_db[username] = user

        # Auto-login after registration
        session['user_id'] = user.id
        session['username'] = user.username

        return jsonify({'success': True, 'message': 'Registration successful'})

    except Exception as e:
        return jsonify({'success': False, 'error': 'Registration failed'})

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'})

        user = users_db.get(username)
        if not user or user.password != password:  # In production, use proper password hashing
            return jsonify({'success': False, 'error': 'Invalid credentials'})

        session['user_id'] = user.id
        session['username'] = user.username

        return jsonify({'success': True, 'message': 'Login successful'})

    except Exception as e:
        return jsonify({'success': False, 'error': 'Login failed'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/current_user')
def api_current_user():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'})

    username = session['username']
    user = users_db.get(username)
    
    if not user:
        return jsonify({'error': 'User not found'})

    return jsonify({
        'username': user.username,
        'email': user.email,
        'display_name': user.display_name,
        'bio': user.bio,
        'avatar': user.avatar,
        'followers': len(user.followers),
        'following': len(user.following)
    })

@app.route('/api/posts')
def api_posts():
    # Add user info to posts
    for post in posts_db:
        user = next((u for u in users_db.values() if u.id == post.user_id), None)
        if user:
            post.username = user.username
            post.display_name = user.display_name
            post.avatar = user.avatar

    posts_data = [{
        'id': post.id,
        'content': post.content,
        'timestamp': post.timestamp,
        'likes': post.likes,
        'username': post.username,
        'display_name': post.display_name,
        'avatar': post.avatar
    } for post in posts_db]

    return jsonify(posts_data)

@app.route('/api/user_posts')
def api_user_posts():
    if 'user_id' not in session:
        return jsonify([])

    user_posts = [post for post in posts_db if post.user_id == session['user_id']]
    posts_data = [{
        'id': post.id,
        'content': post.content,
        'timestamp': post.timestamp,
        'likes': post.likes
    } for post in user_posts]

    return jsonify(posts_data)

@app.route('/api/create_post', methods=['POST'])
def api_create_post():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    try:
        data = request.get_json()
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'success': False, 'error': 'Post content cannot be empty'})

        # Create new post
        post = Post(session['user_id'], content)
        
        # Add user info
        user = users_db.get(session['username'])
        if user:
            post.username = user.username
            post.display_name = user.display_name
            post.avatar = user.avatar

        posts_db.append(post)

        # Emit socket event for real-time update
        socketio.emit('new_post', {
            'id': post.id,
            'content': post.content,
            'timestamp': post.timestamp,
            'username': post.username,
            'display_name': post.display_name,
            'avatar': post.avatar,
            'likes': post.likes
        })

        return jsonify({'success': True, 'message': 'Post created successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to create post'})

@app.route('/api/like_post/<post_id>', methods=['POST'])
def api_like_post(post_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    try:
        post = next((p for p in posts_db if p.id == post_id), None)
        if post:
            post.likes += 1
            
            # Emit socket event for real-time update
            socketio.emit('post_updated', {
                'id': post.id,
                'likes': post.likes
            })

            return jsonify({'success': True, 'likes': post.likes})
        else:
            return jsonify({'success': False, 'error': 'Post not found'})

    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to like post'})

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print('Client connected to Aura Social')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from Aura Social')

@socketio.on('join_feed')
def handle_join_feed():
    print('User joined feed')
    emit('feed_joined', {'message': 'Welcome to Aura Social feed!'})

if __name__ == '__main__':
    # Create some sample data for demonstration
    if not users_db:
        sample_user = User('demo', 'demo@aura.social', 'demo')
        users_db['demo'] = sample_user
        
        sample_post = Post(sample_user.id, "Welcome to Aura Social! 🌟 This is a sample post to get things started. Share your aura with the world!")
        sample_post.username = sample_user.username
        sample_post.display_name = sample_user.display_name
        sample_post.avatar = sample_user.avatar
        posts_db.append(sample_post)

    print("🚀 Aura Social Pro starting on http://localhost:8000")
    socketio.run(app, debug=True, host='0.0.0.0', port=8000)
