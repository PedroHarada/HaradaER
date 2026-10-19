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

- O texto `1` (`llabelUm`) e `N` (`llabelMuitos`) é um filho de texto **não editável** (`isEditable() == false`) e **não é gravado** no arquivo. Tentar mudá-lo por código também não aparece no `.xml` (teste: `0..N` não foi gravado).
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
