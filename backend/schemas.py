from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

#chemas de login--------------

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

    
#schemas do usuario --------------

class UsuarioCreate(BaseModel):
    nome: str
    @field_validator("nome")
    @classmethod
    def validar_usuario(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("O nome deve ter pelo menos 3 caracteres")
        return v
    
    descricao: Optional[str] = None
    email: EmailStr

    senha: str
    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres")
        return v


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    email: str
    senha: str 
    model_config = ConfigDict(from_attributes=True) #pra ler os objetos do bd

class UsuarioPaginadoResponse(BaseModel):
    data: list[UsuarioResponse] #lista com os usuários daquela página específica
    total: int                  #quantidade total de registros
    page: int                   #número da página atual
    limit: int                  #limite de itens por página
    pages: int                  #número total de páginas disponíveis

#schemas da região------------------
class RegiaoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    id_regiao_pai: Optional[int] = None
    caminho: Optional[str] = None
    id_criador: int

class RegiaoResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    id_regiao_pai: Optional[int] = None
    caminho: Optional[str] = None
    id_criador: int
    usuario_criador: Optional[UsuarioResponse] = None
    model_config = ConfigDict(from_attributes=True) #pra ler os objetos do bd

class RegiaoUpdate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    id_regiao_pai: Optional[int] = None
    id_criador: int

#schemas da tags------------------------

class TagsCreate(BaseModel):
    nome: str
    id_regiao: int
    

class TagsResponse(BaseModel):
    id: int
    nome: str
    id_regiao: Optional[int] = None
    regiao: Optional[RegiaoResponse] = None
    model_config = ConfigDict(from_attributes=True) #pra ler os objetos do bd



#schemas da relacao ---------------------


