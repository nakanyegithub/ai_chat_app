import unittest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from database import User, Chat, Message

class ChatAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/test_ai_chat_db'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()
    
    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    # ==================== ТЕСТЫ РЕГИСТРАЦИИ ====================
    
    def test_01_register_success(self):
        response = self.client.post('/api/register', 
            json={'username': 'testuser', 'password': '123', 'email': 'test@test.com'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('Registration successful', response.json['message'])
    
    def test_02_register_duplicate_username(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        response = self.client.post('/api/register', json={'username': 'testuser', 'password': '456'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('User already exists', response.json['error'])
    
    def test_03_register_short_username(self):
        response = self.client.post('/api/register', json={'username': 'ab', 'password': '123'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Username must be at least 3 characters', response.json['error'])
    
    def test_04_register_missing_password(self):
        response = self.client.post('/api/register', json={'username': 'testuser'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Username and password required', response.json['error'])
    
    def test_05_register_missing_username(self):
        response = self.client.post('/api/register', json={'password': '123'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Username and password required', response.json['error'])
    
    def test_06_register_without_email(self):
        response = self.client.post('/api/register', 
            json={'username': 'testuser2', 'password': '123'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('Registration successful', response.json['message'])
    
    # ==================== ТЕСТЫ ВХОДА ====================
    
    def test_07_login_success(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        response = self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login successful', response.json['message'])
        self.assertEqual(response.json['username'], 'testuser')
    
    def test_08_login_wrong_password(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        response = self.client.post('/api/login', json={'username': 'testuser', 'password': 'wrong'})
        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid credentials', response.json['error'])
    
    def test_09_login_nonexistent_user(self):
        response = self.client.post('/api/login', json={'username': 'nonexistent', 'password': '123'})
        self.assertEqual(response.status_code, 401)
    
    # ==================== ТЕСТЫ ВЫХОДА ====================
    
    def test_10_logout(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        response = self.client.post('/api/logout')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Logged out', response.json['message'])
    
    # ==================== ТЕСТЫ ЧАТОВ ====================
    
    def test_11_create_chat_requires_auth(self):
        response = self.client.post('/api/chats', json={'title': 'New Chat'})
        self.assertIn(response.status_code, [401, 302])
    
    def test_12_create_chat_success(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        response = self.client.post('/api/chats', json={'title': 'My New Chat'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('chat', response.json)
        self.assertEqual(response.json['chat']['title'], 'My New Chat')
    
    def test_13_get_chats(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/chats', json={'title': 'Chat 1'})
        self.client.post('/api/chats', json={'title': 'Chat 2'})
        response = self.client.get('/api/chats')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json['chats']), 2)
    
    def test_14_delete_chat(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        chats_before = self.client.get('/api/chats').json['chats']
        if chats_before:
            chat_id = chats_before[0]['id']
            response = self.client.delete(f'/api/chats/{chat_id}')
            self.assertEqual(response.status_code, 200)
    
    def test_15_update_chat_title(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        create_resp = self.client.post('/api/chats', json={'title': 'Old Title'})
        chat_id = create_resp.json['chat']['id']
        response = self.client.put(f'/api/chats/{chat_id}', json={'title': 'New Title'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['chat']['title'], 'New Title')
    
    # ==================== ТЕСТЫ МОДЕЛЕЙ ====================
    
    def test_16_get_models_requires_auth(self):
        response = self.client.get('/api/models')
        self.assertIn(response.status_code, [401, 302])
    
    def test_17_get_models_success(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        response = self.client.get('/api/models')
        self.assertEqual(response.status_code, 200)
        self.assertIn('models', response.json)
    
    # ==================== ТЕСТЫ АДМИНКИ ====================
    
    def test_18_admin_access_requires_admin(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        response = self.client.get('/api/admin/users')
        self.assertEqual(response.status_code, 403)
    
    def test_19_admin_page_redirect_for_non_admin(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 302)
    
    # ==================== ТЕСТЫ ЗАЩИТЫ ====================
    
    def test_20_access_chat_without_login(self):
        response = self.client.get('/chat')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
    
    def test_21_access_admin_without_login(self):
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)
    
    # ==================== ТЕСТЫ ГРАНИЧНЫХ ЗНАЧЕНИЙ ====================
    
    def test_22_register_long_username(self):
        long_username = 'a' * 80
        response = self.client.post('/api/register', 
            json={'username': long_username, 'password': '123'})
        self.assertIn(response.status_code, [200, 201])
    
    def test_23_register_special_chars_in_username(self):
        response = self.client.post('/api/register', 
            json={'username': 'user_123-test', 'password': '123'})
        self.assertEqual(response.status_code, 201)
    
    # ==================== ТЕСТЫ МОДЕЛЕЙ БД ====================
    
    def test_24_user_model_works(self):
        with app.app_context():
            user = User(username='testmodel', password_hash='hash123')
            db.session.add(user)
            db.session.commit()
            found = User.query.filter_by(username='testmodel').first()
            self.assertIsNotNone(found)
            self.assertEqual(found.username, 'testmodel')
    
    def test_25_chat_model_works(self):
        with app.app_context():
            user = User(username='testmodel2', password_hash='hash123')
            db.session.add(user)
            db.session.commit()
            chat = Chat(user_id=user.id, title='Test Chat')
            db.session.add(chat)
            db.session.commit()
            found = Chat.query.filter_by(title='Test Chat').first()
            self.assertIsNotNone(found)
            self.assertEqual(found.user_id, user.id)
    
    def test_26_message_model_works(self):
        with app.app_context():
            user = User(username='testmodel3', password_hash='hash123')
            db.session.add(user)
            db.session.commit()
            chat = Chat(user_id=user.id, title='Test Chat')
            db.session.add(chat)
            db.session.commit()
            msg = Message(chat_id=chat.id, role='user', content='Hello world')
            db.session.add(msg)
            db.session.commit()
            found = Message.query.filter_by(content='Hello world').first()
            self.assertIsNotNone(found)
            self.assertEqual(found.role, 'user')
    
    def test_27_user_has_chat_after_registration(self):
        self.client.post('/api/register', json={'username': 'testuser', 'password': '123'})
        self.client.post('/api/login', json={'username': 'testuser', 'password': '123'})
        response = self.client.get('/api/chats')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json['chats']), 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
