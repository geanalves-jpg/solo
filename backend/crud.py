import os, json, shutil, math
from database import gerar_hash_senha
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from models import Regiao, Tags, Usuario
from schemas import RegiaoCreate, RegiaoResponse, RegiaoUpdate, TagsCreate, TagsResponse, UsuarioCreate, UsuarioResponse

# CRUD DO USUARIO ---------------------------------------------
def criar_usuario(db: Session, dados: UsuarioCreate):
    dados_usuario = dados.dict()
    if len(dados_usuario["senha"]) < 60 and not dados_usuario["senha"].startswith("$2b$"):
        dados_usuario["senha"] = gerar_hash_senha(dados_usuario["senha"])
    
    novo_usuario = Usuario(**dados_usuario)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

def listar_usuario(db: Session, nome: str = None, page: int = 1, limit: int = 10):
    query = db.query(Usuario)
    if nome:
        query = query.filter(Usuario.nome.icontains(nome))
    total_registros = query.count()
    offset = (page - 1) * limit
    usuarios = query.offset(offset).limit(limit).all()
    total_paginas = math.ceil(total_registros / limit) if total_registros > 0 else 1
    
    return {
        "data": usuarios,
        "total": total_registros,
        "page": page,
        "limit": limit,
        "pages": total_paginas
    }

def buscar_usuario(db: Session, usuario_id: int):
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()

def substituir_usuario(db: Session, usuario_id: int, dados: UsuarioCreate):
    usuario = buscar_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="usuario não encontrado")

    usuario.nome = dados.nome
    usuario.descricao = dados.descricao
    usuario.email = dados.email
    
    if len(dados.senha) < 60 and not dados.senha.startswith("$2b$"):
        usuario.senha = gerar_hash_senha(dados.senha)
    else:
        usuario.senha = dados.senha
    
    db.commit()
    db.refresh(usuario)
    return usuario

def deletar_usuario(db: Session, usuario_id: int):
    usuario = buscar_usuario(db, usuario_id)
    if usuario:
        db.delete(usuario)
        db.commit()
    else:
        print(f"O usuario {usuario_id} foi deletado.")
    return usuario



# CRUD DA TABELA REGIAO ----------------------------------------------------------------------
PASTA_IMAGENS = "Regioes"

def criar_regiao(db: Session, dados: dict):
    nova_regiao = Regiao(
        nome=dados["nome"],
        descricao=dados.get("descricao"),
        id_regiao_pai=dados.get("id_regiao_pai"),
        id_criador=dados["id_criador"],
        caminho=""
    )
    db.add(nova_regiao)
    db.commit()
    db.refresh(nova_regiao)

    pasta_regiao = os.path.join("Regioes", str(nova_regiao.id))
    os.makedirs(pasta_regiao, exist_ok=True)

    nome_arquivo_imagem = f"{nova_regiao.id}.png"
    caminho_final_imagem = os.path.join(pasta_regiao, nome_arquivo_imagem)

    imagem: UploadFile = dados["imagem"]
    imagem.file.seek(0) 
    with open(caminho_final_imagem, "wb") as arquivo_local:
        shutil.copyfileobj(imagem.file, arquivo_local)

    nova_regiao.caminho = caminho_final_imagem.replace("\\", "/") 
    db.commit()

    todas_regioes = db.query(Regiao).all()
    
    def montar_arvore(regiao_atual):
        filhas = [r for r in todas_regioes if str(r.id_regiao_pai) == str(regiao_atual.id)]
        
        return {
            "Arquivo": f"{regiao_atual.id}.png",
            "X": 0,       # Padrão exigido pelo front
            "Y": 0,      
            "Cor": "#000000",
            "Regiões filhas": {r.nome: montar_arvore(r) for r in filhas}
        }

    raizes = [r for r in todas_regioes if r.id_regiao_pai is None or r.id_regiao_pai == 0 or r.id_regiao_pai == ""]
    estrutura_json = {r.nome: montar_arvore(r) for r in raizes}

    caminho_json = os.path.join(pasta_regiao, "mapa.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(estrutura_json, f, indent=4, ensure_ascii=False)

    return nova_regiao


def listar_regiao(db: Session):
    return db.query(Regiao).all()


def buscar_regiao(db: Session, regiao_id: int):
    return db.query(Regiao).filter(Regiao.id == regiao_id).first()

def substituir_regiao(db: Session, regiao_id: int, dados: RegiaoUpdate):
    regiao = buscar_regiao(db, regiao_id)
    if not regiao:
        raise HTTPException(status_code=404, detail="região não encontrada")

    regiao.nome = dados.nome
    regiao.descricao = dados.descricao
    regiao.id_regiao_pai = dados.id_regiao_pai
    regiao.id_criador = dados.id_criador
    
    db.commit()
    db.refresh(regiao)
    return regiao

def deletar_regiao(db: Session, regiao_id: int):
    regiao = buscar_regiao(db, regiao_id)
    if regiao:
        db.delete(regiao)
        db.commit()
    else:
        print(f"A regiao {regiao_id} foi deletada.")
    return regiao

# CRUD DA TABELA TAGS ----------------------------------------------------------------------
def criar_tag(db: Session, tag: TagsCreate, regiao_id: int = None):
    nova_tag = Tags(nome=tag.nome, id_regiao=regiao_id)
    db.add(nova_tag)
    db.commit()
    db.refresh(nova_tag)
    return nova_tag

def listar_tags(db: Session):
    return db.query(Tags).all()

def buscar_tag(db: Session, tag_id: int):
    return db.query(Tags).filter(Tags.id == tag_id).first()

def substituir_tag(db: Session, tag_id: int, dados: TagsCreate):
    tag = buscar_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    
    tag.nome = dados.nome
    db.commit()
    db.refresh(tag)
    return tag

def deletar_tag(db: Session, tag_id: int):
    tag = buscar_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    db.delete(tag)
    db.commit()
    return tag