from models.database import db, inicializar_banco

try:
    print("Conectando ao banco...")
    db.connect()
    inicializar_banco()
    print("✅ Conexão bem-sucedida e tabelas criadas/atualizadas!")
except Exception as e:
    print("❌ Erro na conexão:", e)
finally:
    db.close()


