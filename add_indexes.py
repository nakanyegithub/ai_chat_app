from app import app, db
from sqlalchemy import text

with app.app_context():
    # Добавляем индексы для оптимизации
    try:
        db.session.execute(text("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_chat_id_timestamp ON messages(chat_id, timestamp);"))
        print("✓ Index idx_messages_chat_id_timestamp created")
    except Exception as e:
        print(f"Index creation error: {e}")
    
    try:
        db.session.execute(text("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chats_user_id_updated ON chats(user_id, updated_at DESC);"))
        print("✓ Index idx_chats_user_id_updated created")
    except Exception as e:
        print(f"Index creation error: {e}")
    
    try:
        db.session.execute(text("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);"))
        print("✓ Index idx_messages_timestamp created")
    except Exception as e:
        print(f"Index creation error: {e}")
    
    db.session.commit()
    print("All indexes added successfully!")
