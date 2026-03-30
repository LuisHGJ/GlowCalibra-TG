# 📦 Descrição básica do software

- O **core** foi projetado para ser a implementação do processamento de imagens de maneira **individual** e **isolada** da API.  

- As funções estão **separadas por responsabilidade** em cada diretório.  
  A pasta `testes/` é ""provisória"" e contém um pipeline orquestrando as funções de maneira correta.  

- O processo de criação do processamento não foi documentado, contudo a clareza das funções do **OpenCV** torna simples deduzir.  

- Por fim, o projeto foi pensado para ser **portável** para uma API (seja função por função ou o pipeline inteiro).  
  Desse modo, como o **core** é separado da API, também é possível desenvolver um código para **CLI**.  

---

# 🚀 Como utilizar após clonar o repositório

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Atualizar o arquivo de dependências (se preciso)
```bash
pip freeze > requirements.txt
```

### 3. Rodar o arquivo "provisório" de testes
```bash
python3 -m core.testes.pipeline
```

---

## ⚠️ Observações
- Todos os comandos são relativos e devem ser rodados no **diretório raiz do projeto**.  
- Qualquer diferença será incoerente com os pacotes e caminhos relativos criados. 
- TODOS os comandos citados nesse documento são relativos ao sistema Linux, possuindo sempre uma equivalencia em Windows.


## Te poupando dor de cabeça
- Para manter a coerência e não entupir o teu pc de dependências, use um venv.
- Criar venv: python3 -m venv venv
- Ativar venv: source ./venv/bin/activate
- Desativar venv: deactivate