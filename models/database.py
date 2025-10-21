# models/database.py
import os
import sys
from peewee import *
from datetime import date
from playhouse.db_url import connect
from playhouse.shortcuts import ReconnectMixin
from dotenv import load_dotenv

load_dotenv()

# ==========================
# Configuração do Banco
# ==========================

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"DEBUG: Conectando ao banco -> {DATABASE_URL or 'SQLite local'}")

# Classe que adiciona reconexão automática (para Neon/PostgreSQL)
class ReconnectPostgresqlDatabase(ReconnectMixin, PostgresqlDatabase):
    pass

if DATABASE_URL:
    # Conecta ao Neon
    db = connect(DATABASE_URL)

    # Se for um Postgres puro, força reconexão automática
    if isinstance(db, PostgresqlDatabase):
        db = ReconnectPostgresqlDatabase(
            db.database,
            user=db.connect_params.get("user"),
            password=db.connect_params.get("password"),
            host=db.connect_params.get("host"),
            port=db.connect_params.get("port"),
            autorollback=True
        )
else:
    # Caminho local (SQLite)
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    db_path = os.path.join(BASE_DIR, "data", "uniformes.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = SqliteDatabase(db_path)


# ==========================
# Modelos
# ==========================

class BaseModel(Model):
    class Meta:
        database = db


class Fornecedor(BaseModel):
    nome = CharField(null=False)
    cpf_cnpj = CharField(null=True)
    telefone = CharField(null=True)
    endereco = CharField(null=True)
    email = CharField(null=True)
    chave_pg = CharField(null=True)


class Funcionario(BaseModel):
    cpf = CharField(unique=True)
    nome = CharField()
    telefone = CharField()
    endereco = CharField()
    tamanho = CharField()
    prazo = IntegerField(default=12)


class Uniforme(BaseModel):
    descricao = CharField()
    tamanho = CharField()
    quantidade_estoque = IntegerField(default=0)
    deposito = CharField()
    estado = CharField()
    fornecedor = ForeignKeyField(Fornecedor, backref="uniformes")


class Entrega(BaseModel):
    id = AutoField(primary_key=True)
    funcionario = ForeignKeyField(Funcionario, backref="entregas")
    data_entrega = DateField(default=date.today)
    usuario = CharField(null=False)


class ItemEntrega(BaseModel):
    id = AutoField(primary_key=True)
    entrega = ForeignKeyField(Entrega, backref="itens")
    uniforme = ForeignKeyField(Uniforme, backref="entregas")
    estado = CharField(null=False)
    tamanho = CharField(null=False)
    quantidade = IntegerField()


class Comodato(BaseModel):
    funcionario = ForeignKeyField(Funcionario, backref="comodatos")
    uniforme = ForeignKeyField(Uniforme)
    quantidade = IntegerField()
    data_entrega = DateField()
    data_devolucao = DateField(null=True)
    ativo = BooleanField(default=True)


class Compra(BaseModel):
    id = AutoField(primary_key=True)
    fornecedor = ForeignKeyField(Fornecedor, backref="compra")
    data_compra = DateField(default=date.today)
    valor = FloatField()


class ItemCompra(BaseModel):
    id = AutoField(primary_key=True)
    compra = ForeignKeyField(Compra, backref="itens")
    uniforme = ForeignKeyField(Uniforme, backref="compra")
    estado = CharField(default="Novo")
    tamanho = CharField(null=False)
    quantidade = IntegerField()
    preco_unitario = FloatField()
    subtotal = FloatField()


class Users(BaseModel):
    cpf = CharField(unique=True)
    nome = CharField(null=False)
    user = CharField(null=False)
    psw = CharField(null=False)
    perfil = CharField(null=False)


class Reparo(BaseModel):
    data_reparo = DateField(default=date.today)
    fornecedor = ForeignKeyField(Fornecedor, backref="reparos")
    reparo = CharField(null=False)
    quantidade = IntegerField(null=False)
    preco_unitario = FloatField(null=False)
    subtotal = FloatField(null=False)


# ==========================
# Funções auxiliares
# ==========================

def ensure_connection():
    """Garante que a conexão com o banco esteja aberta."""
    if db.is_closed():
        try:
            db.connect(reuse_if_open=True)
        except Exception as e:
            print(f"⚠️ Erro ao reconectar ao banco: {e}")


def inicializar_banco():
    """Cria as tabelas, se não existirem."""
    ensure_connection()
    db.create_tables([
        Fornecedor,
        Funcionario,
        Uniforme,
        Entrega,
        ItemEntrega,
        Comodato,
        Compra,
        ItemCompra,
        Users,
        Reparo
    ])
    print("✅ Banco inicializado com sucesso.")


# ==========================
# Execução direta (teste)
# ==========================
if __name__ == "__main__":
    inicializar_banco()