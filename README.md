# P&D-Power-Solis
Repositório de desenvolvimento do projeto Power Solis

# Descrição do Projeto

Este repositório implementa um sistema completo para tratamento dos dados, extração de atributos, modelagem e inferência de parâmetros relacionados ao monitoramento de equipamentos de potência.

## Descrição do Sistema

O projeto é estruturado em torno dos scripts 

.
.
.


Estes devem ser rodados nesta sequência para possibilitar a preparação dos dados e geração dos modelos.

Alternativamente pode ser usada o script `main.py` que faz todo o processo automaticamente. # ainda vai ser adicionado


## Pipenv

O Pipenv é uma ferramenta que combina o uso de ambientes virtuais e o controle de dependências em projetos Python. Ele foi criado para substituir o uso separado do pip e do virtualenv, oferecendo uma abordagem mais organizada e segura para lidar com bibliotecas externas.

Ao utilizar o Pipenv, cada projeto Python possui seu próprio ambiente isolado, o que evita conflitos de versões entre diferentes projetos. Além disso, os arquivos Pipfile e Pipfile.lock permitem registrar com precisão os pacotes instalados, garantindo que o ambiente possa ser reproduzido de forma idêntica em outras máquinas.

### 0. Requisitos Iniciais: Instalar o Python

- Acesse: [https://www.python.org/downloads/windows](https://www.python.org/downloads/windows)
- Baixe a versão mais recente do **Python 3.x** para Windows.
- Durante a instalação, marque a opção ✅ **“Add Python to PATH”**.
- Conclua a instalação.

---

### 1. Utilizando um Pipfile.lock Existente

Utilizar este processo ao abrir um projeto com Pipfile e Pipfile.lock já definidos (por exemplo, clonado de um repositório).

1. Abrir o terminal e acessar o diretório do projeto:

```sh
cd caminho\do\projeto
```

2. Instalar o Pipenv, se necessário:

```sh
pip install --user pipenv
```

3. Instalar todas as dependências já definidas:

```sh
pipenv install
```

Este comando utiliza o Pipfile.lock para configurar o ambiente com versões consistentes de pacotes.

### 2. Criando um Projeto do Zero com Pipenv

Use esta etapa para iniciar um novo projeto Python com gerenciamento de dependências. **Pule esta etapa se o projeto já existir os arquivos `Pipfile` e `Pipfile.lock`**.

1. Abrir o terminal (Prompt de Comando ou PowerShell).
2. Navegar até o diretório do projeto:

```sh
cd caminho\para\seu\projeto
```

3. Instalar o Pipenv (somente na primeira vez):

```sh
pip install --user pipenv
```

4. Criar o ambiente virtual do projeto:

```sh
pipenv install
```

5. Instalar dependências do projeto:

```sh
pipenv install numpy matplotlib
```

Isso criará os arquivos:

- `Pipfile` – descreve o ambiente.
- `Pipfile.lock` – define versões específicas dos pacotes.

6. Para ativar o ambiente virtual:

```sh
pipenv shell
```

### 3. Criando ambiente virtual

Obtendo o caminho do ambiente virtual (observe que não será criado na pasta do projeto, mas sim em outra localização)

No terminal, executar:

```sh
pipenv --venv
```

Copiar o caminho retornado, por exemplo:

```sh
C:\Users\usuario\.virtualenvs\nome_projeto-abc123
```

### 4. Configuração no VS Code

1. Abrir o projeto no VS Code.

2. Pressionar `Ctrl+Shift+P` → selecionar `Python: Select Interpreter`.

3. Escolher Enter interpreter path.

4. Inserir o caminho completo: 

`C:\Users\usuario\.virtualenvs\nome_projeto-abc123\Scripts\python.exe`

### 5. Configurando o Interpretador no Spyder

1. Abrir o Spyder.

2. Acessar: `Tools → Preferences → Python Interpreter`.

3. Selecionar a opção Use the following interpreter.

4. Localizar e selecionar o caminho do interpretador: 

`C:\Users\usuario\.virtualenvs\nome_projeto-abc123\Scripts\python.exe`

5. Reiniciar o Spyder.

## API HTTP com FastAPI

O projeto tambem pode ser executado como API HTTP. A API reaproveita o
`DiagnosticPipeline` existente e expoe endpoints para diagnostico individual
e em lote.

### Instalar dependencias

```sh
pip install --user pipenv
pipenv install
```

### Executar servidor

```sh
pipenv run uvicorn api.main:app --reload
```

Depois acesse:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/api/v1/ready`

### Diagnostico individual

```sh
curl -X POST http://127.0.0.1:8000/api/v1/diagnosticos ^
  -H "Content-Type: application/json" ^
  -d "{\"id_equipamento\":\"TC-550kV-001\",\"tangente_perdas\":0.7,\"corrente\":2000.0,\"temperatura_ambiente\":30.0,\"ponto_quente_externo\":45.0,\"horas_operacao\":87600.0,\"tensao_nominal\":550.0}"
```

### Configuracao por ambiente

Por padrao, a API usa `models/modelo_hotspot.pkl`. Para apontar outro modelo:

```sh
set POWER_SOLIS_MODEL_HOTSPOT=D:\caminho\para\modelo_hotspot.pkl
```

Variaveis opcionais:

- `POWER_SOLIS_MODEL_CLUSTERING`
- `POWER_SOLIS_TENSAO_ENSAIO_V`
- `POWER_SOLIS_VIDA_REF_ANOS`
- `POWER_SOLIS_TEMP_REF_C`
- `POWER_SOLIS_P_MONTSINGER`
