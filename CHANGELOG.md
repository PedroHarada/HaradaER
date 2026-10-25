# Histórico de versões

O que mudou em cada versão do HaradaER. A numeração segue a seção 13 do
[ARQUITETURA](docs/ARQUITETURA.md): `z` para correções, `y` para funcionalidades novas e `x`
para mudanças que quebram algo que já funcionava.

## 1.2.0 — 2026-10-25

### Adicionado

- Painel **Esquema lógico**: o esquema relacional calculado do diagrama, pelo mapeamento de
  Elmasri e Navathe (entidades, entidades fracas, 1:1, 1:N, N:N, n-ário, multivalorados,
  especialização, categorias e entidade associativa), com as chaves estrangeiras e os atributos
  derivados. Atualiza a cada mudança e tem o botão Copiar.
- **Arquivo › Gravar esquema lógico ao salvar** (desligado por padrão): grava o mesmo texto em
  `<modelo>.esquema.md`, ao lado do `.xml`, em Markdown básico. Nada muda no `.xml`.
- `docs/CONCEITOS.md` e `docs/REVISAO-TEORICA.md`: a base teórica do HaradaER e os pontos ainda
  em aberto em relação ao livro.

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
