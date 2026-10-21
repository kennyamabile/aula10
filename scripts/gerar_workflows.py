"""Gera os dois workflows da Aula 10 no formato de importacao do n8n 2.42.

Saida:
  workflows/ingestao-convenios.json
  workflows/clara-multiagente.json

As credenciais (Groq e Ollama) nao vao no JSON: depois de importar,
selecione-as em cada no de modelo e de embeddings.

Uso: python scripts/gerar_workflows.py
"""
import json
import uuid
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "workflows"


# Credenciais criadas no n8n com estes ids (ver LEIA-ME.md). Numa instalacao
# sem elas, o n8n importa o workflow e pede para escolher a credencial no no.
CREDENCIAIS = {
    "@n8n/n8n-nodes-langchain.lmChatGroq": {"groqApi": {"id": "aula10Groq000001", "name": "Groq"}},
    "@n8n/n8n-nodes-langchain.embeddingsOllama": {"ollamaApi": {"id": "aula10Ollama0001", "name": "Ollama"}},
}


def no(nome, tipo, versao, posicao, parametros):
    item = {
        "parameters": parametros,
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "aula10/" + nome)),
        "name": nome,
        "type": tipo,
        "typeVersion": versao,
        "position": posicao,
    }
    if tipo in CREDENCIAIS:
        item["credentials"] = CREDENCIAIS[tipo]
    return item


def liga(conexoes, origem, destino, tipo="main"):
    conexoes.setdefault(origem, {}).setdefault(tipo, [[]])[0].append(
        {"node": destino, "type": tipo, "index": 0}
    )


def workflow(id_, nome, nos, conexoes):
    return {
        "id": id_,
        "name": nome,
        "nodes": nos,
        "connections": conexoes,
        "pinData": {},
        "settings": {"executionOrder": "v1"},
        "meta": {"templateCredsSetupCompleted": False},
        "tags": [],
    }


# ---------------------------------------------------------------- ingestao

CODIGO_UM_ITEM = """// O formulário entrega todos os PDFs num único item (Documentos_0, Documentos_1, ...).
// Aqui cada arquivo vira um item, com o binário em "data" e o nome do arquivo no JSON.
const saida = [];
for (const item of $input.all()) {
  for (const chave of Object.keys(item.binary ?? {})) {
    const arquivo = item.binary[chave];
    saida.push({ json: { arquivo: arquivo.fileName }, binary: { data: arquivo } });
  }
}
return saida;"""


def ingestao():
    nos = [
        no("Enviar convênios", "n8n-nodes-base.formTrigger", 2.5, [0, 0], {
            "formTitle": "Base de convênios",
            "formDescription": "Envie os PDFs dos convênios. O envio substitui a base anterior.",
            "formFields": {"values": [{
                "fieldName": "documentos",
                "fieldLabel": "Documentos",
                "fieldType": "file",
                "multipleFiles": True,
                "acceptFileTypes": ".pdf",
                "requiredField": True,
            }]},
            "options": {"path": "base-convenios"},
        }),
        no("Um item por arquivo", "n8n-nodes-base.code", 2, [220, 0], {
            "jsCode": CODIGO_UM_ITEM,
        }),
        no("Extrair texto", "n8n-nodes-base.extractFromFile", 1.1, [440, 0], {
            "operation": "pdf",
            "options": {},
        }),
        no("Inserir na base", "@n8n/n8n-nodes-langchain.vectorStoreInMemory", 1.3, [680, 0], {
            "mode": "insert",
            "memoryKey": {"__rl": True, "mode": "list", "value": "convenios"},
            "embeddingBatchSize": 50,
            "clearStore": True,
        }),
        no("Embeddings", "@n8n/n8n-nodes-langchain.embeddingsOllama", 1, [600, 220], {
            "model": "nomic-embed-text:latest",
        }),
        no("Carregar documento", "@n8n/n8n-nodes-langchain.documentDefaultDataLoader", 1.1, [820, 220], {
            "dataType": "json",
            "jsonMode": "expressionData",
            "jsonData": "={{ $json.text }}",
            "textSplittingMode": "custom",
            "options": {"metadata": {"metadataValues": [
                {"name": "arquivo", "value": "={{ $('Um item por arquivo').item.json.arquivo }}"},
                {"name": "convenio", "value": "={{ $json.text.match(/N[º°o]\\s*(\\d+\\/\\d{4})/)?.[1] ?? '' }}"},
            ]}},
        }),
        no("Dividir em trechos", "@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter", 1, [900, 420], {
            "chunkSize": 1000,
            "chunkOverlap": 150,
            "options": {},
        }),
        no("Base atualizada", "n8n-nodes-base.form", 2.3, [1060, 0], {
            "operation": "completion",
            "completionTitle": "Base atualizada",
            "completionMessage": "={{ $('Um item por arquivo').all().length }} arquivo(s) indexado(s) em {{ $input.all().length }} trecho(s).",
            "options": {},
        }),
    ]
    c = {}
    liga(c, "Enviar convênios", "Um item por arquivo")
    liga(c, "Um item por arquivo", "Extrair texto")
    liga(c, "Extrair texto", "Inserir na base")
    liga(c, "Inserir na base", "Base atualizada")
    liga(c, "Embeddings", "Inserir na base", "ai_embedding")
    liga(c, "Carregar documento", "Inserir na base", "ai_document")
    liga(c, "Dividir em trechos", "Carregar documento", "ai_textSplitter")
    return workflow("aula10Ingestao01", "Aula 10 - Ingestão dos convênios", nos, c)


# ---------------------------------------------------------------- CLARA

PROMPT_CLARA = """Você é a CLARA, assistente virtual do Núcleo de Convênios, um órgão hipotético usado em aula.

Responda sempre em português do Brasil, em no máximo três parágrafos curtos. Nunca liste os convênios da base: informe só o convênio cujo número a pessoa deu. Não invente informação: o que você sabe sobre o Núcleo e sobre os convênios vem das ferramentas.

FERRAMENTAS
- Sub-agente_INFO: endereço, horário, telefone, e-mail e serviços do Núcleo.
- Sub-agente_CONVENIOS: dados de um convênio (partes, representantes, objeto, valor, data). Só acione depois que a pessoa informar o número do convênio, no formato NNN/AAAA. Sem o número, peça o número e não acione a ferramenta. Envie a pergunta completa, com o número e o dado pedido, por exemplo "valor e objeto do convênio 047/2026".
- Sub-agente_ATENDIMENTO: registra um chamado para a equipe humana. Antes de acionar, obtenha o nome completo, o e-mail e a descrição do problema; a descrição pode já ter vindo numa mensagem anterior da conversa, e então não peça de novo. Passe os três na mensagem para a ferramenta.

ROTEAMENTO
- Saudação ou pergunta sobre você: responda direto, sem ferramenta, e apresente-se como CLARA.
- Endereço, horário, contato ou serviços: Sub-agente_INFO.
- Convênio, parceria, valor ou vigência: peça o número; com o número, Sub-agente_CONVENIOS.
- Reclamação, caso que as outras ferramentas não resolvem ou pedido para falar com uma pessoa: colete os três dados e acione Sub-agente_ATENDIMENTO. Ao final, informe o protocolo devolvido."""

PROMPT_INFO = """Você responde perguntas sobre o Núcleo de Convênios usando SOMENTE os dados abaixo. Se a resposta não estiver aqui, diga que não tem essa informação.

DADOS DO NÚCLEO (fictícios)
Nome: Núcleo de Convênios
Endereço: Rua das Parcerias, 100, Centro, Vale Verde/MT
Telefone: (00) 0000-0000
E-mail: atendimento@nucleo-convenios.example
Atendimento presencial e por telefone: segunda a sexta, das 8h às 17h
Chat e e-mail: 24 horas, com resposta humana no próximo dia útil
Serviços: consulta a convênios vigentes, orientação sobre prestação de contas, protocolo de documentos, agendamento de reuniões com a equipe técnica"""

PROMPT_CONVENIOS = """Você consulta os documentos dos convênios do Núcleo.

- Busque na ferramenta Base_de_convenios com o número do convênio e o dado pedido, por exemplo "047/2026 valor global".
- Cada trecho traz nos metadados o número do convênio (campo convenio) e o arquivo de origem (campo arquivo). O valor, o objeto e a data podem estar num trecho que não repete o número no texto: é o campo convenio que diz a que convênio o trecho pertence.
- Se o dado pedido não aparecer nos trechos do convênio, faça uma nova busca só com o assunto, por exemplo "valor global", e use os trechos cujo campo convenio é o número pedido.
- Responda só com o que os trechos dizem e cite o arquivo. Nunca estime nem complete valores, nomes ou datas: se o dado não estiver nos trechos, diga que não o encontrou.
- Se nenhum trecho tiver o campo convenio igual ao número pedido, diga apenas que não há registro desse número na base.
- Nunca cite nem resuma outros convênios além do pedido, mesmo que apareçam nos trechos."""

PROMPT_ATENDIMENTO = """Você registra chamados para a equipe humana do Núcleo de Convênios.

- Use a ferramenta Registrar_chamado com o nome completo, o e-mail e a descrição recebidos.
- Se faltar algum dos três dados, não registre: responda quais dados faltam.
- Depois de registrar, responda com o protocolo devolvido pela ferramenta e diga que a equipe responde no próximo dia útil."""

PEDIDO = "={{ $fromAI('Prompt__User_Message_', `Pedido em linguagem natural, com os dados que o sub-agente precisa`, 'string') }}"


def sub_agente(nome, posicao, descricao, prompt):
    return no(nome, "@n8n/n8n-nodes-langchain.agentTool", 3, posicao, {
        "toolDescription": descricao,
        "text": PEDIDO,
        "options": {"systemMessage": prompt, "maxIterations": 4},
    })


def coluna(nome):
    return {
        "id": nome, "displayName": nome, "required": False, "defaultMatch": False,
        "display": True, "type": "string", "readOnly": False, "removed": False,
    }


def clara():
    colunas = {
        "protocolo": "={{ 'CH-' + $now.toFormat('yyyyMMdd-HHmmss') }}",
        "nome": "={{ $fromAI('nome', `Nome completo da pessoa`, 'string') }}",
        "email": "={{ $fromAI('email', `E-mail da pessoa`, 'string') }}",
        "descricao": "={{ $fromAI('descricao', `Descrição do problema`, 'string') }}",
        "registrado_em": "={{ $now.toISO() }}",
    }
    nos = [
        no("Mensagem recebida", "@n8n/n8n-nodes-langchain.chatTrigger", 1.4, [0, 0], {"options": {}}),
        no("CLARA", "@n8n/n8n-nodes-langchain.agent", 3.1, [260, 0], {
            "options": {"systemMessage": PROMPT_CLARA},
        }),
        no("Modelo da CLARA", "@n8n/n8n-nodes-langchain.lmChatGroq", 1, [0, 260], {
            "model": "openai/gpt-oss-120b",
            "options": {"temperature": 0.2},
        }),
        no("Memória", "@n8n/n8n-nodes-langchain.memoryBufferWindow", 1.3, [180, 260], {
            "contextWindowLength": 10,
        }),
        sub_agente("Sub-agente INFO", [400, 260],
                   "Responde sobre endereço, horário, telefone, e-mail e serviços do Núcleo de Convênios.",
                   PROMPT_INFO),
        sub_agente("Sub-agente CONVENIOS", [640, 260],
                   "Consulta os documentos dos convênios: partes, representantes, objeto, valor e data. "
                   "Envie a pergunta completa, com o número do convênio e o dado pedido.",
                   PROMPT_CONVENIOS),
        sub_agente("Sub-agente ATENDIMENTO", [900, 260],
                   "Registra um chamado para a equipe humana. Envie na mensagem o nome completo, "
                   "o e-mail e a descrição do problema.",
                   PROMPT_ATENDIMENTO),
        no("Modelo dos sub-agentes", "@n8n/n8n-nodes-langchain.lmChatGroq", 1, [480, 520], {
            "model": "openai/gpt-oss-20b",
            "options": {"temperature": 0.2},
        }),
        no("Base de convenios", "@n8n/n8n-nodes-langchain.vectorStoreInMemory", 1.3, [720, 520], {
            "mode": "retrieve-as-tool",
            "toolDescription": "Busca por semelhança nos trechos dos convênios. Devolve os trechos mais "
                               "próximos da consulta, com o arquivo de origem.",
            "memoryKey": {"__rl": True, "mode": "list", "value": "convenios"},
            "topK": 4,
            "includeDocumentMetadata": True,
        }),
        no("Embeddings", "@n8n/n8n-nodes-langchain.embeddingsOllama", 1, [720, 740], {
            "model": "nomic-embed-text:latest",
        }),
        no("Registrar chamado", "n8n-nodes-base.dataTableTool", 1.1, [1000, 520], {
            "descriptionType": "manual",
            "toolDescription": "Grava um chamado na tabela chamados e devolve o protocolo.",
            "dataTableId": {"__rl": True, "mode": "name", "value": "chamados"},
            "columns": {
                "mappingMode": "defineBelow",
                "value": colunas,
                "matchingColumns": [],
                "schema": [coluna(n) for n in colunas],
                "attemptToConvertTypes": False,
                "convertFieldsToString": False,
            },
            "options": {},
        }),
    ]
    c = {}
    liga(c, "Mensagem recebida", "CLARA")
    liga(c, "Modelo da CLARA", "CLARA", "ai_languageModel")
    liga(c, "Memória", "CLARA", "ai_memory")
    for s in ("Sub-agente INFO", "Sub-agente CONVENIOS", "Sub-agente ATENDIMENTO"):
        liga(c, s, "CLARA", "ai_tool")
        liga(c, "Modelo dos sub-agentes", s, "ai_languageModel")
    liga(c, "Base de convenios", "Sub-agente CONVENIOS", "ai_tool")
    liga(c, "Embeddings", "Base de convenios", "ai_embedding")
    liga(c, "Registrar chamado", "Sub-agente ATENDIMENTO", "ai_tool")
    return workflow("aula10Clara00001", "Aula 10 - CLARA multiagente", nos, c)


def main():
    PASTA.mkdir(exist_ok=True)
    for arquivo, wf in (("ingestao-convenios.json", ingestao()), ("clara-multiagente.json", clara())):
        (PASTA / arquivo).write_text(json.dumps(wf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"workflows/{arquivo}: {len(wf['nodes'])} nós")


if __name__ == "__main__":
    main()
