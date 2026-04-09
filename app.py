from flask import Flask, request, jsonify, render_template, session, redirect, url_for, Response, stream_with_context
from functools import wraps
from datetime import datetime, timedelta, timezone
import secrets
import time
import json
import threading
from database import db, User, Chat, Message, ModelStats
from ollama_client import ask_ollama_stream, get_available_models
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin_user = User(username='admin', password_hash='admin123', email=None, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print("Admin created: admin / admin123")

def get_current_time():
    return datetime.now(timezone.utc)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    models = get_available_models()
    return render_template('register.html', available_models=models)

@app.route('/chat')
@login_required
def chat_page():
    user = db.session.get(User, session['user_id'])
    available_models = get_available_models()
    if user.is_admin:
        return redirect(url_for('admin_page'))
    chats = Chat.query.filter_by(user_id=user.id).order_by(Chat.updated_at.desc()).all()
    return render_template('chat.html', 
                         username=session.get('username'),
                         current_model=user.preferred_model if user else (available_models[0] if available_models else "llama2"),
                         available_models=available_models,
                         chats=[c.to_dict() for c in chats])

@app.route('/admin')
@login_required
def admin_page():
    user = db.session.get(User, session['user_id'])
    if not user.is_admin:
        return redirect(url_for('chat_page'))
    available_models = get_available_models()
    users = User.query.all()
    return render_template('admin.html', 
                         username=session.get('username'),
                         users=users,
                         available_models=available_models)

@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    users = User.query.all()
    return jsonify({'users': [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_admin': u.is_admin,
        'created_at': u.created_at.isoformat() if u.created_at else None,
        'last_login': u.last_login.isoformat() if u.last_login else None,
        'chats_count': u.chats.count()
    } for u in users]})

@app.route('/api/admin/users/<int:user_id>/chats', methods=['GET'])
@admin_required
def admin_get_user_chats(user_id):
    user = User.query.get_or_404(user_id)
    chats = Chat.query.filter_by(user_id=user.id).order_by(Chat.updated_at.desc()).all()
    return jsonify({'chats': [c.to_dict() for c in chats], 'username': user.username})

@app.route('/api/admin/users/<int:user_id>/chats/<int:chat_id>/messages', methods=['GET'])
@admin_required
def admin_get_chat_messages(user_id, chat_id):
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first_or_404()
    messages = chat.messages.order_by(Message.timestamp.asc()).all()
    return jsonify({'messages': [m.to_dict() for m in messages], 'chat_title': chat.title})

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'User already exists'}), 400
        
        if email == '':
            email = None
        
        available_models = get_available_models()
        default_model = available_models[0] if available_models else "llama2"
        
        new_user = User(username=username, password_hash=password, email=email, preferred_model=default_model)
        db.session.add(new_user)
        db.session.commit()
        
        first_chat = Chat(user_id=new_user.id, title='New Chat', model_used=default_model)
        db.session.add(first_chat)
        db.session.commit()
        
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        
        return jsonify({'message': 'Registration successful', 'user_id': new_user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        user = User.query.filter_by(username=username, password_hash=password).first()
        
        if user:
            user.last_login = get_current_time()
            session['user_id'] = user.id
            session['username'] = user.username
            
            db.session.commit()
            return jsonify({'message': 'Login successful', 'username': user.username, 'preferred_model': user.preferred_model, 'user_id': user.id, 'is_admin': user.is_admin})
        
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})

@app.route('/api/chats', methods=['GET'])
@login_required
def get_chats():
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if user.is_admin:
        return jsonify({'chats': []})
    chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.updated_at.desc()).all()
    return jsonify({'chats': [c.to_dict() for c in chats]})

@app.route('/api/chats', methods=['POST'])
@login_required
def create_chat():
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if user.is_admin:
        return jsonify({'error': 'Admins cannot create chats'}), 403
    data = request.json
    title = data.get('title', 'New Chat')
    model = data.get('model', user.preferred_model)
    new_chat = Chat(user_id=user_id, title=title, model_used=model)
    db.session.add(new_chat)
    db.session.commit()
    return jsonify({'chat': new_chat.to_dict()}), 201

@app.route('/api/chats/<int:chat_id>', methods=['PUT'])
@login_required
def update_chat(chat_id):
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if user.is_admin:
        return jsonify({'error': 'Admins cannot edit chats'}), 403
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first_or_404()
    data = request.json
    if 'title' in data:
        chat.title = data['title']
    if 'model_used' in data:
        chat.model_used = data['model_used']
    db.session.commit()
    return jsonify({'chat': chat.to_dict()})

@app.route('/api/chats/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if user.is_admin:
        return jsonify({'error': 'Admins cannot delete chats'}), 403
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first_or_404()
    db.session.delete(chat)
    db.session.commit()
    return jsonify({'message': 'Chat deleted'})

@app.route('/api/chats/<int:chat_id>/messages', methods=['GET'])
@login_required
def get_chat_messages(chat_id):
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if user.is_admin:
        return jsonify({'error': 'Admins cannot view chats'}), 403
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first_or_404()
    messages = chat.messages.order_by(Message.timestamp.asc()).all()
    return jsonify({'messages': [m.to_dict() for m in messages]})

stop_flags = {}

@app.route('/api/chats/<int:chat_id>/messages/stream', methods=['POST'])
@login_required
def send_message_stream(chat_id):
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if user.is_admin:
        return jsonify({'error': 'Admins cannot send messages'}), 403
    
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first_or_404()
    data = request.json
    user_message = data.get('message')
    model_name = data.get('model', chat.model_used)
    
    user_msg = Message(chat_id=chat.id, role='user', content=user_message)
    db.session.add(user_msg)
    db.session.commit()
    
    history = chat.messages.order_by(Message.timestamp.asc()).limit(20).all()
    context = "\n".join([f"{m.role}: {m.content}" for m in history])
    
    stop_key = f"{chat_id}_{user_msg.id}"
    stop_flags[stop_key] = False
    
    def generate():
        full_response = ""
        start_time = time.time()
        
        for chunk in ask_ollama_stream(context + f"\nuser: {user_message}\nassistant:", model_name):
            if stop_flags.get(stop_key, False):
                break
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        response_time = time.time() - start_time
        
        if full_response:
            ai_msg = Message(chat_id=chat.id, role='assistant', content=full_response, model_used=model_name, response_time=response_time)
            db.session.add(ai_msg)
            
            chat.updated_at = get_current_time()
            if chat.title == 'New Chat' and len(user_message) > 0:
                chat.title = user_message[:30] + ('...' if len(user_message) > 30 else '')
            
            db.session.commit()
            
            model_stat = ModelStats.query.filter_by(model_name=model_name).first()
            if not model_stat:
                model_stat = ModelStats(model_name=model_name, total_requests=0, avg_response_time=0.0)
                db.session.add(model_stat)
                db.session.commit()
                model_stat = ModelStats.query.filter_by(model_name=model_name).first()
            
            if model_stat.total_requests is None:
                model_stat.total_requests = 0
            model_stat.total_requests += 1
            model_stat.avg_response_time = (model_stat.avg_response_time * (model_stat.total_requests - 1) + response_time) / model_stat.total_requests
            model_stat.last_used = get_current_time()
            db.session.commit()
        
        del stop_flags[stop_key]
        yield f"data: {json.dumps({'done': True, 'response_time': round(response_time, 2)})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/chats/<int:chat_id>/messages/stop', methods=['POST'])
@login_required
def stop_generation(chat_id):
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if user.is_admin:
        return jsonify({'error': 'Admins cannot stop messages'}), 403
    
    data = request.json
    message_id = data.get('message_id')
    stop_key = f"{chat_id}_{message_id}"
    
    if stop_key in stop_flags:
        stop_flags[stop_key] = True
        return jsonify({'message': 'Generation stopped'}), 200
    
    return jsonify({'message': 'No active generation found'}), 404

@app.route('/api/chats/<int:chat_id>/messages', methods=['DELETE'])
@login_required
def clear_chat_messages(chat_id):
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    if user.is_admin:
        return jsonify({'error': 'Admins cannot clear chats'}), 403
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first_or_404()
    Message.query.filter_by(chat_id=chat.id).delete()
    db.session.commit()
    return jsonify({'message': 'Messages cleared'})

@app.route('/api/models', methods=['GET'])
@login_required
def get_models():
    models = get_available_models()
    return jsonify({'models': models})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

@app.route('/api/chats/search', methods=['GET'])
@login_required
def search_chats():
    user_id = session['user_id']
    query = request.args.get('q', '')
    chats = Chat.query.filter(
        Chat.user_id == user_id,
        Chat.title.ilike(f'%{query}%')
    ).order_by(Chat.updated_at.desc()).limit(50).all()
    return jsonify({'chats': [c.to_dict() for c in chats]})

@app.route('/api/chats/<int:chat_id>/messages/paginated', methods=['GET'])
@login_required
def get_messages_paginated(chat_id):
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first_or_404()
    paginated = chat.messages.order_by(Message.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'messages': [m.to_dict() for m in paginated.items],
        'total': paginated.total,
        'page': page,
        'pages': paginated.pages
    })
