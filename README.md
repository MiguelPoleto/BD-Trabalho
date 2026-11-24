# Quadra Stats — sistema simples de basquete

Trabalho 6 da disciplina **Tópicos Especiais em Banco de Dados**. Aplicação web em Python/Flask integrada ao MongoDB para cadastrar e consultar equipes, jogadores e partidas.

## Integrantes

- Miguel Santuchi Poleto
- Andrey Magalhaes Silva
- Marcos Lopes Ribeiro

## Requisitos

- Docker Engine e Docker Compose (modo recomendado); ou
- Python 3.10 ou superior e MongoDB Community Server 6.0 ou superior (modo local)
- Navegador atualizado

Para instalar Docker no Ubuntu, siga o [guia oficial do Docker Engine](https://docs.docker.com/engine/install/ubuntu/). Sem Docker, instale o MongoDB Community Server conforme o [guia oficial](https://www.mongodb.com/docs/manual/installation/).

## Executar a aplicação com Docker

Na pasta do projeto, suba os serviços:

```bash
sudo docker compose up -d --build
```

O Compose constrói a aplicação, prepara um ambiente virtual Python **dentro da imagem Docker**, inicia o MongoDB e aguarda o banco ficar pronto antes de subir o site. Acesse [http://127.0.0.1:5000](http://127.0.0.1:5000).

Se a porta `5000` já estiver ocupada, escolha outra porta no computador:

```bash
sudo env APP_PORT=5050 docker compose up -d --build
```

Nesse caso, acesse [http://127.0.0.1:5050](http://127.0.0.1:5050).

Para conferir os serviços e acompanhar os registros da aplicação:

```bash
sudo docker compose ps
sudo docker compose logs -f app
```

Para encerrar sem apagar os dados:

```bash
sudo docker compose down
```

Os dados do MongoDB ficam no volume `mongodb_data`. O ambiente virtual do container fica em `/opt/venv`; não é necessário instalar Python nem pacotes no computador para usar esta opção.

### Executar somente o banco no Docker

Se preferir executar o Flask no computador, inicie somente o MongoDB:

```bash
sudo docker compose up -d mongodb
```

Prepare o ambiente Python do projeto e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Abra [http://127.0.0.1:5000](http://127.0.0.1:5000). A aplicação usa o banco `basquete_db`, no endereço padrão `mongodb://localhost:27017`.

Também é possível instalar o MongoDB Community Server diretamente no computador e executar a aplicação no ambiente Python local.

## Dados de demonstração e filtros

Na aplicação, abra **Ferramentas de demonstração** no rodapé. Clique em **Carregar dados de demonstração** e confirme: são adicionadas quatro equipes, vinte jogadores e oito partidas fictícias. A ação pode ser repetida sem duplicar exemplos ou apagar outros registros.

As listas da visão geral, equipes, jogadores, partidas e resultados das consultas têm busca instantânea com sugestões. Os filtros de cidade, posição, equipe, resultado e período podem ser combinados; a busca não diferencia letras acentuadas. Esses filtros rápidos atuam sobre os registros exibidos na tela. As cinco consultas da página **Consultas** são executadas no MongoDB.

## Funcionalidades e buscas

- CRUD completo (inserir, listar, atualizar e remover) para equipes, jogadores e partidas.
- Validação de campos obrigatórios, placares e referências entre coleções.
- Proteção contra a remoção de equipes que ainda tenham jogadores ou partidas vinculadas.
- Painel com contagens, partidas recentes, busca instantânea e filtros.
- Cinco consultas MongoDB:
  1. Elenco de jogadores por equipe (`team_id`).
  2. Jogadores por posição.
  3. Partidas em um período (`$gte` / `$lte`).
  4. Histórico de uma equipe como mandante ou visitante (`$or`).
  5. Vitórias do mandante ou visitante, comparando os placares (`$expr`).

## Modelo de dados

| Coleção | Campos principais | Relacionamentos |
| --- | --- | --- |
| `teams` | `name`, `city`, `coach` | Dados da equipe |
| `players` | `name`, `number`, `position`, `team_id` | `team_id` referencia `teams._id` |
| `games` | `home_team_id`, `away_team_id`, `home_score`, `away_score`, `played_at`, `venue` | As duas equipes referenciam `teams._id` |

Os relacionamentos entre documentos são armazenados como `ObjectId`. A carga de demonstração recria os documentos de exemplo com identificadores estáveis, para poder ser repetida sem duplicações.

## Consultar o banco durante a apresentação

Com os serviços Docker em execução, abra o shell do MongoDB:

```bash
sudo docker compose exec mongodb mongosh basquete_db
```

No prompt do `mongosh`, use:

```javascript
show collections
db.teams.find().limit(3)
db.players.findOne()
db.games.findOne()
```

Digite `exit` para sair do shell.

## Testes

Os testes usam `mongomock`, um banco em memória, e não precisam de um servidor MongoDB ativo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Enviar o trabalho

Crie o ZIP na pasta do projeto:

```bash
zip -r trabalho6.zip app.py seed.py Dockerfile .dockerignore templates static tests requirements.txt requirements-dev.txt docker-compose.yml README.md .gitignore
```

O arquivo contém o código, a configuração para recriar o banco e os dados de demonstração; não inclua `.venv` nem os arquivos de dados internos do MongoDB.

> Projeto acadêmico para execução local. Não possui autenticação, proteção CSRF ou configuração de produção; não o exponha diretamente à internet.
