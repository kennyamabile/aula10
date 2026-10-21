# Aula 10 — ChatBot multiagente com n8n (CLARA)

Chatbot de atendimento do **Núcleo de Convênios** (órgão hipotético): a orquestradora
**CLARA** delega a três sub-agentes — INFO (dados fixos), CONVENIOS (RAG sobre os PDFs)
e ATENDIMENTO (grava chamado numa Data table).

## Estrutura

```
convenios/                  3 convênios fictícios (021/2026, 034/2026, 047/2026)
workflows/
  ingestao-convenios.json   Formulário -> PDF -> texto -> trechos -> embeddings -> base "convenios"
  clara-multiagente.json    Chat -> CLARA (gpt-oss-120b) -> sub-agentes (gpt-oss-20b)
scripts/
  gerar_convenios.py        Recria os PDFs (Python puro, sem dependências)
  gerar_workflows.py        Recria os JSON dos workflows
testes.md                   Tabela dos 8 cenários da seção 6.2
```

## Dependências

| Peça | Onde | Observação |
|------|------|------------|
| n8n 2.42.5 | Docker, `../aula08/docker-compose.yml` | http://localhost:5678 |
| Ollama + `nomic-embed-text` | Windows, porta 11434 | Embeddings locais |
| Groq (`openai/gpt-oss-120b` e `openai/gpt-oss-20b`) | Internet | Chave em https://console.groq.com/keys |

## Credenciais no n8n

| Nome | Tipo | Campo |
|------|------|-------|
| `Groq` | Groq | API Key |
| `Ollama` | Ollama | Base URL `http://host.docker.internal:11434` |

## Data table `chamados`

Colunas texto: `protocolo`, `nome`, `email`, `descricao`, `registrado_em`.

## Lembrete

A base vetorial (Simple Vector Store) e a memória do chat vivem na memória do n8n:
depois de reiniciar o contêiner, reenvie os PDFs em http://localhost:5678/form/base-convenios.

Os dados enviados ao Groq saem da máquina: use só documentos fictícios ou públicos.
