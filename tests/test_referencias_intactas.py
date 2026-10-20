"""Os gabaritos de `docs/referencia-terraer/` não podem mudar sem querer.

Eles foram gravados pelo próprio TerraER (ou são a evidência do RNF-01). Num teste manual, é fácil
salvar por cima de um deles; este teste avisa. Se a mudança for intencional, atualize o hash
(os 32 primeiros dígitos do SHA-256).
"""

import hashlib

import pytest

ESPERADO = {
    "amostra-basica.xml": "e3ad012b0691bd3ebd58fe5c0899262f",
    "amostra-caracteres-invalidos.xml": "b832df0e4c7ff99814a11e3e88530125",
    "amostra-conexoes-incompletas.xml": "6a31217523082c3578005a15b2ca3c78",
    "amostra-escapes-e-numeros.xml": "999906027afc80893843cbb3143417ea",
    "amostra-estilos.xml": "ab0d27a97b150fea5beb7587e83778e0",
    "amostra-figuras-de-apoio.xml": "bd50ef08cf6b0592259a57b7ee33fbf9",
    "amostra-grupo.xml": "c0a5fed40599e785a0fc8c431ccd7675",
    "amostra-numeros.xml": "200a42a5633238eccc00cb3ae1379dc5",
    "amostra-ordem-empilhamento.xml": "130ea6e0c4efe6d6f68e6e5a91a6d118",
    "amostra-paralelas-dupla.xml": "6833bdf74660742bc56715a2b0851cd6",
    "amostra-paralelas.xml": "be82bb6336d85af380576788291dc11f",
    "amostra-todos-os-tipos.xml": "7eba5e24c7ad772817b9c0be3cc7bfd0",
    "amostra-unicode.xml": "58361c2daed3e15127df4451698abbdd",
    "amostra-vazios.xml": "120b6faf7829d7834b33b4f45285ce03",
    "criados-no-haradaer/grupos-regravado-pelo-terraer.xml": "74449e05b5efe04b94d00459c6fe3ee2",
    "criados-no-haradaer/grupos.xml": "fe13288314e01b4703cfae558a651b5a",
    "criados-no-haradaer/paralelas-regravado-pelo-terraer.xml": "7312c19a70cecd8048a367ada10f574b",
    "criados-no-haradaer/paralelas.xml": "433b74a9e3bf7def6ce726aa3e019794",
    "criados-no-haradaer/regravado-pelo-terraer.xml": "3b9b14e9f6c2678b0f17a05083dda8fa",
    "criados-no-haradaer/todas-validas-pelo-terraer.xml": "3e6294e56045b97edf9354e4eb65d81d",
    "criados-no-haradaer/todas-validas.xml": "611e350cd9b437de79a5fd3661f6a025",
    "criados-no-haradaer/todos-os-tipos.xml": "47881341193f577bd3d3a9110d7d48e4",
    "criados-no-haradaer/vertices-regravado-pelo-terraer.xml": "4c9631cf4ae5c793ced54cae5b7cfddc",
    "criados-no-haradaer/vertices.xml": "8de4ac1916e0f59792fadc6995a0f472",
    "leitura-casos/tipo_FOO_.xml": "3a3d35a4905f3a73c59663af70279e17",
    "leitura-casos/tipo_NUMBER_.xml": "5c88eed5cde0a7d12a80866225b87b1d",
    "leitura-casos/tipo_semattr.xml": "34e3e377c61c3d793c41ab2f7f3020c7",
    "leitura-casos/u_attr_ent.xml": "2a5b53c34a29470b764da3c00a7c9c83",
    "leitura-casos/u_doctype.xml": "c9c9642dc54cf1076b07d5d8f36d523a",
    "leitura-casos/u_idnaohex.xml": "2cd54fc1f6967b07718e3c2083f60218",
    "leitura-casos/u_idrepetido.xml": "6ae243204a4eb5835ca302f786e73bdb",
    "leitura-casos/u_tag_fig.xml": "2730a0cc9e12885177e6c79c6ca6002b",
    "leitura-casos/u_xmldecl.xml": "2d333a1489af268e882424ee476a84a8",
}


@pytest.mark.parametrize("nome", sorted(ESPERADO))
def test_gabarito_nao_mudou(referencia, nome):
    conteudo = (referencia / nome).read_bytes()
    assert hashlib.sha256(conteudo).hexdigest()[:32] == ESPERADO[nome], (
        f"{nome} mudou. Se foi sem querer: git checkout -- docs/referencia-terraer/{nome}"
    )


def test_todas_as_amostras_estao_na_lista(referencia):
    amostras = {p.name for p in referencia.glob("amostra-*.xml")}
    assert amostras <= set(ESPERADO)
