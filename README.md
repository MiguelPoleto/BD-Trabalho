# Quadra Stats — sistema simples de basquete

Trabalho 6 da disciplina **Tópicos Especiais em Banco de Dados**. Aplicação web em Python/Flask integrada ao MongoDB para cadastrar e consultar equipes, jogadores e partidas.

## Integrantes

- Miguel Santuchi Poleto
- Andrey Magalhaes Silva
- Marcos Lopes Ribeiro

## Requisitos

- Python 3.10 ou superior
- MongoDB Community Server 6.0 ou superior, ou Docker com Docker Compose
- Navegador web atualizado

O MongoDB não está incluído no Python: é necessário iniciar um servidor MongoDB antes de usar o sistema. O Docker Compose abaixo é a forma mais simples de iniciar o banco; alternativamente, instale o MongoDB Community Server para seu sistema operacional seguindo o [guia oficial de instalação](https://www.mongodb.com/docs/manual/installation/). Para instalar Docker e Docker Compose no Ubuntu, siga o [guia oficial do Docker Engine](https://docs.docker.com/engine/install/ubuntu/).

## Como executar

### 1. Inicie o MongoDB

Com Docker instalado, na pasta do projeto execute:

```bash
sudo docker compose up -d
```

Isso inicia o MongoDB na porta `27017` e persiste os dados no volume `mongodb_data`. Para parar o servico sem apagar os dados:

```bash
sudo docker compose down
```

Sem Docker, instale o MongoDB Community Server pelo guia oficial acima e inicie o serviço local. O sistema usa por padrão `mongodb://localhost:27017`.

### 2. Prepare o ambiente Python

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 3. Rode o sistema

```bash
python app.py
```

Abra [http://127.0.0.1:5000](http://127.0.0.1:5000). A aplicação usa o banco `basquete_db` e cria as coleções quando os dados são inseridos.

### Carregar dados de demonstração

Na aplicação, abra o link discreto **Ferramentas de demonstração** no rodapé. Na página aberta, clique em **Carregar dados de demonstração** e confirme a ação. O sistema adiciona quatro equipes, vinte jogadores e oito partidas fictícias.

Os dados de exemplo podem ser carregados novamente: os mesmos registros são atualizados sem duplicação, e os demais dados são mantidos.

Configurações opcionais:

- `MONGODB_URI`: endereco de conexao (padrao `mongodb://localhost:27017`)
- `MONGODB_DATABASE`: nome do banco (padrao `basquete_db`)
- `SECRET_KEY`: chave de sessão do Flask
- `FLASK_DEBUG=1`: ativa o modo de depuracao local

Exemplo Linux/macOS:

```bash
MONGODB_URI="mongodb://localhost:27017" MONGODB_DATABASE="basquete_db" python app.py
```

## O que o sistema faz

- CRUD completo (inserir, listar, atualizar e remover) para equipes, jogadores e partidas.
- Valida campos obrigatórios, placares e referências entre coleções.
- Impede remover uma equipe que ainda tenha jogadores ou partidas vinculadas.
- Exibe um painel com contagens e partidas recentes.
- Oferece cinco consultas MongoDB:
  1. Elenco de jogadores por equipe.
  2. Jogadores por posição.
  3. Partidas dentro de um período.
  4. Histórico de partidas de uma equipe (mandante ou visitante).
  5. Partidas por resultado: vitoria do mandante ou vitoria do visitante.

## Modelo de dados

| Colecao | Campos principais | Relacionamentos |
| --- | --- | --- |
| `teams` | `name`, `city`, `coach` | Equipe |
| `players` | `name`, `number`, `position`, `team_id` | `team_id` referencia `teams._id` |
| `games` | `home_team_id`, `away_team_id`, `home_score`, `away_score`, `played_at`, `venue` | As duas equipes referenciam `teams._id` |

Os relacionamentos entre documentos são armazenados como `ObjectId`, e as consultas usam filtros e comparações do MongoDB.

## Testes

Os testes usam `mongomock`, um banco em memória, e não precisam de um servidor MongoDB ativo:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Entrega compactada

Para criar o arquivo a enviar ao AVA no Linux/macOS:

```bash
zip -r trabalho6.zip app.py seed.py templates static tests requirements.txt requirements-dev.txt docker-compose.yml README.md .gitignore
```

Não inclua a pasta `.venv` nem dados locais do MongoDB no arquivo.

> Este projeto é um trabalho acadêmico para execução local. Não possui autenticação, proteção CSRF ou configuração de produção; não o exponha diretamente à internet.
