from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import uuid
from datetime import datetime
import database

app = Flask(__name__)

# Production session configuration
app.secret_key = os.environ.get('SECRET_KEY', 'aura_social_pro_render_deploy_2024_secure_key_12345')
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600
)

# Initialize database
database.init_db()

class User:
    def __init__(self, username, email, password):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password = password
        self.display_name = username
        self.bio = "Welcome to my Aura! ✨"
        self.avatar = "👤"
        self.created_at = datetime.now().isoformat()

def get_user_from_db(username):
    """Get user from database"""
    conn = database.get_db_connection()
    user_row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user_row:
        user = User(user_row['username'], user_row['email'], user_row['password'])
        user.id = user_row['id']
        user.display_name = user_row['display_name'] or user.username
        user.bio = user_row['bio'] or "Welcome to my Aura! ✨"
        user.avatar = user_row['avatar'] or "👤"
        user.created_at = user_row['created_at']
        return user
    return None

def save_user_to_db(user):
    """Save user to database"""
    conn = database.get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO users (id, username, email, password, display_name, bio, avatar, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user.id, user.username, user.email, user.password, user.display_name, user.bio, user.avatar, user.created_at))
    conn.commit()
    conn.close()

def get_posts_from_db():
    """Get all posts from database"""
    conn = database.get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY timestamp DESC').fetchall()
    conn.close()
    return posts

def save_post_to_db(post):
    """Save post to database"""
    conn = database.get_db_connection()
    conn.execute('''
        INSERT INTO posts (id, user_id, content, timestamp, likes, loves, laughs, wows, username, display_name, avatar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (post.id, post.user_id, post.content, post.timestamp, post.likes, post.loves or 0, post.laughs or 0, post.wows or 0, post.username, post.display_name, post.avatar))
    conn.commit()
    conn.close()

def update_post_reaction(post_id, reaction_type):
    """Update post reaction counts"""
    conn = database.get_db_connection()
    
    if reaction_type == 'like':
        conn.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
    elif reaction_type == 'love':
        conn.execute('UPDATE posts SET loves = loves + 1 WHERE id = ?', (post_id,))
    elif reaction_type == 'laugh':
        conn.execute('UPDATE posts SET laughs = laughs + 1 WHERE id = ?', (post_id,))
    elif reaction_type == 'wow':
        conn.execute('UPDATE posts SET wows = wows + 1 WHERE id = ?', (post_id,))
    
    conn.commit()
    
    # Get updated counts
    post = conn.execute('SELECT likes, loves, laughs, wows FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    
    if post:
        return {
            'likes': post['likes'],
            'loves': post['loves'],
            'laughs': post['laughs'],
            'wows': post['wows']
        }
    return None

# Initialize sample data if needed
def init_sample_data():
    demo_user = get_user_from_db('demo')
    if not demo_user:
        demo_user = User('demo', 'demo@aura.social', 'demo')
        save_user_to_db(demo_user)
        
        # Create sample posts
        sample_posts = [
            "Welcome to Aura Social! 🌟 This is a sample post to get things started. Share your aura with the world!",
            "Just discovered this amazing platform! The design is incredible and the community seems so friendly. Can't wait to connect with everyone! ✨",
            "Morning meditation complete! Starting the day with positive energy and good vibes. Remember to share your light with others today! 💫"
        ]
        
        for content in sample_posts:
            post = type('Post', (), {})()
            post.id = str(uuid.uuid4())
            post.user_id = demo_user.id
            post.content = content
            post.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            post.likes = 0
            post.loves = 0
            post.laughs = 0
            post.wows = 0
            post.username = demo_user.username
            post.display_name = demo_user.display_name
            post.avatar = demo_user.avatar
            save_post_to_db(post)

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

# MESSAGES ROUTE - THIS WAS MISSING!
@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('messages.html')

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

        # Check if user exists in database
        if get_user_from_db(username):
            return jsonify({'success': False, 'error': 'Username already exists'})

        # Create new user
        user = User(username, email, password)
        save_user_to_db(user)

        # Auto-login after registration
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        
        print(f"DEBUG: User registered and logged in: {username}")
        
        return jsonify({'success': True, 'message': 'Registration successful'})

    except Exception as e:
        print(f"DEBUG: Registration error: {e}")
        return jsonify({'success': False, 'error': 'Registration failed'})

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'})

        user = get_user_from_db(username)
        if not user or user.password != password:
            return jsonify({'success': False, 'error': 'Invalid credentials'})

        # Set up session properly
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        
        print(f"DEBUG: User logged in: {username}")
        
        return jsonify({'success': True, 'message': 'Login successful'})

    except Exception as e:
        print(f"DEBUG: Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    print("DEBUG: User logged out, session cleared")
    return jsonify({'success': True})

@app.route('/api/current_user')
def api_current_user():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'})

    username = session['username']
    user = get_user_from_db(username)
    
    if not user:
        return jsonify({'error': 'User not found'})

    # Get post count for this user
    conn = database.get_db_connection()
    post_count = conn.execute('SELECT COUNT(*) as count FROM posts WHERE user_id = ?', (user.id,)).fetchone()['count']
    conn.close()

    return jsonify({
        'username': user.username,
        'email': user.email,
        'display_name': user.display_name,
        'bio': user.bio,
        'avatar': user.avatar,
        'post_count': post_count,
        'followers': 0,
        'following': 0
    })

@app.route('/api/posts')
def api_posts():
    posts = get_posts_from_db()
    posts_data = [dict(post) for post in posts]
    print(f"DEBUG: Returning {len(posts_data)} posts from database")
    return jsonify(posts_data)

@app.route('/api/user_posts')
def api_user_posts():
    if 'user_id' not in session:
        return jsonify([])

    conn = database.get_db_connection()
    user_posts = conn.execute(
        'SELECT * FROM posts WHERE user_id = ? ORDER BY timestamp DESC', 
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    posts_data = [{
        'id': post['id'],
        'content': post['content'],
        'timestamp': post['timestamp'],
        'likes': post['likes'],
        'loves': post['loves'],
        'laughs': post['laughs'],
        'wows': post['wows']
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

        user = get_user_from_db(session['username'])
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})

        # Create new post object
        post = type('Post', (), {})()
        post.id = str(uuid.uuid4())
        post.user_id = user.id
        post.content = content
        post.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        post.likes = 0
        post.loves = 0
        post.laughs = 0
        post.wows = 0
        post.username = user.username
        post.display_name = user.display_name
        post.avatar = user.avatar

        save_post_to_db(post)
        print(f"DEBUG: Post created by {user.username}: {content}")

        return jsonify({'success': True, 'message': 'Post created successfully'})

    except Exception as e:
        print(f"DEBUG: Create post error: {e}")
        return jsonify({'success': False, 'error': 'Failed to create post'})

@app.route('/api/react_post/<post_id>/<reaction_type>', methods=['POST'])
def api_react_post(post_id, reaction_type):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    try:
        valid_reactions = ['like', 'love', 'laugh', 'wow']
        if reaction_type not in valid_reactions:
            return jsonify({'success': False, 'error': 'Invalid reaction type'})

        updated_counts = update_post_reaction(post_id, reaction_type)
        if updated_counts:
            return jsonify({'success': True, 'reactions': updated_counts})
        else:
            return jsonify({'success': False, 'error': 'Post not found'})

    except Exception as e:
        print(f"DEBUG: React post error: {e}")
        return jsonify({'success': False, 'error': 'Failed to react to post'})

@app.route('/api/update_avatar', methods=['POST'])
def api_update_avatar():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    try:
        data = request.get_json()
        avatar = data.get('avatar', '👤')
        
        username = session['username']
        user = get_user_from_db(username)
        
        if user:
            user.avatar = avatar
            save_user_to_db(user)
            print(f"DEBUG: Updated avatar for {username} to {avatar}")
            return jsonify({'success': True, 'message': 'Avatar updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'User not found'})
            
    except Exception as e:
        print(f"DEBUG: Update avatar error: {e}")
        return jsonify({'success': False, 'error': 'Failed to update avatar'})

@app.route('/api/debug_posts')
def debug_posts():
    posts = get_posts_from_db()
    return jsonify([dict(post) for post in posts])

@app.route('/api/debug_session')
def debug_session():
    return jsonify(dict(session))

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    # Initialize sample data
    init_sample_data()
    
    # Production settings
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 10000))
    
    print(f"🚀 Aura Social Pro with MESSAGES starting on port {port}")
    print("💬 Features: Live Messaging, SQLite Database, Avatar System")
    print("🔑 Demo account: username 'demo', password 'demo'")
    print("🌐 Production Ready!")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
