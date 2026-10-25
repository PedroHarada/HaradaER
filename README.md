# HaradaER

Ferramenta de modelagem Entidade-Relacionamento em Python, compatível com o arquivo `.xml` do
TerraER 3.14: um modelo salvo no HaradaER abre no TerraER com o mesmo diagrama, e o inverso
também vale.

## Instalar e abrir

Alvo da v1: Linux (Wayland), Python 3.14 e PySide6 6.12.

```
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m haradaer              # modelo novo
.venv/bin/python -m haradaer modelo.xml   # abrir um modelo do TerraER ou do HaradaER
```

Cada modelo abre na sua própria janela. Para experimentar, abra uma **cópia** de um dos modelos
de exemplo, que também servem aos testes:

```
cp docs/referencia-terraer/criados-no-haradaer/todos-os-tipos.xml /tmp/
.venv/bin/python -m haradaer /tmp/todos-os-tipos.xml
```

## Como usar

**Desenhar**

| O quê | Como |
|---|---|
| Criar um elemento | Escolha o tipo na faixa de cima e clique no desenho; digite o nome e Enter |
| Ligar dois elementos | Escolha o tipo de conexão (à direita na faixa) e arraste de um elemento ao outro (verde: o par é aceito; vermelho: não é, mas a conexão é criada e fica marcada) |
| Repetir a ferramenta | Segure Shift ao clicar ou soltar |
| Voltar a selecionar | Esc |
| Renomear | Duplo clique no elemento, ou o campo Nome em Propriedades |
| Mover e redimensionar | Arraste o elemento; arraste as alças do elemento selecionado |
| Excluir | Delete (leva junto as conexões ligadas) |
| Copiar, recortar, colar | Ctrl+C, Ctrl+X, Ctrl+V (também de uma janela para outra); as conexões vão junto quando os dois elementos ligados são copiados |
| Duplicar | Ctrl+D |
| Agrupar e desagrupar | Ctrl+G e Ctrl+Shift+G (as conexões continuam ligadas aos elementos de dentro) |
| Desfazer e refazer | Ctrl+Z e Ctrl+Shift+Z |

**Linhas das conexões** (com a conexão selecionada)

| O quê | Como |
|---|---|
| Criar vértice | Arraste o pontinho do meio de um trecho, ou duplo clique na linha |
| Mover vértice | Arraste o quadrado branco |
| Remover vértice | Duplo clique no quadrado branco |
| Endireitar a linha | Botão direito › Endireitar linha |
| Ligar a ponta a outro elemento | Arraste o quadrado azul da ponta |

Várias conexões entre os mesmos dois elementos saem para os lados, sem se sobrepor, e as
conexões "N" de um relacionamento são numeradas N, M, P..., como no TerraER.

**Painéis e menus**

- **Mensagens**: os erros de conexão (vermelho) e os avisos de estrutura (laranja) do modelo;
  clicar numa linha leva ao elemento. A barra de status também resume a verificação.
- **Inspetor de objetos**: a árvore do modelo, com os atributos dentro do dono. Ctrl+F procura
  um elemento pelo nome (sem diferenciar maiúsculas e acentos).
- **Propriedades**: nome, tipo SQL e "pode ser nulo" dos atributos, tipo de uma conexão e
  rótulo das generalizações.
- **Exibir**: zoom (também pinça e rolagem com dois dedos no trackpad, ou Ctrl + roda), grade
  com encaixe, verificação do modelo (conexões com problema em vermelho), avisos de estrutura
  (em laranja: entidade sem chave, relacionamento com um participante só...; dá para desligar),
  os painéis, o tema
  (claro, escuro ou o do sistema, lido do qt6ct e atualizado quando você troca de tema; a
  escolha é lembrada e a exportação sai sempre no claro) e o idioma (português ou inglês; na
  primeira vez vale o do sistema, e a troca vale ao reabrir o programa).
- **Organizar**: trazer para a frente, enviar para trás, agrupar, desagrupar e alinhar.
- **Editar**: selecionar tudo ou do mesmo tipo, localizar, copiar o desenho como imagem.
- **Arquivo**: novo, abrir, abrir recente, salvar, salvar como e exportar o desenho em PNG, JPG,
  SVG ou PDF.

Se a faixa não couber na janela, role-a com dois dedos, com a roda do mouse ou pelas setas das pontas. Cada botão tem o desenho do elemento ou da conexão e um nome curto; parando o mouse em cima aparece o nome completo. Com dois elementos selecionados, a barra mostra em negrito as conexões aceitas entre eles.

## Estado

A v1 está pronta, em português e em inglês. O que fica para depois dela, como a geração de DDL,
está em `docs/REQUISITOS.md` (seção 10).

## Documentação

- [Primeiros passos](docs/PRIMEIROS-PASSOS.md): baixar, abrir e instalar em cada sistema
  (em inglês: [Getting started](docs/GETTING-STARTED.md))
- [Requisitos](docs/REQUISITOS.md)
- [Arquitetura e design](docs/ARQUITETURA.md)
- [Investigações sobre o TerraER](docs/INVESTIGACOES.md)
- [Conceitos](docs/CONCEITOS.md): a base teórica (Elmasri e Navathe) e o esquema lógico
- [Revisão teórica](docs/REVISAO-TEORICA.md): onde o HaradaER ainda não segue o livro

## Baixar sem instalar

Cada versão publicada em **Releases** traz executáveis prontos para Linux (Ubuntu 22.04+, Arch,
Fedora...), Windows 10/11 e macOS 14+ com chip Apple, sem precisar de Python. No Linux, o `instalar.sh` do pacote põe o HaradaER no menu de
aplicativos, com ícone (`packaging/linux/`). As instruções de
como abrir (e o aviso de "programa não reconhecido" no Windows e no macOS) estão na página de
cada versão e, com mais detalhes, em [Primeiros passos](docs/PRIMEIROS-PASSOS.md).

## Lançar uma versão

```
git tag v1.2.0
git push origin v1.2.0
```

O GitHub Actions roda o lint e os testes no Linux, no Windows e no macOS, gera os executáveis
(`packaging/HaradaER.spec`), roda neles o autoteste (`HaradaER --autoteste SAIDA.txt`: janela,
módulos fora do pacote e conexão segura com o GitHub; no Linux, também no Fedora e no Arch) e
publica a versão em Releases. Para gerar e testar os pacotes sem publicar, use **Run workflow**
na aba Actions (ou `gh workflow run versao.yml`). Se algum teste falhar, nada é
publicado. O número segue a seção 13 do [ARQUITETURA](docs/ARQUITETURA.md), e o que muda em cada versão fica no [CHANGELOG](CHANGELOG.md). Etiquetas com hífen (`v1.1.0-beta`) saem como pré-lançamento, sem tirar a versão final de
Releases. Cada versão final substitui as anteriores em Releases (as etiquetas antigas continuam
no git). A cada envio ao
`main` e a cada pull request, só o lint e os testes rodam (no Linux).

## Desenvolvimento

```
.venv/bin/pytest
.venv/bin/ruff check .
```

O `TerraER3.14.jar`, os gabaritos gravados por ele e os programas que o usam para conferir a
compatibilidade não fazem parte deste repositório; ficam só na máquina do autor. Sem eles, os
testes que dependem dos gabaritos são pulados, e o resto da suíte roda normalmente.

## Licença

O HaradaER é software livre, distribuído sob a [GNU General Public License, versão 3](LICENSE)
(GPLv3): pode ser usado, estudado, modificado e redistribuído, desde que as versões
modificadas também saiam sob a GPLv3, com o código-fonte. As bibliotecas incluídas nos pacotes
e as suas licenças estão em [`packaging/AVISOS-DE-LICENCA.txt`](packaging/AVISOS-DE-LICENCA.txt).
