from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib

DATABASE_URL = "sqlite:///./mapas.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def gerar_hash_senha(senha: str) -> str:
    if senha and len(senha) == 64:
        return senha
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def verificar_senha(senha_pura: str, senha_criptografada: str) -> bool:
    return gerar_hash_senha(senha_pura) == senha_criptografada