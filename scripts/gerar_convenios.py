"""Gera os tres PDFs ficticios de convenio usados na Aula 10.

Escreve o PDF a mao (sem bibliotecas externas), com a fonte Helvetica
e a codificacao WinAnsi, para que o texto seja selecionavel e o no
Extract From PDF do n8n consiga extrai-lo.

Uso: python scripts/gerar_convenios.py
"""
from pathlib import Path

CONVENIOS = {
    "convenio_01.pdf": [
        "CONVÊNIO Nº 021/2026",
        "",
        "PARTES: Núcleo de Convênios, órgão hipotético, e o Instituto Federal de",
        "Educação Tecnológica de Vale Verde (fictício).",
        "",
        "REPRESENTANTES: pelo Núcleo, Ricardo Almeida Prado, coordenador; pelo",
        "Instituto, Juliana Costa Ribeiro, diretora-geral.",
        "",
        "OBJETO: Capacitação em Gestão de Projetos Públicos para servidores",
        "municipais, com oferta de 120 vagas em turmas semestrais.",
        "",
        "VALOR GLOBAL: R$ 180.000,00 (cento e oitenta mil reais).",
        "",
        "VIGÊNCIA: 12 (doze) meses, a contar da assinatura.",
        "",
        "LOCAL E DATA: Vale Verde/MT, 10 de março de 2026.",
    ],
    "convenio_02.pdf": [
        "CONVÊNIO Nº 034/2026",
        "",
        "PARTES: Núcleo de Convênios, órgão hipotético, e a Prefeitura Municipal",
        "de Serra Azul (fictícia).",
        "",
        "REPRESENTANTES: pelo Núcleo, Ricardo Almeida Prado, coordenador; pela",
        "Prefeitura, Marcos Vinícius Teixeira, prefeito.",
        "",
        "OBJETO: Modernização da Infraestrutura de Conectividade das Escolas",
        "Municipais, com instalação de rede sem fio em 18 unidades.",
        "",
        "VALOR GLOBAL: R$ 420.000,00 (quatrocentos e vinte mil reais).",
        "",
        "VIGÊNCIA: 18 (dezoito) meses, a contar da assinatura.",
        "",
        "LOCAL E DATA: Vale Verde/MT, 22 de abril de 2026.",
    ],
    "convenio_03.pdf": [
        "CONVÊNIO Nº 047/2026",
        "",
        "PARTES: Núcleo de Convênios, órgão hipotético, e a Fundação de Apoio à",
        "Pesquisa de Vale Verde (fictícia).",
        "",
        "REPRESENTANTES: pelo Núcleo, Ricardo Almeida Prado, coordenador; pela",
        "Fundação, Fernanda Lopes Azevedo, diretora-presidente.",
        "",
        "OBJETO: Pesquisa Aplicada em Tecnologias Sustentáveis, com bolsas para",
        "pesquisadores e aquisição de equipamentos de laboratório.",
        "",
        "VALOR GLOBAL: R$ 250.000,00 (duzentos e cinquenta mil reais).",
        "",
        "VIGÊNCIA: 24 (vinte e quatro) meses, a contar da assinatura.",
        "",
        "LOCAL E DATA: Vale Verde/MT, 5 de junho de 2026.",
    ],
}

RODAPE = "Documento fictício, criado para fins didáticos (Aula 10)."


def escapar(texto: str) -> bytes:
    dados = texto.encode("cp1252")
    return dados.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def montar_pdf(linhas: list[str]) -> bytes:
    conteudo = [b"BT", b"/F1 16 Tf", b"72 760 Td", b"(" + escapar(linhas[0]) + b") Tj", b"/F1 11 Tf", b"16 TL"]
    for linha in linhas[1:]:
        conteudo.append(b"T*")
        if linha:
            conteudo.append(b"(" + escapar(linha) + b") Tj")
    conteudo += [b"ET", b"BT", b"/F1 8 Tf", b"72 60 Td", b"(" + escapar(RODAPE) + b") Tj", b"ET"]
    stream = b"\n".join(conteudo)

    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    saida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    posicoes = []
    for i, obj in enumerate(objetos, start=1):
        posicoes.append(len(saida))
        saida += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(saida)
    saida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for p in posicoes:
        saida += f"{p:010d} 00000 n \n".encode()
    saida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(saida)


def main() -> None:
    pasta = Path(__file__).resolve().parent.parent / "convenios"
    pasta.mkdir(exist_ok=True)
    for nome, linhas in CONVENIOS.items():
        (pasta / nome).write_bytes(montar_pdf(linhas))
        texto = "\n".join(linhas)
        print(f"{nome}: {len(texto)} caracteres")


if __name__ == "__main__":
    main()
