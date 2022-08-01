import psycopg2


class BotDB:
    def __init__(self, DB_URI):
        self.conn = psycopg2.connect(DB_URI, sslmode="require")
        self.cursor = self.conn.cursor()

    def user_exists(self, user_id):
        """Проверяем, есть ли юзер в базе"""
        self.cursor.execute(f"SELECT id FROM users WHERE user_id = {user_id}")
        result = self.cursor.fetchone()
        return True if result else False

    def add_user(self, user_id):
        """Добавляем юзера в базу"""
        self.cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
        return self.conn.commit()

    def close(self):
        """Закрываем соединение с БД"""
        self.conn.close()