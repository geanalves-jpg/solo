from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Regiao(Base):
    __tablename__ = "regiao"
    id        = Column(Integer, primary_key=True, index=True)
    id_regiao_pai    = Column(Integer, ForeignKey("regiao.id"), nullable=True)
    nome = Column(String)
    descricao = Column(String)
    caminho = Column(String)
    id_criador = Column(Integer, ForeignKey("usuario.id"), nullable=False)

    filhos = relationship("Regiao", backref="pai", remote_side=[id])
    usuario_criador = relationship("Usuario")

class Tags(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    id_regiao = Column(Integer, ForeignKey("regiao.id"))

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    descricao = Column(String)
    email = Column(String)
   # Quanti_mapas = Column(int)
    senha  = Column(String)
    regiao = relationship("Regiao")

class Relacao(Base):
    __tablename__ = "relacao"
    id_relacao = Column(Integer, primary_key=True, index=True)
    nome_regiao = Column(String)
    id_regiao = Column(Integer, ForeignKey("regiao.id"), nullable=True)
    caminho = Column(String)
