import sqlite3

def init_db():
    print("💾 Inicializando banco de dados...")
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    message TEXT,
                    reply TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso.")

def log_message(sender, message, reply):
    print("📝 Salvando mensagem no banco de dados...")
    conn = sqlite3.connect("messages.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, message, reply) VALUES (?, ?, ?)",
              (sender, message, reply))
    conn.commit()
    conn.close()

