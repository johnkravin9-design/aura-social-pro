from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'aura_social_pro_admin_2024_secure')

# Enhanced user storage with admin support
users_db = {}
posts_db = []
reports_db = []

class User:
    def __init__(self, username, email, password, is_admin=False):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password = password
        self.display_name = username
        self.bio = "Welcome to my Aura! ✨"
        self.avatar = "👤"
        self.is_admin = is_admin
        self.is_active = True
        self.created_at = datetime.now().isoformat()
        self.last_login = datetime.now().isoformat()

class Post:
    def __init__(self, user_id, content):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.content = content
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.likes = 0
        self.is_approved = True
        self.reports = 0
        self.username = ""
        self.display_name = ""
        self.avatar = "👤"

# Initialize with admin user - FIXED CREDENTIALS
def init_sample_data():
    # Create admin user - SIMPLE PASSWORD
    if 'admin' not in users_db:
        admin_user = User('admin', 'admin@aura.social', 'admin', is_admin=True)  # Changed to simple 'admin'
        users_db['admin'] = admin_user
        print("👑 ADMIN USER CREATED: username 'admin', password 'admin'")
    
    # Create demo user
    if 'demo' not in users_db:
        demo_user = User('demo', 'demo@aura.social', 'demo')
        users_db['demo'] = demo_user
        print("👤 DEMO USER: username 'demo', password 'demo'")
        
        # Create sample posts
        sample_posts = [
            "Welcome to Aura Social! 🌟 Share your aura with the world!",
            "Just discovered this amazing platform! The community seems so friendly. ✨",
            "Morning meditation complete! Starting the day with positive energy! 💫"
        ]
        
        for content in sample_posts:
            post = Post(demo_user.id, content)
            post.username = demo_user.username
            post.display_name = demo_user.display_name
            post.avatar = demo_user.avatar
            posts_db.append(post)

    print(f"✅ Total users: {len(users_db)}")
    print(f"✅ Total posts: {len(posts_db)}")

# Admin authentication middleware
def require_admin(f):
    def decorated_function(*args, **kwargs):
        print(f"🔐 Checking admin access for {session.get('username', 'No user')}")
        
        if 'username' not in session:
            print("❌ No user in session - redirecting to login")
            return redirect('/login')
        
        username = session['username']
        user = users_db.get(username)
        
        if not user:
            print(f"❌ User {username} not found in database")
            return jsonify({'success': False, 'error': 'User not found'}), 403
        
        if not user.is_admin:
            print(f"❌ User {username} is not admin")
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        print(f"✅ Admin access granted for {username}")
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

# ========== ROUTES ========== #
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

@app.route('/messages')
def messages():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('messages.html')

# ADMIN PANEL ROUTES
@app.route('/admin')
@require_admin
def admin_dashboard():
    print("🎯 Rendering admin dashboard")
    return render_template('admin_dashboard.html')

@app.route('/admin/users')
@require_admin
def admin_users():
    return render_template('admin_users.html')

@app.route('/admin/posts')
@require_admin
def admin_posts():
    return render_template('admin_posts.html')

@app.route('/admin/reports')
@require_admin
def admin_reports():
    return render_template('admin_reports.html')

# ========== API ROUTES ========== #
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

        user = User(username, email, password)
        users_db[username] = user

        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin

        print(f"✅ New user registered: {username}")
        return jsonify({'success': True, 'message': 'Registration successful'})

    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({'success': False, 'error': 'Registration failed'})

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        print(f"🔐 Login attempt: {username}")

        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'})

        user = users_db.get(username)
        
        if not user:
            print(f"❌ User {username} not found")
            return jsonify({'success': False, 'error': 'Invalid credentials'})

        if user.password != password:
            print(f"❌ Invalid password for {username}")
            return jsonify({'success': False, 'error': 'Invalid credentials'})

        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account suspended'})

        # Set session data
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin

        user.last_login = datetime.now().isoformat()

        print(f"✅ Login successful: {username} (Admin: {user.is_admin})")
        return jsonify({
            'success': True, 
            'message': 'Login successful', 
            'is_admin': user.is_admin,
            'username': user.username
        })

    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    print(f"🚪 Logout: {session.get('username', 'Unknown')}")
    session.clear()
    return jsonify({'success': True})

@app.route('/api/current_user')
def api_current_user():
    username = session.get('username')
    print(f"👤 Current user check: {username}")
    
    if not username:
        return jsonify({'error': 'Not logged in'})

    user = users_db.get(username)
    
    if not user:
        return jsonify({'error': 'User not found'})

    return jsonify({
        'username': user.username,
        'email': user.email,
        'display_name': user.display_name,
        'bio': user.bio,
        'avatar': user.avatar,
        'is_admin': user.is_admin,
        'is_active': user.is_active
    })

# ADMIN API ROUTES
@app.route('/api/admin/stats')
@require_admin
def api_admin_stats():
    stats = {
        'total_users': len(users_db),
        'total_posts': len(posts_db),
        'pending_reports': len([r for r in reports_db if r.status == 'pending']),
        'active_today': len([u for u in users_db.values() if u.last_login.split('T')[0] == datetime.now().date().isoformat()]),
        'new_users_today': len([u for u in users_db.values() if u.created_at.split('T')[0] == datetime.now().date().isoformat()])
    }
    return jsonify(stats)

@app.route('/api/admin/users')
@require_admin
def api_admin_users():
    users_data = []
    for user in users_db.values():
        user_posts = len([p for p in posts_db if p.user_id == user.id])
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'post_count': user_posts,
            'created_at': user.created_at,
            'last_login': user.last_login
        })
    return jsonify(users_data)

@app.route('/api/admin/posts')
@require_admin
def api_admin_posts():
    posts_data = []
    for post in posts_db:
        user = next((u for u in users_db.values() if u.id == post.user_id), None)
        posts_data.append({
            'id': post.id,
            'content': post.content,
            'username': user.username if user else 'Unknown',
            'timestamp': post.timestamp,
            'likes': post.likes,
            'reports': post.reports,
            'is_approved': post.is_approved
        })
    return jsonify(posts_data)

@app.route('/api/admin/toggle_user/<username>', methods=['POST'])
@require_admin
def api_admin_toggle_user(username):
    user = users_db.get(username)
    if user:
        user.is_active = not user.is_active
        return jsonify({'success': True, 'is_active': user.is_active})
    return jsonify({'success': False, 'error': 'User not found'})

@app.route('/api/admin/toggle_post/<post_id>', methods=['POST'])
@require_admin
def api_admin_toggle_post(post_id):
    post = next((p for p in posts_db if p.id == post_id), None)
    if post:
        post.is_approved = not post.is_approved
        return jsonify({'success': True, 'is_approved': post.is_approved})
    return jsonify({'success': False, 'error': 'Post not found'})

@app.route('/api/admin/delete_post/<post_id>', methods=['POST'])
@require_admin
def api_admin_delete_post(post_id):
    global posts_db
    posts_db = [p for p in posts_db if p.id != post_id]
    return jsonify({'success': True})

# User API routes
@app.route('/api/posts')
def api_posts():
    approved_posts = [p for p in posts_db if p.is_approved]
    
    for post in approved_posts:
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
    } for post in approved_posts]

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

        user = users_db.get(session['username'])
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})

        post = Post(user.id, content)
        post.username = user.username
        post.display_name = user.display_name
        post.avatar = user.avatar

        posts_db.append(post)
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
            return jsonify({'success': True, 'likes': post.likes})
        else:
            return jsonify({'success': False, 'error': 'Post not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to like post'})

@app.route('/api/update_avatar', methods=['POST'])
def api_update_avatar():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})

    try:
        data = request.get_json()
        avatar = data.get('avatar', '👤')
        
        username = session['username']
        user = users_db.get(username)
        
        if user:
            user.avatar = avatar
            return jsonify({'success': True, 'message': 'Avatar updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'User not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to update avatar'})

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    init_sample_data()
    
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 8000))
    
    print("\n" + "="*50)
    print("🚀 AURA SOCIAL PRO - ADMIN PANEL READY")
    print("="*50)
    print("👑 ADMIN LOGIN:")
    print("   Username: admin")
    print("   Password: admin")
    print("   URL: /admin")
    print("")
    print("👤 DEMO LOGIN:")
    print("   Username: demo") 
    print("   Password: demo")
    print("")
    print("💬 Messages: /messages")
    print("👑 Admin Panel: /admin")
    print(f"🌐 Running on http://0.0.0.0:{port}")
    print("="*50 + "\n")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

@app.route('/admin_test')
def admin_test():
    return render_template('admin_test.html')
