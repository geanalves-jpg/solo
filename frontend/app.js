const API_URL = "http://127.0.0.1:8000"; // Ajuste se a porta do seu Uvicorn for diferente

// Função para decodificar a parte de dados (payload) do Token JWT
function extrairIdDoToken(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('0' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        const payload = JSON.parse(jsonPayload);
        return payload.sub; // Retorna o ID do usuário que está logado
    } catch (error) {
        console.error("Erro ao decodificar o token:", error);
        return "1"; // Valor padrão caso falhe
    }
}

// Controle de Telas (Abas)
function mudarAba(idAba) {
    document.querySelectorAll('.aba-conteudo').forEach(aba => aba.classList.add('hidden'));
    document.getElementById(idAba).classList.remove('hidden');
    
    const titulos = {
        'login-aba': 'Autenticação',
        'regioes-aba': 'Gerenciamento de Regiões e Árvores de Mapas'
    };
    document.getElementById('titulo-pagina').innerText = titulos[idAba] || 'Dashboard';
}

// Auxiliares para o LocalStorage (Token JWT)
function guardarToken(token) {
    localStorage.setItem('token_mapas', token);
    document.getElementById('status-token').innerText = "Status: Autenticado 🟢";
}

// Remove o token ativo
function obterToken() {
    return localStorage.getItem('token_mapas');
}

function deslogar() {
    localStorage.removeItem('token_mapas');
    document.getElementById('status-token').innerText = "Status: Não autenticado 🔴";
    alert("Token removido. Logue novamente se for fazer requisições protegidas.");
    mudarAba('login-aba');
}

// Verificar se o usuário já possui token salvo ao carregar a página
if(obterToken()) {
    document.getElementById('status-token').innerText = "Status: Autenticado 🟢";
}

// -------------------------------------------------------------
// ROTA: LOGIN
// -------------------------------------------------------------
async function executarLogin() {
    const email = document.getElementById('login-email').value;
    const senha = document.getElementById('login-senha').value;

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, senha })
        });

        if (!response.ok) {
            const erro = await response.json();
            throw new Error(erro.detail || "Erro de login");
        }

        const dados = await response.json();
        guardarToken(dados.access_token);
        alert("Login efetuado com sucesso!");
        mudarAba('regioes-aba');
        carregarRegioes();
    } catch (error) {
        alert(`Falha no Login: ${error.message}`);
    }
}

// -------------------------------------------------------------
// ROTA: CADASTRO EXTERNO (AUTO-CADASTRO)
// -------------------------------------------------------------
async function executarCadastro(event) {
    event.preventDefault();

    const nome = document.getElementById('cadastro-nome').value;
    const email = document.getElementById('cadastro-email').value;
    const senha = document.getElementById('cadastro-senha').value;
    const descricao = document.getElementById('cadastro-descricao').value;

    try {
        // Envia os dados para criar o usuário no banco
        const responseCadastro = await fetch(`${API_URL}/usuario`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, email, senha, descricao })
        });

        if (!responseCadastro.ok) {
            const erro = await responseCadastro.json();
            throw new Error(erro.mensagem || "Não foi possível realizar o cadastro. Verifique os critérios dos campos.");
        }

        alert("Conta criada com sucesso! Realizando login automático...");

        // Faz o login automático com a conta criada
        const responseLogin = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, senha })
        });

        if (!responseLogin.ok) {
            throw new Error("Usuário criado, mas houve uma falha ao gerar o token de acesso. Tente logar manualmente.");
        }

        const dadosLogin = await responseLogin.json();
        guardarToken(dadosLogin.access_token);
        
        document.getElementById('form-auto-cadastro').reset();
        mudarAba('regioes-aba');
        carregarRegioes();

    } catch (error) {
        alert(`Erro no cadastro: ${error.message}`);
    }
}

// -------------------------------------------------------------
// OPERAÇÕES: REGIÕES
// -------------------------------------------------------------
async function carregarRegioes() {
    const listaDiv = document.getElementById('lista-regioes');
    listaDiv.innerHTML = `<p class="text-gray-500">Carregando regiões...</p>`;

    try {
        const response = await fetch(`${API_URL}/regiao`);
        const regioes = await response.ok ? await response.json() : [];
        
        listaDiv.innerHTML = "";
        if (regioes.length === 0) {
            listaDiv.innerHTML = `<p class="text-gray-500 col-span-3">Nenhuma região encontrada no momento.</p>`;
            return;
        }

        regioes.forEach(reg => {
            const urlImagem = `${API_URL}/uploads/${reg.id}/${reg.id}.png`;

            const card = document.createElement('div');
            card.className = "bg-white rounded-lg shadow-md overflow-hidden border border-gray-200 flex flex-col justify-between";
            card.innerHTML = `
                <div>
                    <div class="h-40 bg-gray-200 relative overflow-hidden">
                        <img src="${urlImagem}" alt="Imagem de ${reg.nome}" class="w-full h-full object-cover" onerror="this.src='https://placehold.co/400x200?text=Sem+Imagem'">
                        <span class="absolute top-2 right-2 bg-slate-900/80 text-white text-xs px-2 py-1 rounded">ID: ${reg.id}</span>
                    </div>
                    <div class="p-4 space-y-2">
                        <h4 class="font-bold text-lg text-gray-800">${reg.nome}</h4>
                        <p class="text-gray-600 text-sm">${reg.descricao || 'Sem descrição cadastrada.'}</p>
                        <div class="text-xs text-gray-500 space-y-1">
                            <p><strong>Pai estrutural (ID):</strong> ${reg.id_regiao_pai || 'Raiz / Nenhum'}</p>
                            <p><strong>Criado pelo Usuário (ID):</strong> ${reg.id_criador}</p>
                        </div>
                    </div>
                </div>
                <div class="p-4 bg-gray-50 border-t flex justify-end">
                    <button onclick="deletarRegiao(${reg.id})" class="text-xs text-red-600 border border-red-200 bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded transition">
                        Excluir Região
                    </button>
                </div>
            `;
            listaDiv.appendChild(card);
        });
    } catch (error) {
        listaDiv.innerHTML = `<p class="text-red-500 col-span-3">Erro ao conectar com o servidor.</p>`;
    }
}

async function salvarRegiao(event) {
    event.preventDefault();
    const token = obterToken();
    if (!token) {
        alert("Você precisa fazer login antes de enviar uma região (Rota Protegida).");
        return;
    }

    // 1. EXTRAI O ID DO TOKEN E ATUALIZA O CAMPO OCULTO NOS BASTIDORES
    const idUsuarioLogado = extrairIdDoToken(token);
    document.getElementById('regiao-criador').value = idUsuarioLogado;

    const formData = new FormData();
    formData.append('nome', document.getElementById('regiao-nome').value);
    
    // 2. ISSO ENVIA O ID CORRETO EXTRAÍDO DO SEU LOGIN PARA O BACKEND
    formData.append('id_criador', document.getElementById('regiao-criador').value); 
    
    formData.append('descricao', document.getElementById('regiao-descricao').value);
    
    const idPai = document.getElementById('regiao-pai').value;
    if (idPai) formData.append('id_regiao_pai', idPai);

    const inputImagem = document.getElementById('regiao-imagem');
    if (inputImagem.files[0]) {
        formData.append('imagem', inputImagem.files[0]);
    }

    try {
        const response = await fetch(`${API_URL}/regiao`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (!response.ok) {
            const erro = await response.json();
            throw new Error(erro.detail || "Erro desconhecido ao salvar");
        }

        alert("Região adicionada e mapa.json gerado!");
        document.getElementById('form-regiao').reset();
        carregarRegioes();
    } catch (error) {
        alert(`Erro: ${error.message}`);
    }
}

async function deletarRegiao(id) {
    if (!confirm("Tem certeza que deseja apagar essa região?")) return;
    const token = obterToken();
    
    try {
        const response = await fetch(`${API_URL}/regiao/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error("Não foi possível deletar. Certifique-se de estar autenticado.");
        alert("Região removida.");
        carregarRegioes();
    } catch (error) {
        alert(error.message);
    }
}