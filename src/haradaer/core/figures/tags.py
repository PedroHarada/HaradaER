"""Tabela de tags do TerraER (a mesma da `DrawFigureFactory`), em dados."""

# Elementos do modelo ER (seção 3.1 de REQUISITOS.md).
NODE_TAGS = frozenset(
    {
        "ent",
        "entfraca",
        "rel",
        "relfraco",
        "entrel",
        "atr",
        "atrchave",
        "atrchaveparcial",
        "atrderivado",
        "atrmulti",
        "uniao",
        "disjuncao",
        "sobreposicao",
    }
)

# Conexões (seção 3.2). `lcf` é um apelido de `lcaf` que o TerraER também registra.
CONNECTION_TAGS = frozenset(
    {
        "llabel",
        "llabelUm",
        "llabelMuitos",
        "llabelDoubleUm",
        "llabelDoubleMuitos",
        "lcaf",
        "lcf",
        "generalizacaoLine",
        "llabelGeneralizacao",
        "llabelDoubleGeneralizacao",
    }
)

# Figuras de apoio: texto, formas, linhas, imagem e grupo.
SUPPORT_TAGS = frozenset(
    {"t", "tn", "ti", "ta", "r", "e", "diamond", "circ", "l", "b", "bezier", "image", "g"}
)

CONNECTOR_TAGS = frozenset(
    {"rConnector", "ellipseConnector", "diamondConnector", "bezierConnector"}
)

# Atributos que têm tipo SQL e anulabilidade.
TYPED_ATTRIBUTE_TAGS = frozenset({"atr", "atrchave", "atrchaveparcial", "atrmulti"})

# Partes de texto que guardam o nome de um elemento.
TEXT_PART_TAGS = ("t", "tn", "ti")

# Valor nulo: o TerraER grava `<null/>` onde falta um objeto (por exemplo, a ponta solta de uma
# conexão ainda não ligada).
NULL_TAG = "null"

FIGURE_TAGS = NODE_TAGS | CONNECTION_TAGS | SUPPORT_TAGS
KNOWN_OBJECT_TAGS = FIGURE_TAGS | CONNECTOR_TAGS | {NULL_TAG}

# Elementos estruturais cujos filhos são objetos conhecidos do TerraER.
CONTAINERS_OF_OBJECTS = frozenset(
    {"figures", "children", "Owner", "startConnector", "endConnector"}
)
