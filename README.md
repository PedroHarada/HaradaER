# HaradaER

Ferramenta de modelagem Entidade-Relacionamento em Python, compatível com o arquivo `.xml` do
TerraER 3.14: um modelo salvo no HaradaER abre no TerraER com o mesmo
diagrama, e o inverso também vale.

Estado: em construção. Abre, mostra, edita e salva arquivos `.xml` do TerraER (criar, mover, redimensionar, conectar, renomear, excluir, alinhar, desfazer/refazer), com zoom e gestos de trackpad. Marca em vermelho as conexões com problema e recomenda as conexões aceitas entre dois elementos selecionados. Tem grade com encaixe e ordem de empilhamento. Ainda faltam painéis e exportação de imagem.

## Documentação

- [Requisitos](docs/REQUISITOS.md)
- [Arquitetura e design](docs/ARQUITETURA.md)
- [Investigações sobre o TerraER](docs/INVESTIGACOES.md)

## Desenvolvimento

Alvo da v1: Linux (Wayland), Python 3.14 e PySide6 6.12.

```
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
.venv/bin/ruff check .
```

Para abrir um modelo (ou, sem argumento, começar um novo):

```
.venv/bin/python -m haradaer docs/referencia-terraer/amostra-basica.xml
```

O `TerraER3.14.jar` é só material de consulta e não faz parte do repositório (está no `.gitignore`).
