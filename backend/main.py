import os #ngc pra subir imagem
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles

import crud, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import Base, engine, get_db, verificar_senha, SessionLocal, gerar_hash_senha
import jwt
from datetime import datetime, timedelta
from schemas import RegiaoCreate, RegiaoResponse, RegiaoUpdate, TagsCreate, TagsResponse, UsuarioCreate, UsuarioResponse, UsuarioPaginadoResponse, LoginRequest, TokenResponse
from fastapi import UploadFile, File, Form, BackgroundTasks
from fastapi.exceptions import RequestValidationError  # pra erro 422
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database import Base, engine, get_db, verificar_senha, SessionLocal, gerar_hash_senha # Adicionado SessionLocal e gerar_hash_senha
import models # Garanta que models está importado para o seed encontrar a tabela

Base.metadata.create_all(bind=engine)  # cria as tabelas ao iniciar

def seeder_usuario_fixo():
    db = SessionLocal()
    try:
        usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == "admin@email.com").first()
        
        if not usuario_existente:
            usuario_seed = models.Usuario(
                nome="Administrador",
                descricao="Usuário padrão criado pelo backend.",
                email="admin@email.com",
                senha=gerar_hash_senha("admin1234") 
            )
            db.add(usuario_seed)
            db.commit()
            print("BANCO DE DADOS: Usuário fixo ('admin@email.com') criado com sucesso!")
    except Exception as e:
        print(f"Erro ao criar usuário fixo no seed: {e}")
    finally:
        db.close()
seeder_usuario_fixo()

def enviar_email_boas_vindas(email_destino: str, nome_usuario: str):
    SMTP_SERVER = "smtp.gmail.com"  # Altere para o host do seu provedor
    SMTP_PORT = 587                           
    SMTP_USER = "desouzagean00@gmail.com"             
    SMTP_PASSWORD = "dgri psay tgne bnnv"           
    
    # 📝 ESTRUTURAÇÃO DA MENSAGEM
    mensagem = MIMEMultipart("alternative")
    mensagem["Subject"] = f"Bem-vindo ao Sistema de Mapas, {nome_usuario}!"
    mensagem["From"] = f"Sistema de Mapas <{SMTP_USER}>"
    mensagem["To"] = email_destino

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2c3e50;">Olá, {nome_usuario}!</h2>
        <p>Seu cadastro foi realizado com sucesso em nossa plataforma de mapeamento geográfico.</p>
        <p>Agora você já pode fazer login, criar suas regiões e gerenciar suas tags personalizadas.</p>
        <br>
        <a href="http://localhost:8000/docs" style="background-color: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Acessar o Sistema</a>
        <br><br>
        <p>Atenciosamente,<br><strong>Equipe de Desenvolvimento</strong></p>
      </body>
    </html>
    """
    
    mensagem.attach(MIMEText(html, "html"))

    try:
        # Nota: Se usar porta 465, mude para smtplib.SMTP_SSL()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as servidor:
            # Se o servidor exigir TLS (comum na porta 587/2525)
            servidor.starttls() 
            servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.sendmail(mensagem["From"], email_destino, mensagem.as_string())
        print(f"E-mail de boas-vindas enviado com sucesso para {email_destino}!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

app = FastAPI(title="API de Mapas (SQLite)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validador_customizado_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "erro": "Dados inválidos",
            "mensagem": "Por favor, verifique os campos enviados. Certifique-se de que os tipos de dados estão corretos e que nenhum campo obrigatório está faltando."
        }
    )
# ROTAS DE SEGURANÇA -------------------------
security_bearer = HTTPBearer()

def verificar_token_obrigatorio(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="O token de acesso expirou. Faça login novamente."
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido. Acesso não autorizado."
        )


#ROTAS DOS USUARIOS ------------------------
@app.post("/usuario", status_code=201, tags=["Usuario"])
def criar_usuario(dados: UsuarioCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    email_em_uso = db.query(models.Usuario).filter(models.Usuario.email == dados.email).first()
    if email_em_uso:
        raise HTTPException(
            status_code=409,
            detail="Este e-mail já está cadastrado no sistema. Tente outro ou faça login."
        )
    novo_usuario = crud.criar_usuario(db, dados)
    background_tasks.add_task(enviar_email_boas_vindas, novo_usuario.email, novo_usuario.nome)
        
    return novo_usuario

@app.get("/usuario", response_model=UsuarioPaginadoResponse, tags=["Usuario"])
def listar_usuario(nome: str = None, 
    page: int = 1,    # Valor padrão é a página 1
    limit: int = 10,  # Valor padrão é limite de 10 por página
    db: Session = Depends(get_db)):
    return crud.listar_usuario(db, nome=nome, page=page, limit=limit)

@app.get("/usuario/{usuario_id}", response_model=UsuarioResponse, tags=["Usuario"])
def buscar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    usuario = crud.buscar_usuario(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário ainda não foi cadastrado")
    return usuario

@app.put("/usuario/{usuario_id}", response_model=UsuarioResponse, tags=["Usuario"])
def substituir_usuario(usuario_id: int, dados: UsuarioCreate, db: Session = Depends(get_db)):
    return crud.substituir_usuario(db, usuario_id, dados)

@app.delete("/usuario/{usuario_id}", status_code=204, tags=["Usuario"])
def deletar_usuario(usuario_id: int, db: Session = Depends(get_db)):
    print(usuario_id)
    crud.deletar_usuario(db, usuario_id)


# ROTAS DA ENTIDADE REGIAO -------------------------------------------------------------------

@app.post("/regiao", status_code=201, tags=["Região"], dependencies=[Depends(verificar_token_obrigatorio)])
async def criar_regiao(
    nome: str = Form(...),
    descricao: str = Form(None),
    id_regiao_pai: int = Form(None),
    id_criador: int = Form(...),
    imagem: UploadFile = File(...),
    db: Session = Depends(get_db)):

    usuario = crud.buscar_usuario(db, id_criador)
    if not usuario:
        raise HTTPException(
            status_code=404, 
            detail="O id_criador informado não corresponde a nenhum usuário cadastrado."
        )

    dados_regiao = {
        "nome": nome,
        "descricao": descricao,
        "id_regiao_pai": id_regiao_pai,
        "caminho": "",
        "id_criador": id_criador,
        "imagem": imagem
    }
    return crud.criar_regiao(db, dados_regiao)

@app.get("/regiao",response_model=list[RegiaoResponse],response_model_exclude={"__all__": {"usuario_criador": {"id"}}}, tags=["Região"])
def listar_regiao(db: Session = Depends(get_db)):
    return crud.listar_regiao(db)

@app.get("/regiao/{regiao_id}", response_model=RegiaoResponse, tags=["Região"])
def buscar_regiao(regiao_id: int, db: Session = Depends(get_db)):
    regiao = crud.buscar_regiao(db, regiao_id)
    if not regiao:
        raise HTTPException(status_code=404, detail="Sua Região ainda não foi anexada")
    return regiao

@app.put("/regiao/{regiao_id}", response_model=RegiaoResponse, tags=["Região"], dependencies=[Depends(verificar_token_obrigatorio)])
def substituir_regiao(regiao_id: int, dados: RegiaoUpdate, db: Session = Depends(get_db)):
    usuario = crud.buscar_usuario(db, dados.id_criador)
    if not usuario:
        raise HTTPException(status_code=404, detail="O id_criador informado não existe.")
    return crud.substituir_regiao(db, regiao_id, dados)

@app.delete("/regiao/{regiao_id}", status_code=204, tags=["Região"], dependencies=[Depends(verificar_token_obrigatorio)])
def deletar_regiao(regiao_id: int, db: Session = Depends(get_db)):
    print(regiao_id)
    crud.deletar_regiao(db, regiao_id)

# ROTAS DA ENTIDADE TAGS -------------------------------------------------------------------

@app.post("/tags", response_model=TagsResponse, status_code=201, tags=["Tags"], dependencies=[Depends(verificar_token_obrigatorio)])
def criar_tag(dados: TagsCreate, db: Session = Depends(get_db)):
    regiao = crud.buscar_regiao(db, dados.id_regiao)
    if not regiao:
        raise HTTPException(status_code=404, detail="Região informada para a tag não existe")
    return crud.criar_tag(db, dados, dados.id_regiao)

@app.get("/tags", response_model=list[TagsResponse], tags=["Tags"])
def listar_tags(db: Session = Depends(get_db)):
    return crud.listar_tags(db)

@app.get("/tags/{tag_id}", response_model=TagsResponse, tags=["Tags"])
def buscar_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = crud.buscar_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag não encontrada")
    return tag

@app.put("/tags/{tag_id}", response_model=TagsResponse, tags=["Tags"], dependencies=[Depends(verificar_token_obrigatorio)])
def substituir_tag(tag_id: int, dados: TagsCreate, db: Session = Depends(get_db)):
    return crud.substituir_tag(db, tag_id, dados)

@app.delete("/tags/{tag_id}", status_code=204, tags=["Tags"], dependencies=[Depends(verificar_token_obrigatorio)])
def deletar_tag(tag_id: int, db: Session = Depends(get_db)):
    crud.deletar_tag(db, tag_id)
    return Response(status_code=204)

app.mount("/uploads", StaticFiles(directory="Regioes"), name="imagens")

# ROTA DE LOGIN ---------------------

SECRET_KEY = "chave_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

@app.post("/login", response_model=TokenResponse, tags=["Login"])
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(crud.Usuario).filter(crud.Usuario.email == dados.email).first()
    
    if not usuario or not verificar_senha(dados.senha, usuario.senha):
        raise HTTPException(
            status_code=401, 
            detail="Credenciais inválidas. Verifique o e-mail e a senha."
        )
    
    tempo_expiracao = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_token = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "exp": tempo_expiracao
    }
    
    token_jwt = jwt.encode(dados_token, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "access_token": token_jwt,
        "token_type": "bearer"
    }