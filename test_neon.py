# from models.database import db, inicializar_banco
#
# try:
#     print("Conectando ao banco...")
#     db.connect()
#     inicializar_banco()
#     print("✅ Conexão bem-sucedida e tabelas criadas/atualizadas!")
# except Exception as e:
#     print("❌ Erro na conexão:", e)
# finally:
#     db.close()

# import bcrypt
# from models.database import Users, db
#
# with db:
#     senha_hash = bcrypt.hashpw("lb@2025".encode(), bcrypt.gensalt()).decode()
#     Users.create(
#         cpf="00000000000",
#         nome="Login Padrão",
#         user="lbservicos",
#         psw=senha_hash,
#         perfil="Administrador"
#     )
