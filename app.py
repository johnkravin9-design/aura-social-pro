from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import json
import datetime
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'aura_social_secret_key_2024'

# User database (in production we'd use a real database)
users_db = {}
posts_db = []
user_id_counter = 1

class User:
    def __init__(self, user_id, username, email, display_name, bio="", avatar="👤", role="user"):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.display_name = display_name
        self.bio = bio
        self.avatar = avatar
        self.role = role
        self.joined_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.following = []
        self.followers = []
        self.is_active = True

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "bio": self.bio,
            "avatar": self.avatar,
            "role": self.role,
            "joined_date": self.joined_date,
            "following_count": len(self.following),
            "followers_count": len(self.followers),
            "is_active": self.is_active
        }

    def is_admin(self):
        return self.role == "admin"

# Add admin user and sample users
def initialize_sample_data():
    global user_id_counter
    
    # CREATE ADMIN USER - You can login with these credentials!
    admin_user = User(user_id_counter, "admin", "admin@aura.social", "Aura Administrator", 
                     "Platform Administrator", "👑", "admin")
    user_id_counter += 1
    
    user1 = User(user_id_counter, "johnkravin", "john@aura.social", "John Kravin", 
                 "Building the future of social media 🚀", "👨‍💻")
    user_id_counter += 1
    user2 = User(user_id_counter, "auratech", "tech@aura.social", "Aura Team", 
                 "Creating intelligent social experiences", "🤖")
    user_id_counter += 1
    
    users_db[admin_user.username] = admin_user
    users_db[user1.username] = user1
    users_db[user2.username] = user2
    
    # Sample posts
    posts_db.extend([
        {
            "post_id": 1,
            "user_id": user1.user_id,
            "username": user1.username,
            "display_name": user1.display_name,
            "avatar": user1.avatar,
            "content": "Building the future of social media with Aura! 🚀\n\nThis platform will change how we connect online.",
            "timestamp": "2024-01-15 10:30:00",
            "reactions": {"like": 5, "love": 2, "insightful": 3},
            "comments": [
                {"username": "auratech", "display_name": "Aura Team", "text": "This is revolutionary!", "timestamp": "2024-01-15 10:35:00"}
            ],
            "is_approved": True
        },
        {
            "post_id": 2,
            "user_id": user2.user_id,
            "username": user2.username,
            "display_name": user2.display_name,
            "avatar": user2.avatar,
            "content": "Aura Features Coming Soon:\n• Focus Flow feeds\n• Smart Channels\n• Living Profiles\n• Context-aware AI\n• Ephemeral Spaces",
            "timestamp": "2024-01-15 09:15:00",
            "reactions": {"like": 8, "excited": 5, "curious": 4},
            "comments": [],
            "is_approved": True
        }
    ])

initialize_sample_data()

def is_admin():
    if 'user_id' in session:
        user = next((u for u in users_db.values() if u.user_id == session['user_id']), None)
        return user and user.is_admin()
    return False

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return jsonify({"success": False, "error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    if 'user_id' in session:
        if is_admin():
            return redirect('/admin')
        return render_template('feed.html')
    return render_template('auth.html')

@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        return redirect('/')
    return render_template('admin_dashboard.html')

@app.route('/profile/<username>')
def profile(username):
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    user = users_db.get(username)
    if not user:
        return "User not found", 404
    
    user_posts = [post for post in posts_db if post['username'] == username and post.get('is_approved', True)]
    return render_template('profile.html', user=user.to_dict(), posts=user_posts)

@app.route('/my_profile')
def my_profile():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    user = next((u for u in users_db.values() if u.user_id == session['user_id']), None)
    if user:
        user_posts = [post for post in posts_db if post['user_id'] == user.user_id and post.get('is_approved', True)]
        return render_template('profile.html', user=user.to_dict(), posts=user_posts, is_own_profile=True)
    return redirect(url_for('home'))

# Authentication APIs
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip().lower()
    email = data.get('email', '').strip().lower()
    display_name = data.get('display_name', '').strip()
    password = data.get('password', '')
    
    if not all([username, email, display_name, password]):
        return jsonify({"success": False, "error": "All fields are required"})
    
    if username in users_db:
        return jsonify({"success": False, "error": "Username already exists"})
    
    global user_id_counter
    new_user = User(user_id_counter, username, email, display_name)
    user_id_counter += 1
    
    users_db[username] = new_user
    
    # Auto-login after registration
    session['user_id'] = new_user.user_id
    session['username'] = new_user.username
    
    return jsonify({"success": True, "user": new_user.to_dict()})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    
    user = users_db.get(username)
    if user and user.is_active:  # In real app, we'd verify password hash
        session['user_id'] = user.user_id
        session['username'] = user.username
        return jsonify({"success": True, "user": user.to_dict()})
    
    return jsonify({"success": False, "error": "Invalid credentials"})

@app.route('/api/logout')
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/api/current_user')
def current_user():
    if 'user_id' in session:
        user = next((u for u in users_db.values() if u.user_id == session['user_id']), None)
        if user:
            return jsonify({"success": True, "user": user.to_dict()})
    return jsonify({"success": False})

# Admin APIs
@app.route('/api/admin/stats')
@require_admin
def admin_stats():
    stats = {
        "total_users": len(users_db),
        "total_posts": len(posts_db),
        "active_users": len([u for u in users_db.values() if u.is_active]),
        "pending_posts": len([p for p in posts_db if not p.get('is_approved', True)]),
        "new_users_today": len([u for u in users_db.values() if u.joined_date == datetime.datetime.now().strftime("%Y-%m-%d")])
    }
    return jsonify({"success": True, "stats": stats})

@app.route('/api/admin/users')
@require_admin
def admin_users():
    users_list = [user.to_dict() for user in users_db.values()]
    return jsonify({"success": True, "users": users_list})

@app.route('/api/admin/posts')
@require_admin
def admin_posts():
    return jsonify({"success": True, "posts": posts_db})

@app.route('/api/admin/toggle_user/<username>', methods=['POST'])
@require_admin
def toggle_user(username):
    user = users_db.get(username)
    if user:
        user.is_active = not user.is_active
        return jsonify({"success": True, "user": user.to_dict()})
    return jsonify({"success": False, "error": "User not found"})

@app.route('/api/admin/toggle_post/<int:post_id>', methods=['POST'])
@require_admin
def toggle_post(post_id):
    for post in posts_db:
        if post['post_id'] == post_id:
            post['is_approved'] = not post.get('is_approved', True)
            return jsonify({"success": True, "post": post})
    return jsonify({"success": False, "error": "Post not found"})

@app.route('/api/admin/delete_post/<int:post_id>', methods=['POST'])
@require_admin
def delete_post(post_id):
    global posts_db
    posts_db = [post for post in posts_db if post['post_id'] != post_id]
    return jsonify({"success": True})

# Post APIs
@app.route('/api/posts')
def get_posts():
    if is_admin():
        return jsonify(posts_db)
    else:
        approved_posts = [post for post in posts_db if post.get('is_approved', True)]
        return jsonify(approved_posts)

@app.route('/api/add_post', methods=['POST'])
def add_post():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"})
    
    data = request.json
    user = next((u for u in users_db.values() if u.user_id == session['user_id']), None)
    
    if user and data.get('content'):
        new_post = {
            "post_id": len(posts_db) + 1,
            "user_id": user.user_id,
            "username": user.username,
            "display_name": user.display_name,
            "avatar": user.avatar,
            "content": data['content'],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reactions": {"like": 0},
            "comments": [],
            "is_approved": user.is_admin()  # Auto-approve admin posts
        }
        posts_db.append(new_post)
        return jsonify({"success": True, "post": new_post})
    
    return jsonify({"success": False, "error": "Invalid data"})

@app.route('/api/react/<int:post_id>', methods=['POST'])
def react_to_post(post_id):
    data = request.json
    reaction_type = data.get('reaction', 'like')
    
    for post in posts_db:
        if post['post_id'] == post_id and post.get('is_approved', True):
            if reaction_type in post['reactions']:
                post['reactions'][reaction_type] += 1
            else:
                post['reactions'][reaction_type] = 1
            return jsonify({"success": True, "reactions": post['reactions']})
    
    return jsonify({"success": False, "error": "Post not found"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
