# Histórico de versões

O que mudou em cada versão do HaradaER. A numeração segue a seção 13 do
[ARQUITETURA](docs/ARQUITETURA.md): `z` para correções, `y` para funcionalidades novas e `x`
para mudanças que quebram algo que já funcionava.

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
