# HaradaER — Resultados das investigações sobre o TerraER

2026-10-19 · Complementa `REQUISITOS.md` (seção 8, questões em aberto) e `ARQUITETURA.md`.

Método: classes do `TerraER3.14.jar` executadas em modo headless por programas Java (`referencia-terraer/harness/`), mais leitura do bytecode com `javap`. Onde algo foi **inferido** do bytecode e não executado, está dito.

Este documento relata fatos; as decisões tomadas a partir deles estão na seção 10.

## 1. QA-06 — Como o TerraER relê `attributeType`

Teste: `Read4` sobre arquivos com cada valor (`referencia-terraer/leitura-casos/`).

| Valor no arquivo | Resultado ao ler | Item do enum | Regravação |
|---|---|---|---|
| `CHAR(128)` | OK | `CHAR` | OK |
| `VARCHAR2(128)` | OK | `TEXT` | OK |
| `NUMBER` | OK | **`INTEGER`** | OK |
| `NUMBER(9,2)` | OK | **`NUMBER`** | OK |
| `DATE` | OK | `DATE` | OK |
| `INTEGER` | lê **sem erro**, tipo vira `null` | nenhum | **falha** (`NullPointerException`) |
| `FOO` | idem | nenhum | **falha** |
| `char(128)` (minúsculo) | idem | nenhum | **falha** |
| atributo ausente em `atr` | tipo `VARCHAR2(128)`, `nullable=false` | `TEXT` | OK |
| atributo ausente em `atrchave` | tipo `NUMBER`, `nullable=false` | `INTEGER` | OK |
| `nullable="maybe"` | lido como `false` | | OK |

Conclusões:
- O mapeamento do documento está certo: `NUMBER` ↔ INTEGER e `NUMBER(9,2)` ↔ NUMBER.
- A comparação do valor é exata e diferencia maiúsculas de minúsculas.
- Um `attributeType` inválido **abre normalmente no TerraER e só quebra ao salvar**. O HaradaER nunca deve gravar um valor fora dos cinco válidos.
- `nullable` só é verdadeiro quando o texto é `true`.

## 2. QA-07 — Como o TerraER reage a entradas fora do padrão

| Entrada | Resultado |
|---|---|
| Tag desconhecida como figura (`<foo/>`) | **Falha**: `Storable name not known to factory: foo` |
| Tag desconhecida como filho de um elemento | **Falha**, mesma mensagem |
| Atributo desconhecido num elemento (`<ent zzz="1">`) | Ignorado |
| Chave de estilo desconhecida em `<a>` | Ignorada |
| Raiz diferente de `drawing`, ou sem `figures` | Falha (`no such element:...`) |
| Arquivo vazio ou truncado | Falha (`no such element` / `Unexpected EOF`) |
| `id` ausente | Aceito |
| `id` que não é hexadecimal (`zz`) | Aceito (o id é só um texto) |
| `id` repetido | **Falha** (`no such element:children`) |
| `ref` para id inexistente | **Falha** (`NullPointerException`) |
| Declaração `<?xml ...?>` | Aceita |
| Arquivo indentado, com quebras de linha | Aceito |
| `DOCTYPE` com `SYSTEM "x.dtd"` | Aceito, sem buscar o DTD |
| UTF-8 direto (`ção 中`) | Aceito |

Conclusões:
- **Uma tag que o TerraER não conhece impede a abertura do arquivo inteiro.** Isso confirma o RNF-02 e mostra que arquivos válidos do TerraER nunca contêm tags desconhecidas.
- Atributos e chaves de estilo desconhecidos são ignorados, o que deixaria margem para metadados extras. Mas o TerraER os **descartaria** ao salvar de novo, então não são um lugar seguro para guardar dados do HaradaER.
- O TerraER é bem mais tolerante do que o formato que ele grava: declaração, indentação e DOCTYPE passam.

## 3. QA-02 — Rótulos de cardinalidade editados

- O texto `1` (`llabelUm`) e `N` (`llabelMuitos`) é um filho de texto **não editável** (`isEditable() == false`). Mudar o texto do filho por código não aparece no `.xml` (teste: `0..N` não foi gravado).
- **Corrigido na seção 15:** nas conexões "N", a ferramenta de conexão do TerraER troca a letra por N, M, P... pelo método `changeText`, e essa letra **é gravada** no estilo da conexão (`<a><text><string>M</string></text></a>`).
- O rótulo das conexões de generalização **é editável** e gravado em `labelGeneralizacaoText` (teste: `exclusiva` apareceu no arquivo). O padrão é "característica" em português e "characteristic" em inglês.

Conclusão: a cardinalidade do TerraER só tem os valores `1` e `N`, definidos pela **tag** da conexão. Não existe cardinalidade como `0..N` ou `1..1`.

## 4. QA-03 — Direção das ligações de atributo

Análise da matriz de validação (`matriz-validacao.txt`): para todas as conexões, exceto `generalizacaoLine`, o conjunto de pares válidos é **simétrico** (se `A→B` é válido, `B→A` também é). Em `lcaf` são 37 pares, todos simétricos.

Exceção: `generalizacaoLine` aceita `ent→ent` e `G*→ent`, mas não `ent→G*` (3 pares assimétricos).

Conclusões:
- Para `lcaf`, a direção não importa para a validação. As combinações "atributo→dono" que eu tinha estranhado são só o lado inverso das válidas, não artefato.
- Também não importa para a leitura: o TerraER não valida ao ler.
- O gerador de DDL do TerraER também aceita as **duas** direções: ele testa "início = entidade e fim = atributo" e também "fim = entidade e início = atributo" (confirmado no bytecode de `generateTables`).
- Em que direção a ferramenta de desenho do TerraER grava ao desenhar, só a interface mostraria; mas como o TerraER lê e processa as duas, isso não afeta a compatibilidade. As amostras que gerei por código usam atributo→dono.

## 5. QA-01 e QA-05 — Tamanho e estilo padrão

### 5.1 Estilo padrão dos elementos recém-criados

Medido por `Gen6` (valores são os padrões do `init()`). Em todos: contorno preto `#ff000000`, largura de traço `1.0`, fonte `Dialog`, tamanho `12.0`, cor do texto preta, preenchimento da forma branco `#ffffffff`, exceto onde indicado.

| Elemento | Forma | Diferenças do padrão | Texto padrão (inglês) |
|---|---|---|---|
| `ent` | retângulo | — | `ENT.0` |
| `entfraca` | retângulo | traço `DOUBLE` | `W. ENT. 0` |
| `rel` | losango | — | `rel. 0` |
| `relfraco` | losango | traço `DOUBLE` | `weak rel. 0` |
| `entrel` | retângulo + losango | — | `ENT. REL. 0` |
| `atr` | elipse | — | `att.0` |
| `atrchave` | elipse | texto negrito e sublinhado | `key att. 0` |
| `atrchaveparcial` | elipse | texto negrito; traço da elipse **do texto** tracejado `[3.0]` | `part. key att.0` |
| `atrderivado` | elipse | preenchimento `#ffffebeb`, traço tracejado `[5.0]` | `der. att.0` |
| `atrmulti` | elipse | preenchimento `#ffffebeb`, traço `DOUBLE` | `mult. att. 0` |
| `uniao` / `disjuncao` / `sobreposicao` | círculo | preenchimento `#fff5f2e0`; texto negrito, tamanho `16.0` | `u` / `d` / `o` |

Observação: o tracejado de `atrchaveparcial` é aplicado ao **texto**, não à elipse (por isso a descrição "contorno tracejado" no `REQUISITOS.md` está imprecisa).

### 5.2 Tamanho ao criar (inferido do bytecode, não executado)

A ferramenta de criação (`CreationTool`) posiciona o elemento a partir do ponto de clique, com os tamanhos abaixo. Quais ramos valem para qual tipo vem de comparações de classe (`RectangleFigure`, `DiamondFigure`, `TextFigure`) e **não foi confirmado na interface**.

| Categoria | Tamanhos encontrados |
|---|---|
| Entidade (grupo/retângulo) | 80 × 40; losango interno da entidade associativa 76 × 36; texto 80 × 20 |
| Atributo | 80 × 40; elipse 125 × 27; texto 80 × 20 |
| Relacionamento | 80 × 40; losango 97 × 50; texto 80 × 20 |
| Generalização (círculo) | 20 × 20 |
| Outros | 80 × 40; texto 80 × 20 |

### 5.3 Ajuste ao texto (executado, `Gen7`)

- Ao **mudar o texto**, a forma cresce até `largura do texto + 20` (10 de margem em cada lado) e **nunca encolhe**. Teste: forma 100×40 com "Aluno" ficou 100; com texto longo foi para 207,56; ao voltar para "A" ficou 207,56.
- O texto é **centralizado** na forma: `x = x_forma + (largura − largura_texto)/2` e `y = y_forma + (altura − altura_texto)/2` (conferido: 50 + (40 − 16,34)/2 = 61,83).
- O redimensionamento pelo mouse usa a mesma lógica (`TerraResizeEventFunctions`: centralizar o texto, margem de 20 e ajuste da forma). Chamar `setBounds` diretamente no grupo, como fiz nos testes, deu resultados incoerentes (um losango pedido com 100×50 ficou com 28×16), então **o comportamento ao arrastar as alças não foi medido**.
- Medidas de texto: fonte `Dialog` 12 pt do Java. Altura de uma linha de texto: 16,34. Largura de "Aluno": 32,86.

Conclusão: a geometria do arquivo sempre é a da forma, e o texto é recalculado a partir dela. Ao ler, usar o que está no arquivo. Ao criar ou editar texto, é preciso medir o texto; sem a fonte `Dialog` do Java, a largura vai diferir um pouco.

## 6. QA-04 — Geração de DDL

Executei o gerador real do TerraER (`GenerateDDLAction`) sobre 9 modelos (`harness/Ddl.java`; saída completa em `ddl-saida-terraer.txt`).

### 6.1 Como o gerador funciona

1. Classifica cada figura **pela classe exata** (`getClass().equals`). Consequência: **`uniao` (união) não é tratada**; só `disjuncao` e `sobreposicao`.
2. Chama, em ordem: criar tabelas → chaves primárias → chaves parciais → entidade associativa → generalização → relacionamentos → atributos multivalorados → atributos derivados.
3. Nomes de tabela: maiúsculas, espaços viram `_`.

### 6.2 Regras observadas

| Caso | O que o TerraER gera |
|---|---|
| Entidade com atributo chave | `CREATE TABLE`, coluna da chave com tipo e `NOT NULL`, `ALTER TABLE ... PRIMARY KEY` |
| Atributo comum | Coluna **sem tipo** (`nome NOT NULL`, `sigla ,`); só `NOT NULL` se `nullable=false` |
| Relacionamento 1:N | Coluna de chave estrangeira **na tabela do lado N**, nomeada `<chave>_<entidade 1>`, mais `FOREIGN KEY`. Anulável, salvo se a participação do lado N for **dupla** (então `NOT NULL`) |
| Relacionamento 1:1 | No teste, a chave estrangeira foi para a **segunda** entidade ligada. O critério exato (ordem de ligação ou outro) não foi determinado |
| Relacionamento N:N | Nova tabela `ENT1_ENT2`, colunas das duas chaves, chave primária composta. **Atributos do relacionamento (`nota`) não entram** |
| Entidade fraca + relacionamento fraco | Chave estrangeira da dona `NOT NULL`, chave primária composta (chave parcial + chave da dona) |
| Atributo multivalorado | Nova tabela `<ENT>_<ATRIBUTO>` com a chave da dona e o valor |
| Atributo derivado | `CREATE OR REPLACE VIEW VW_<ENT> AS ( <sql do atributo> )`, ou `( null )` se não houver SQL |
| Entidade associativa | Tabela própria com chaves das duas entidades |
| Generalização | Cria tabelas das entidades; **sem chave primária nem estrangeira** nas filhas |

### 6.3 Defeitos do próprio TerraER

Confirmados no bytecode (não são artefato do meu teste):
- Atributo comum não recebe tipo (`generateTables` só chama `getAttributeType` para atributo chave).
- `FOREING KEY` (erro de grafia) no N:N e na entidade associativa: SQL **inválido**.
- Entidade associativa sai sem `;` em duas linhas.
- Multivalorado gera a coluna `pk-telefone` (com hífen, inválida) e usa **só ela** como chave primária.
- Atributos de relacionamento N:N são perdidos.
- Generalização não gera chaves.
- Em N:N e associativa, o nome da restrição é `FK_...` e `FK2_...`.

Conclusão: o DDL do TerraER é uma **aproximação parcial**; reproduzi-lo byte a byte reproduziria SQL inválido.

## 7. QA-08 — Modo de Edição Rápida

Inferido do bytecode (`FastEditingModeAction`, `ButtonFactory$1`): é uma chave liga/desliga global. Normalmente, ao terminar de criar uma figura, o TerraER **volta para a ferramenta de seleção**. Com o modo rápido ligado, ele **não volta**: a ferramenta de criação continua ativa para criar vários elementos seguidos.

Não executado na interface; a descrição vem da lógica `setSelected(!ACTIVE)` no fim de cada ferramenta.

## 8. QA-09 — Instrução SQL

- A instrução SQL pertence **somente ao atributo derivado** (`AtributoDerivadoFigure.getSql/setSql`). A ação "Incluir respectiva instrução SQL" funciona só com um atributo derivado selecionado e abre uma caixa de texto "SQL:".
- **É gravada no `.xml`**, como atributo da tag: `<atrderivado id="0" sql="SELECT COUNT(*) FROM ALUNO">`, e relida corretamente.
- Vai para o DDL como o corpo da visão (`CREATE OR REPLACE VIEW VW_<ENT> AS ( <sql> )`).

Isso **faltava** no `REQUISITOS.md`: a tabela de elementos dizia que o atributo derivado não tinha atributos próprios.

## 9. QA-10 — Licença

- Informado pelo autor: o TerraER é distribuído sob **GPLv3** (com menções a donationware / software livre acadêmico).
- **Não verificável no `.jar`**: ele não contém texto de licença do TerraER. Contém apenas avisos de copyright de terceiros: JHotDraw ("original authors of JHotDraw", 1996-2007) e NanoXML (Werner Randelshofer, 2002).
- O código do TerraER é um derivado do JHotDraw e inclui o NanoXML. A fonte oficial do TerraER é quem define os termos.

Implicação, sem decidir nada: com GPLv3, se qualquer trecho de código ou recurso do TerraER fosse copiado ou traduzido, o HaradaER teria de ser GPLv3 também. O RNF-13 (reimplementação independente, sem copiar) evita isso. Compatibilidade de formato de arquivo, por si só, não copia código.

## 10. Decisões tomadas

Decididas pelo autor em 2026-10-19. Regra aplicada: o que pôde sair da v1 saiu; erro claro para tag desconhecida; nos demais, a recomendação.

| # | Decisão | Resultado |
|---|---|---|
| 1 | Tag desconhecida ao **ler** | **Erro claro** e o arquivo não abre (RNF-14) |
| 2 | RF-12 | Restrito às figuras de apoio **conhecidas** |
| 3 | `DOCTYPE` ao ler | Aceito e ignorado, sem DTD nem entidades; subconjunto interno recusado (RNF-15) |
| 4 | `attributeType` inválido | Aviso na leitura, tipo padrão, nunca gravar valor inválido (RNF-16) |
| 5 | DDL (RF-13) | **Fora da v1.** Levantamento preservado para retomar |
| 6 | RF-20 | **Fora da v1** a edição do SQL do derivado e o Modo Rápido. O atributo `sql` continua sendo lido e gravado |
| 7 | Tamanho e estilo ao criar | Adotar os valores das seções 5.1 e 5.2 |
| 8 | Medida de texto | `QFontMetricsF` com fonte equivalente à do TerraER; pequena diferença aceita |
| 9 | Cardinalidade | Só `1` e `N`, pela tag |
| 10 | Direção da ligação de atributo | **Sem impacto.** O HaradaER lê as duas direções e grava atributo→dono; o TerraER aceita ambas (validação simétrica e DDL com os dois casos) |

Decididas pelo autor em 2026-10-22, na revisão do que ficou fora da v1:

| # | Decisão | Resultado |
|---|---|---|
| 11 | Impressão (RF-14) | **Descartada.** O PDF de Exportar desenho cobre a necessidade |
| 12 | GIF (QA-14) | **Descartado.** O PNG cobre a necessidade |
| 13 | Copiar e colar com o TerraER (QA-13) | **Descartado.** Só o arquivo é compatível |
| 14 | Inglês (RNF-06) | **Volta para a v1.** Troca ao reabrir (com aviso), nomes padrão no idioma escolhido, manual em inglês |
| 15 | Paleta como painel (RNF-09) | **Depois da v1, como opção.** Exibir › Paleta: No alto (faixa de hoje) ou À esquerda (painel). Sem fechar e sem soltar |

## 11. Achados durante o M1 (leitura e gravação)

Programas: `harness/Gen10.java`, `Gen11.java`, `Gen12.java`. Amostras em `referencia-terraer/`.

| Assunto | O que o TerraER faz |
|---|---|
| Escape de texto | `& < > " '` viram entidades; `\n` fica literal; **todo** outro caractere abaixo de 0x20 ou a partir de 0x7f vira `&#x<hex>;`, inclusive os que XML puro proíbe (`&#x1;`, `&#x8;`, `&#xd800;`). Vale para texto e para atributos |
| Emoji (acima de U+FFFF) | Gravados como par de surrogates (`&#xd83d;&#xde00;`). Lendo `&#x1f600;` o TerraER corrompe o texto (vira `U+F600`); lendo o par, fica certo. O leitor do HaradaER junta o par antes do parse e o gravador reescreve como par |
| Caractere de controle no texto | Arquivo que um parser XML padrão recusa. O HaradaER devolve erro claro (RNF-14). O TerraER o abre, então é uma diferença de comportamento aceita |
| Texto vazio | `<string/>`. Atributo vazio fica `sql=""`; valor nulo não é gravado |
| Quebra de linha em atributo | Gravada literal; o parser XML padrão a normaliza para espaço (limitação conhecida) |
| Ordem de empilhamento | Conexão antes do nó: o nó é escrito inline dentro do `Owner` e depois aparece como `<ent ref="2"/>` no desenho. Remover um nó do desenho do JHotDraw apaga as conexões ligadas a ele |
| Números | `Double.toString` do Java sem o `.0` final. `-0.0` → `-0`; `1.0E7` e `1.0E10` mantêm o `.0`; o menor positivo é `4.9E-324` (o Java mostra ao menos dois dígitos) |
| Figuras de apoio | `t`, `tn`, `ti`, `ta`, `r`, `e`, `diamond`, `circ` seguem o mesmo molde das partes. `l` e `b` guardam `<points><p colinear="true" x y/>` (sem `c1x`...). `g` tem `<children>`. `image` tem `<imageData>` com Base64 quebrado em linhas de 76 caracteres |

## 12. Achados durante o M2 (validação e recomendação)

Programas: `harness/ValidaArquivo.java`, `Regras.java`, `Recomenda.java`. Fixtures: `validacao-por-arquivo.txt`, `regras-recomendacao-terraer.txt`, `amostra-conexoes-incompletas.xml`.

- **A "Verificação do Modelo" é um interruptor global.** `ValidateModelAction` liga e desliga `LineConnectionFigure.validateEnabled` e manda cada conexão se redesenhar; a cor vermelha vem de `ModelValidation.validateLineConnection`.
- **Conexão com ponta solta** (ainda não ligada a um elemento): o TerraER a grava com `<null/>` no lugar do conector (`<endConnector><null/></endConnector>`) e a pinta de vermelho, **exceto a conexão livre (`llabel`)**, que nunca fica vermelha, nem sem pontas.
- **Dois elementos iguais ligados** por um tipo que não aceita o par (por exemplo `llabelUm` de uma entidade a ela mesma) também ficam vermelhos.
- **Há duas tabelas de regras e elas discordam.** A de validação (`ModelValidation`, usada para pintar de vermelho) e a de recomendação (`ModelValidationRules`, 21 regras). Concordam em tudo, exceto:
  - `Um` e `Muitos`: a recomendação inclui `entidade fraca ↔ relacionamento fraco`, que a validação pinta de vermelho (só a participação dupla aceita esse par);
  - `generalizacaoLine`: a recomendação diz `entidade → círculo`; a validação só aceita `círculo → entidade` (e `entidade → entidade`).
  Ou seja, o TerraER chega a recomendar ligações que ele mesmo marca como inválidas.
- **Decisão técnica do M2:** a recomendação do HaradaER usa a tabela da validação, para nunca sugerir algo que apareceria em vermelho. A conexão livre não entra nas recomendações. Isso é uma divergência intencional, coberta por teste (`test_diferencas_conhecidas_entre_a_recomendacao_do_terraer_e_a_nossa`).
- **A recomendação do TerraER parte de uma conexão já desenhada** (`getOthersConnections(conexão)` e `getOthersFigures(conexão)`) e inclui o próprio tipo da conexão na lista. A do HaradaER parte de dois tipos de elemento, que é o que o RF-10 pede.

## 13. Achados durante o M3 (como o TerraER desenha)

Programas: `harness/Exporta.java`, `Estilos.java`, `Rotulos.java`, `Ta.java`, `TracoDuplo.java`, `Gen13.java`. Imagens que o próprio TerraER exportou, para comparar a olho: `referencia-terraer/imagens/`.

| Assunto | O que o TerraER faz |
|---|---|
| Preenchimento das formas | **Fixo no código**, ignora o atributo `fillColor` do arquivo: retângulo `(175,255,175)` (verde), losango `(255,255,100)` (amarelo), elipse `(175,175,255)` (lilás). Só o círculo (`circ`) usa o `fillColor` (branco por padrão). Por isso os atributos derivado e multivalorado, que gravam rosa, aparecem lilás |
| Traço duplo (`DoubleStroke`) | Duas faixas de largura `w` com um vão de `w × (fator − 1)`. Com `w=1` e fator 3: faixas de 1 px, vão de 2 px, largura total 4 |
| Quais figuras têm traço duplo | As partes de entidade fraca, relacionamento fraco e atributo multivalorado (gravam `strokeType=DOUBLE`) e as conexões `llabelDoubleUm`, `llabelDoubleMuitos` e `llabelDoubleGeneralizacao` (o tipo vem da classe, o arquivo só grava o fator) |
| Rótulos `1` e `N` | Texto em negrito, tamanho 16. Posição: ponto da linha a 0% do comprimento; âncora a 8 unidades dele, a −45° da direção da linha; o rótulo fica no quadrante oposto ao da âncora (canto inferior esquerdo, se a âncora aponta para cima e à direita). Conferido contra o TerraER com precisão de centésimos |
| Rótulo da generalização | Itálico, tamanho 12, mesma regra, a 25% do comprimento |
| Arco da generalização simples | `generalizacaoLine` desenha um arco de 210° e raio 10 no **centro** da linha, a partir de `int(ângulo) − 15` graus, onde o ângulo depende do quadrante da inclinação da linha |
| Chave parcial | O traço tracejado `[3.0]` do texto é um sublinhado tracejado (notação ER para chave parcial). `TextFigure` não desenha traço próprio; isso foi interpretado, não medido |
| Área de texto (`ta`) | Moldura com preenchimento branco e margem interna de 5; o texto de várias linhas começa no canto interno |
| Fonte padrão | `Dialog` 12 (fonte lógica do Java) |
| Imagem | `imageData` é Base64 com quebras de linha; é desenhada escalada para `w × h` |
| Exportação GIF | Perde linhas e usa outro caminho de desenho; **não serve de referência**. O JPG é o fiel |

Não implementado no M3 (anotado como limitação): pontos de controle de curvas Bézier (as amostras do TerraER não os usam), quebra automática de linha na área de texto, crescimento do preenchimento pelo traço e a fonte exata `Dialog` do Java (no Qt vira a fonte sem serifa do sistema, então as larguras de texto diferem um pouco).

## 14. Achados durante o M4 (editar e abrir no TerraER)

Programas: `harness/RegravaTerra.java` (o TerraER lê um arquivo e o grava de novo) e `harness/gera_no_haradaer.py` (cria o modelo pelos comandos de edição do HaradaER). Resultado em `referencia-terraer/criados-no-haradaer/`: o arquivo criado, o que o TerraER regravou e as duas imagens (a do TerraER e a do HaradaER).

| Assunto | O que o TerraER faz |
|---|---|
| Abrir o que o HaradaER cria | Abre sem erro os 13 elementos e as 9 conexões. O modelo regravado tem os mesmos elementos, nomes, tipos, anulabilidade, tamanhos e ligações (conferido por `tests/core/test_compat_terraer.py`) |
| Diferenças na regravação | Só a última casa de números (`112.4` vira `112.39999999999998`, ruído do próprio TerraER) e a ordem das entradas de estilo, que não importa |
| Pontas das conexões | O TerraER **recalcula** as pontas ao abrir. Os pontos que o HaradaER grava coincidem com os dele até a 12ª casa, exceto no círculo da generalização (abaixo) |
| Conector | Todas as conexões usam `rConnector` (retângulo), qualquer que seja a forma do elemento. A linha vai de centro a centro e termina onde cruza a borda. Conferido contra `amostra-basica.xml` (`64.15737413759453` e `54.809172757745785`, idênticos) |
| Caixa do conector | É a caixa do grupo inteiro (forma **e** texto). Só faz diferença no círculo da generalização, cujo texto (fonte 16, altura ≈ 21,8) passa dos 20 da forma: as pontas diferem em menos de 2 unidades. O HaradaER usa só a forma |
| Conexões duplas | O TerraER grava um bloco `<a>` com `innerStrokeWidthFactor=3` depois de `endConnector` (dois blocos na generalização dupla). O HaradaER grava igual |
| Atributo `lcaf` | Gravada do atributo para o dono, como na decisão de QA-03 |

Limitação conhecida: o tamanho do texto vem da fonte do Qt, não da `Dialog` do Java; a largura ao criar ou renomear um elemento pode diferir um pouco da que o TerraER calcularia. Como a geometria gravada no arquivo é sempre respeitada ao abrir, isso não muda o modelo.

## 15. Conexões repetidas entre o mesmo par e a letra N, M, P (achado no teste geral da v1)

Problema relatado: duas conexões "N" entre a mesma entidade e o mesmo relacionamento ficavam uma sobre a outra no HaradaER, as duas com "N"; no TerraER aparecem "N" e "M", com a segunda linha desviada.

Programa: `harness/Paralelas.java` roda os passos da ferramenta de conexão do TerraER (`ConnectionTool.mouseReleased`) três vezes entre o mesmo par. Gabaritos: `amostra-paralelas.xml` e `amostra-paralelas-dupla.xml`.

| Passo do TerraER | O que faz |
|---|---|
| `unaryRelationshipHandle` | Se já existe conexão entre os mesmos dois elementos (em qualquer sentido), a nova ganha duas dobras: pontos a 1/3 e 2/3 da linha, levados para a perpendicular, a 70 de distância **das pontas**. Como os pontos saem das pontas e não do meio, a linha forma um X cruzado; e a 3ª conexão fica exatamente sobre a 2ª |
| `numberInCorrectSideHandle` | Se a conexão vai de entidade (`ent`, `entfraca`, `entrel`) para relacionamento (`rel`, `relfraco`, `entrel`), inverte o sentido. Por isso o rótulo 1/N fica do lado do relacionamento. Vale para qualquer tipo de conexão |
| `updateNumbering` | Só nas conexões "N" (`llabelMuitos`, `llabelDoubleMuitos`). Pega as conexões "N" na área do elemento de início (o relacionamento) e dá a elas, em ordem, N, M, P, Q, R, S; da 7ª em diante, N. A letra é gravada no estilo da conexão; na conexão dupla, no mesmo bloco do `innerStrokeWidthFactor` |
| Dobras no arquivo | `<p colinear="true" x=".." y=".."/>`, sem `c1x`/`c2x` (as pontas continuam com eles) |
| Ao mover | As dobras ficam onde estão; cada ponta mira a dobra mais próxima dela (`ChopRectangleConnector`). No HaradaER, uma conexão selecionada junto com o elemento leva as dobras junto (decisão do autor, 2026-10-22) |
| Ao excluir | Não renumera; só a próxima conexão criada renumera todas |

O que o HaradaER faz (decisão do autor: "desvio limpo"):

- Lê e mostra a letra gravada (antes mostrava sempre "N").
- Inverte entidade → relacionamento, numera N, M, P... e grava a letra igual ao TerraER (conferido: o TerraER relê as letras e regrava os mesmos pontos, `criados-no-haradaer/paralelas.xml`).
- **Desvio diferente do TerraER, de propósito:** dobras a 1/3 e 2/3 do caminho de centro a centro, deslocadas 70 na perpendicular, alternando de lado e se afastando (70, −70, 140, −140...). A linha fica em forma de colchete, sem cruzar, e as conexões extras nunca se sobrepõem. O arquivo continua compatível: o TerraER só guarda os pontos.
- Ao mover, as dobras ficam; se as duas pontas andam juntas, a linha inteira acompanha. No HaradaER, também acompanha quando a própria conexão está na seleção arrastada (decisão do autor, 2026-10-22).

## 16. Editar a linha das conexões (vértices e pontas)

Como o TerraER faz (bytecode do JHotDraw): duplo clique na linha cria um vértice (`LineConnectionFigure.handleMouseClick` → `splitSegment`); arrastar a alça de um vértice o move (`BezierNodeHandle`); duplo clique na alça o remove, se a linha tiver mais de dois pontos (`trackDoubleClick` → `removeNode`); arrastar a alça de uma ponta até outro elemento reconecta a conexão.

O que o HaradaER faz, com uma conexão selecionada:

| Ação | Gesto |
|---|---|
| Adicionar vértice | Arrastar o ponto do meio de um trecho, ou duplo clique na linha (como no TerraER), ou botão direito › Adicionar vértice aqui |
| Mover vértice | Arrastar o quadrado branco (com a grade ligada, encaixa) |
| Remover vértice | Duplo clique no quadrado (como no TerraER), ou botão direito › Remover vértice |
| Endireitar | Botão direito › Endireitar linha (tira todos os vértices) |
| Reconectar ponta | Arrastar o quadrado azul de uma ponta até outro elemento; a prévia fica verde ou vermelha conforme o par seja aceito |

As pontas sempre se religam mirando o vértice mais próximo. Reconectar mantém o tipo, o sentido, a letra e os vértices, como a alça de ponta do TerraER. Cada gesto é um passo de desfazer. O rótulo de texto da conexão também passou a ser clicável, para o duplo clique no rótulo da generalização continuar editando o texto.

Conferido: `criados-no-haradaer/vertices.xml` (feito pelos comandos, `gera_no_haradaer.py --vertices`) é relido e regravado pelo TerraER com os mesmos pontos e as mesmas ligações (`vertices-regravado-pelo-terraer.xml`), e as duas imagens ficam iguais.

## 17. Achados da revisão da v1

- **Critério 4.** Um modelo com uma conexão para cada uma das 343 combinações aceitas (`criados-no-haradaer/todas-validas.xml`, gerado pelos comandos do HaradaER) é lido e regravado pelo TerraER com o mesmo modelo, e a validação do próprio TerraER (`ValidaArquivo.java`) não marca nenhuma conexão. A inversão entidade → relacionamento (seção 15) não torna nenhuma conexão inválida.
- **`lcf` vira `lcaf`.** O TerraER lê `lcf` como apelido de `lcaf` e, ao gravar, sempre escreve `lcaf`. O HaradaER preserva a tag lida, e a barra de ferramentas só cria `lcaf`.
- **Círculo da generalização.** A diferença de menos de 2 unidades nas pontas (seção 14) vale para qualquer conexão que toque um círculo, não só para as de generalização.
- **Tipo de atributo inválido (RNF-16).** Não estava implementado: um `attributeType` inválido era regravado como estava. Agora o HaradaER avisa ao abrir e troca pelo tipo padrão (troca que pode ser desfeita).
- **Permissões ao salvar.** O arquivo salvo ficava só com permissão do dono, porque o temporário da gravação segura nasce assim. Agora mantém as permissões do arquivo substituído.
- **Agrupar (RF-03).** O TerraER usa o `GroupAction` do JHotDraw: tira as figuras do desenho, cria um `g` com elas na ordem de empilhamento e o põe no topo; desagrupar devolve as figuras ao topo. Com elementos que têm conexões (`harness/Grupo.java`, gabarito `amostra-grupo.xml`), as conexões ficam fora do grupo e continuam ligadas aos elementos de dentro: como a conexão vem antes do grupo, o elemento é gravado dentro do `Owner` da conexão e o grupo só faz `ref` a ele. O TerraER relê, valida e, ao mover o grupo, as pontas acompanham. `criados-no-haradaer/grupos.xml` (grupo, grupo dentro de grupo, colar e duplicar, feitos no HaradaER) passa pelo TerraER sem mudança e sem conexão vermelha.
- **Copiar e colar.** O conteúdo copiado é um pedaço de arquivo no formato do TerraER, num tipo próprio da área de transferência (`application/x-haradaer-figuras`); por isso colar entre janelas funciona, mas não com o TerraER (QA-13).

## 18. A conexão livre no TerraER 3.14 (análise do `.jar`, 2026-10-30)

Para decidir o RF-25, as 464 classes do `TerraER3.14.jar` foram desmontadas com `javap`. Não houve teste clicando no programa: no Linux/Wayland desta máquina a janela do TerraER abriu em branco (com `_JAVA_AWT_WM_NONREPARENTING=1` o resultado não foi confirmado) e travou ao fechar.

- **Nenhuma ferramenta cria a conexão livre.** A barra (`DrawApplicationModel.addCreationButtonsTo`) tem uma ferramenta para cada conexão tipada (`createElbowConnectionAtributo`, `createElbowUmConnection`, `createElbowMuitosConnection`, as duas duplas e as três de generalização), e nenhuma para `LabeledLineConnectionFigure`, a classe da `llabel`.
- **Ninguém instancia essa classe.** Ela só aparece como superclasse das conexões 1, N e de generalização (`invokespecial ... "<init>"` nos construtores delas), num `checkcast` do `ConnectionTool` (renumerar N, M, P) e na tabela de leitura e gravação (`DrawFigureFactory`: `LabeledLineConnectionFigure` ↔ `llabel`). O construtor do `ConnectionTool` que recebe o nome de uma classe não é usado, e o nome da classe não aparece em nenhum texto ou `.properties`.
- **Cada conexão tipada tem a sua tag** na tabela do `DrawFigureFactory`, então nenhuma conexão criada pela interface é gravada como `llabel`.
- **Como ela aparece num arquivo:** abrindo um `.xml` que já a tem, ou copiando, colando ou duplicando uma que veio de um arquivo. As das amostras de referência foram geradas pelos programas de `harness/`. O HaradaER, da 1.0 à 1.2.0, cria a conexão livre pela paleta e pela tecla `C`; esses modelos são a fonte mais provável.
- **A conexão livre não carrega informação:** no arquivo, ela tem só os pontos e as duas pontas, sem rótulo nem atributos, e nada aponta para ela. Apagá-la não quebra referência.
- **Textos pela interface.** A barra do TerraER tem as ferramentas Papel (`ti`, texto em itálico, para nomes de papel), Texto (`t`) e Área de Texto (`ta`). As outras figuras de apoio (retângulo, elipse, losango, círculo, linha, bézier, imagem) não têm ferramenta na barra.

