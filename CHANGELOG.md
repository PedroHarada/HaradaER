# Histórico de versões

O que mudou em cada versão do HaradaER. A numeração segue a seção 13 do
[ARQUITETURA](docs/ARQUITETURA.md): `z` para correções, `y` para funcionalidades novas e `x`
para mudanças que quebram algo que já funcionava.

## 1.2.2 — 2026-10-30

A 1.2.1 não foi publicada: os testes do lançamento falharam com o pytest 9.2, e a correção
saiu nesta versão.

### Removido

- A conexão livre: ela não tem significado no modelo ER, e o TerraER 3.14 não tem ferramenta
  para criá-la. Saiu da barra de ferramentas, do painel de propriedades e da tecla `C` da Edição
  rápida.

### Alterado

- Ao abrir um arquivo com conexões livres (do TerraER ou de versões anteriores do HaradaER), elas
  são apagadas, também dentro de grupos, e um aviso diz quantas eram e entre quais elementos. O
  arquivo em disco só muda quando você salvar, e o TerraER continua abrindo o arquivo salvo.
  Colar também descarta as conexões livres.

## 1.2.0 — 2026-10-25

Versão em avaliação: a Edição rápida e a troca de tipo podem mudar nas versões 1.2.x, conforme o
uso mostrar o que manter, ajustar ou tirar.

### Adicionado

- Editar › Edição rápida (Ctrl+Shift+E, ou o botão na barra de status): atalhos de uma tecla para
  as ferramentas, uma letra por família (E entidade, R relacionamento, A atributo, G
  generalização, 1 e N participação, L ligação de atributo, H herança, C conexão, V selecionar).
  Repetir a letra passa ao próximo tipo da família, e Shift + a letra volta. O programa lembra se
  o modo estava ligado.
- Com a Edição rápida ligada:
  - a ferramenta continua ativa depois de criar (Shift + clique inverte);
  - Espaço cria o elemento da ferramenta onde está o mouse;
  - com dois elementos selecionados, a tecla de uma conexão liga os dois na hora, ou a barra de
    status diz por que o par não aceita;
  - A com uma entidade ou um relacionamento selecionado cria um atributo já ligado a ele;
  - com Selecionar ativo, a letra da família do elemento selecionado troca o tipo dele (A num
    atributo o faz virar chave).
- Clique direito num elemento › Trocar tipo: troca o tipo dentro da família (atributo, entidade,
  relacionamento, generalização), com qualquer ferramenta ativa. Ficam o lugar, o nome e as
  conexões; quando o tipo novo perde o tipo SQL ou a instrução SQL, o programa pergunta antes.
- Ajuda › Atalhos do teclado (F1): todos os atalhos, com busca. A mesma lista está nos manuais.

## 1.1.2 — 2026-10-22

### Corrigido

- O aviso de versão nova não funcionava no executável do Linux fora do Ubuntu (Arch, Fedora) e,
  provavelmente, no macOS: a conexão segura com o GitHub não achava os certificados do sistema.
- Quando a verificação pedida em Ajuda falha, a mensagem mostra também o motivo técnico.
- Publicar uma pré-versão não tira mais a versão final da página Releases (a `v1.1.2-rc2`
  tirou a 1.1.1, e o aviso de versão nova ficou sem resposta até a 1.1.2).

## 1.1.1 — 2026-10-22

### Corrigido

- O HaradaER passa a ser distribuído sob a GPLv3 (arquivo `LICENSE`).
- Os pacotes deixam de levar o teclado virtual do Qt (só GPLv3), o Qt Quick, o Qml e o QtPdf, que
  o programa não usa; ficam menores.
- `AVISOS-DE-LICENCA.txt` com todas as bibliotecas incluídas e os textos completos das licenças.
- Ao arrastar um elemento junto com conexões selecionadas, as dobras dessas conexões acompanham
  o movimento (antes ficavam paradas e a linha entortava).

## 1.1.0 — 2026-10-22

### Adicionado

- Menu Ajuda › Relatar um problema e Ajuda › Sugerir uma melhoria: abrem no navegador a página
  de nova issue do GitHub, já com a versão, o sistema e o idioma preenchidos. Nada é enviado
  sem que a pessoa confirme.
- Aviso de versão nova: ao abrir, no máximo uma vez por dia, o HaradaER confere no GitHub se há
  versão mais recente e oferece abrir a página de download. Também em Ajuda › Verificar
  atualizações; desliga em Ajuda › Verificar ao abrir.

## 1.0.1 — 2026-10-22

### Corrigido

- O app do macOS mostrava a versão 0.0.0 em "Obter informações"; agora mostra a versão certa.
- O zip do macOS extrai os arquivos direto, sem a pasta `pacote/`, como os do Linux e do Windows.

## 1.0.0 — 2026-10-22

Primeira versão.

### Adicionado

- Modelagem Entidade-Relacionamento com o arquivo `.xml` do TerraER 3.14: abre e salva
  modelos que o TerraER também abre.
- Entidades, relacionamentos, atributos, entidades associativas, generalizações e as conexões
  entre eles, com desfazer e refazer, copiar e colar, alinhamento e organização.
- Avisos de estrutura no desenho e no painel Mensagens (Exibir › Avisos de estrutura).
- Exportação do desenho em PNG e PDF.
- Interface em português e em inglês (Exibir › Idioma), começando pelo idioma do sistema.
- Tema claro, escuro ou do sistema.
- Pacotes para Linux, Windows e macOS, sem precisar de Python, com o manual de cada sistema em
  português (`PRIMEIROS-PASSOS.txt`) e em inglês (`GETTING-STARTED.txt`).
