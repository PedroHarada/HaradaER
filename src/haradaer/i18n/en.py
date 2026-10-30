"""Traduções para o inglês: texto em português -> texto em inglês.

Os nomes dos elementos e conexões seguem os do TerraER em inglês (`Labels_en`), com os termos
usuais do modelo ER onde o do TerraER é estranho ("Multivalue Attribute" -> "Multivalued
attribute"). O `&` marca a letra de atalho do menu; `{nome}` é preenchido pelo programa.
"""

EN: dict[str, str] = {
    # --- elementos (nome padrão ao criar e nome na interface) --------------------------------
    "Entidade": "Entity",
    "Entidade fraca": "Weak entity",
    "Relacionamento": "Relationship",
    "Relacionamento fraco": "Weak relationship",
    "Entidade associativa": "Associative entity",
    "Atributo": "Attribute",
    "Atributo chave": "Key attribute",
    "Chave parcial": "Partial key",
    "Atributo chave parcial": "Partial key attribute",
    "Atributo derivado": "Derived attribute",
    "Atributo multivalorado": "Multivalued attribute",
    "União": "Union",
    "Disjunção": "Disjunction",
    "Sobreposição": "Overlap",
    "Grupo": "Group",
    "característica": "characteristic",
    # --- conexões ----------------------------------------------------------------------------
    'Participação, lado "1"': 'Participation, side "1"',
    'Participação, lado "N"': 'Participation, side "N"',
    'Participação total, lado "1"': 'Total participation, side "1"',
    'Participação total, lado "N"': 'Total participation, side "N"',
    "Ligação de atributo": "Attribute link",
    "Generalização simples": "Simple generalization",
    "Participação opcional em generalização": "Optional participation in generalization",
    "Participação obrigatória em generalização": "Mandatory participation in generalization",
    # --- nomes curtos da faixa de ferramentas -----------------------------------------------
    "Selecionar": "Select",
    "Ent. fraca": "Weak ent.",
    "Relacion.": "Relation.",
    "Rel. fraco": "Weak rel.",
    "Ent. assoc.": "Assoc. ent.",
    "Chave": "Key",
    "Ch. parcial": "Part. key",
    "Derivado": "Derived",
    "Multival.": "Multival.",
    "Sobrepos.": "Overlap",
    "Lado 1": "Side 1",
    "Lado N": "Side N",
    "Total 1": "Total 1",
    "Total N": "Total N",
    "Lig. atrib.": "Attr. link",
    "General.": "General.",
    "Gen. opc.": "Gen. opt.",
    "Gen. obrig.": "Gen. mand.",
    # --- menus -------------------------------------------------------------------------------
    "&Arquivo": "&File",
    "&Novo": "&New",
    "&Abrir...": "&Open...",
    "Abrir &recente": "Open &recent",
    "&Salvar": "&Save",
    "Salvar &como...": "Save &as...",
    "&Exportar desenho...": "&Export drawing...",
    "&Fechar": "&Close",
    "&Sair": "&Quit",
    "Nenhum arquivo recente": "No recent files",
    "&Limpar lista": "&Clear list",
    "&Editar": "&Edit",
    "&Desfazer": "&Undo",
    "&Refazer": "&Redo",
    "Recor&tar": "Cu&t",
    "&Copiar": "&Copy",
    "C&olar": "&Paste",
    "D&uplicar": "D&uplicate",
    "E&xcluir": "&Delete",
    "Selecionar &tudo": "Select &all",
    "Selecionar do &mesmo tipo": "Select same &kind",
    "&Localizar...": "&Find...",
    "Copiar como &imagem": "Copy as &image",
    "&Organizar": "&Arrange",
    "&Trazer para a frente": "Bring to &front",
    "&Enviar para trás": "Send to &back",
    "A&grupar": "&Group",
    "&Desagrupar": "&Ungroup",
    "&Alinhar": "A&lign",
    "À &esquerda": "&Left",
    "Centro &horizontal": "&Horizontal center",
    "À &direita": "&Right",
    "No &topo": "&Top",
    "Centro &vertical": "&Vertical center",
    "Na &base": "&Bottom",
    "E&xibir": "&View",
    "&Ampliar": "Zoom &in",
    "&Reduzir": "Zoom &out",
    "&Tamanho real": "&Actual size",
    "A&justar à janela": "&Fit to window",
    "&Verificar modelo": "&Check model",
    "&Avisos de estrutura": "&Structure warnings",
    "Laranja: o que a teoria do modelo ER pede além das ligações (entidade sem chave,"
    " relacionamento com um participante só...)": "Orange: what ER model theory asks for beyond"
    " the links (entity without a key, relationship with a single participant...)",
    "&Grade": "&Grid",
    "&Tema": "T&heme",
    "&Claro": "&Light",
    "&Escuro": "&Dark",
    "Do &sistema (qt6ct)": "&System (qt6ct)",
    "&Idioma": "&Language",
    "Idioma": "Language",
    "O idioma muda quando o HaradaER for fechado e aberto de novo.": "The language changes"
    " when HaradaER is closed and opened again.",
    "&Remover vértice": "&Remove vertex",
    "&Adicionar vértice aqui": "&Add vertex here",
    "&Endireitar linha": "&Straighten line",
    # --- painéis e barra de ferramentas -----------------------------------------------------
    "Inspetor de objetos": "Object inspector",
    "Propriedades": "Properties",
    "Mensagens": "Messages",
    "Ferramentas": "Tools",
    "Entidades": "Entities",
    "Relacionamentos": "Relationships",
    "Generalizações": "Generalizations",
    "Atributos sem dono": "Attributes without owner",
    "Outros": "Others",
    "Conexões": "Connections",
    "Localizar elemento...": "Find element...",
    "Nome": "Name",
    "Tipo": "Kind",
    "Nada encontrado": "Nothing found",
    "{n} encontrado(s)": "{n} found",
    "(sem nome)": "(no name)",
    "Erro": "Error",
    "Aviso": "Warning",
    "Elemento": "Element",
    "Mensagem": "Message",
    "Nenhum problema no modelo.": "No problems in the model.",
    "A verificação está desligada (Exibir › Verificar modelo).": "Checking is off"
    " (View › Check model).",
    "{erros} erro(s), {avisos} aviso(s)": "{erros} error(s), {avisos} warning(s)",
    "Tipo:": "Kind:",
    "Nome:": "Name:",
    "Tipo SQL:": "SQL type:",
    "Pode ser nulo": "Nullable",
    "Conexão:": "Connection:",
    "Liga:": "Links:",
    "Rótulo:": "Label:",
    "Nada selecionado.": "Nothing selected.",
    "{n} figuras selecionadas.": "{n} figures selected.",
    "Atributo derivado não tem tipo.": "A derived attribute has no type.",
    # --- verificação e recomendação ---------------------------------------------------------
    "as duas pontas estão soltas": "both ends are loose",
    "a ponta de início está solta": "the start end is loose",
    "a ponta de fim está solta": "the end is loose",
    "ponta solta": "loose end",
    "{conexao} não é aceita entre {inicio} e {fim}": "{conexao} is not accepted between"
    " {inicio} and {fim}",
    "entidade sem atributo chave": "entity without a key attribute",
    "entidade fraca sem relacionamento identificador": "weak entity without an identifying"
    " relationship",
    "relacionamento identificador sem entidade fraca": "identifying relationship without a weak"
    " entity",
    "relacionamento com menos de dois participantes (no recursivo, ligue a entidade duas vezes)": (
        "relationship with fewer than two participants (for a recursive one, link the entity twice)"
    ),
    "especialização sem superclasse ou sem subclasse": "specialization without a superclass or"
    " without a subclass",
    "atributo sem ligação de atributo com um dono": "attribute without an attribute link to an"
    " owner",
    "Aviso: {aviso}": "Warning: {aviso}",
    "aviso de estrutura": "structure warning",
    "avisos de estrutura": "structure warnings",
    "erro de conexão": "connection error",
    "erros de conexão": "connection errors",
    " e ": " and ",
    "{primeiros} e {ultimo}": "{primeiros} and {ultimo}",
    "{partes} (veja o painel Mensagens)": "{partes} (see the Messages panel)",
    "Liga: {pares}": "Links: {pares}",
    "Conexões aceitas entre {a} e {b}: {nomes}": "Connections accepted between {a} and {b}:"
    " {nomes}",
    "Nenhuma conexão aceita entre {a} e {b}": "No connection accepted between {a} and {b}",
    "Esta conexão não é aceita entre estes elementos (será marcada).": "This connection is not"
    " accepted between these elements (it will be marked).",
    # --- desfazer e refazer (nomes dos passos) ----------------------------------------------
    "Adicionar elemento": "Add element",
    "Criar": "Create",
    "Conectar": "Connect",
    "Excluir": "Delete",
    "Mover": "Move",
    "Alinhar": "Align",
    "Redimensionar": "Resize",
    "Renomear": "Rename",
    "Trazer para a frente": "Bring to front",
    "Enviar para trás": "Send to back",
    "Mudar tipo": "Change type",
    "Mudar anulabilidade": "Change nullability",
    "Mudar rótulo": "Change label",
    "Mudar tipo de conexão": "Change connection type",
    "Adicionar vértice": "Add vertex",
    "Mover vértice": "Move vertex",
    "Remover vértice": "Remove vertex",
    "Endireitar linha": "Straighten line",
    "Reconectar": "Reconnect",
    "Corrigir tipos de atributo": "Fix attribute types",
    "Agrupar": "Group",
    "Desagrupar": "Ungroup",
    "Colar": "Paste",
    "Duplicar": "Duplicate",
    # --- arquivos ----------------------------------------------------------------------------
    "Sem título": "Untitled",
    "Abrir modelo": "Open model",
    "Salvar modelo": "Save model",
    "Modelos do TerraER (*.xml)": "TerraER models (*.xml)",
    "Modelos do TerraER (*.xml);;Todos os arquivos (*)": "TerraER models (*.xml);;All files (*)",
    "Salvar as alterações em {nome}?": "Save the changes to {nome}?",
    "Salvo em {caminho}": "Saved to {caminho}",
    "Não foi possível abrir o arquivo": "Could not open the file",
    "O arquivo não existe mais.": "The file no longer exists.",
    "Não foi possível salvar o arquivo": "Could not save the file",
    "Sem permissão para gravar neste local.": "No permission to write to this location.",
    "Já existe uma pasta com esse nome.": "A folder with this name already exists.",
    "A pasta de destino não existe.": "The destination folder does not exist.",
    "Não há espaço livre no disco.": "There is no free space on the disk.",
    "O disco é somente leitura.": "The disk is read-only.",
    "Ocorreu um erro ao gravar o arquivo.": "An error occurred while writing the file.",
    "{motivo}\n\nDetalhe: {detalhe}": "{motivo}\n\nDetail: {detalhe}",
    "Tipos de atributo inválidos": "Invalid attribute types",
    "Estes atributos tinham um tipo que o TerraER não reconhece e passaram a usar o tipo padrão."
    " O TerraER abriria o arquivo, mas não conseguiria salvá-lo.": "These attributes had a type"
    " that TerraER does not recognize and now use the default type. TerraER would open the"
    " file, but could not save it.",
    "... e mais {n}": "... and {n} more",
    # Conexão livre (RF-25)
    "Conexões livres apagadas": "Free connections deleted",
    "O HaradaER não usa a conexão livre, que não tem significado no modelo ER."
    " Foi apagada 1 deste arquivo, entre:": (
        "HaradaER doesn't use the free connection, which has no meaning in the ER model."
        " 1 was deleted from this file, between:"
    ),
    "O HaradaER não usa a conexão livre, que não tem significado no modelo ER."
    " Foram apagadas {n} deste arquivo, entre:": (
        "HaradaER doesn't use the free connection, which has no meaning in the ER model."
        " {n} were deleted from this file, between:"
    ),
    "O arquivo em disco só muda quando você salvar.": (
        "The file on disk only changes when you save."
    ),
    # --- exportar e copiar -------------------------------------------------------------------
    "Exportar desenho": "Export drawing",
    "Imagem PNG": "PNG image",
    "Imagem JPG": "JPG image",
    "Desenho vetorial SVG": "SVG vector drawing",
    "Documento PDF": "PDF document",
    "O desenho está vazio.": "The drawing is empty.",
    "Não foi possível exportar o desenho": "Could not export the drawing",
    "Exportado para {caminho}": "Exported to {caminho}",
    "não foi possível gravar {caminho}": "could not write {caminho}",
    "formato não suportado: {formato}": "unsupported format: {formato}",
    "(sem extensão)": "(no extension)",
    "Desenho copiado como imagem.": "Drawing copied as an image.",
    "Nada para copiar.": "Nothing to copy.",
    "A área de transferência não tem um modelo.": "The clipboard does not hold a model.",
    # --- erros ao abrir um arquivo (RNF-14) -------------------------------------------------
    "{mensagem} (linha {linha})": "{mensagem} (line {linha})",
    "o elemento raiz deve ser <drawing>, mas é <{tag}>": "the root element must be <drawing>,"
    " but it is <{tag}>",
    "o desenho não tem o elemento <figures>": "the drawing has no <figures> element",
    "tag desconhecida <{tag}> dentro de <{pai}>: o TerraER também não abre arquivos com essa tag": (
        "unknown tag <{tag}> inside <{pai}>: TerraER does not open files with this tag either"
    ),
    "o arquivo está vazio ou foi cortado antes do fim": "the file is empty or was cut off"
    " before the end",
    "o arquivo foi cortado no meio de um elemento": "the file was cut off in the middle of an"
    " element",
    "uma tag foi aberta e fechada com nomes diferentes": "a tag was opened and closed with"
    " different names",
    "há conteúdo depois do fim do desenho": "there is content after the end of the drawing",
    "o arquivo usa uma entidade não definida": "the file uses an undefined entity",
    "o texto contém um caractere que o XML não aceita (por exemplo um caractere de controle)": (
        "the text contains a character that XML does not accept (for example a control character)"
    ),
    "o XML tem um erro de sintaxe": "the XML has a syntax error",
    "o XML tem um caractere ou símbolo inválido": "the XML has an invalid character or symbol",
    "o arquivo declara entidades no DOCTYPE, o que não é aceito por segurança": "the file"
    " declares entities in the DOCTYPE, which is not accepted for security reasons",
    "declaração de entidade não é aceita por segurança": "entity declarations are not accepted"
    " for security reasons",
    "o arquivo tem elementos aninhados demais (limite {limite})": "the file has too many nested"
    " elements (limit {limite})",
    "<{nome}> tem 'ref' junto com outros atributos": "<{nome}> has 'ref' together with other"
    " attributes",
    '<{nome}> aponta para o id "{ref}", que não existe (ou aparece só depois)': "<{nome}> points"
    ' to the id "{ref}", which does not exist (or only appears later)',
    "o elemento raiz não pode ser uma referência": "the root element cannot be a reference",
    'o id "{id}" aparece em mais de um elemento (<{nome}>)': 'the id "{id}" appears in more'
    " than one element (<{nome}>)",
    "<{nome}> mistura texto e elementos, o que o formato não permite": "<{nome}> mixes text and"
    " elements, which the format does not allow",
    "o arquivo é grande demais (limite {limite} MiB)": "the file is too large (limit {limite} MiB)",
    "XML inválido: {motivo}": "Invalid XML: {motivo}",
    "o arquivo não tem nenhum elemento": "the file has no elements",
    # Ajuda (RF-21)
    "Aj&uda": "&Help",
    "&Relatar um problema…": "&Report a problem…",
    "&Sugerir uma melhoria…": "&Suggest an improvement…",
    "Abrir no navegador": "Open in browser",
    "Não foi possível abrir o navegador. Copie este endereço:": (
        "The browser couldn't be opened. Copy this address:"
    ),
    # Atualizações (RF-22)
    "Verificar &atualizações…": "Check for &updates…",
    "Verificar ao a&brir": "Check when &opening",
    "Versão nova": "New version",
    "O HaradaER {nova} está disponível (você tem a {atual}).": (
        "HaradaER {nova} is available (you have {atual})."
    ),
    "&Baixar": "&Download",
    "Agora &não": "&Not now",
    "Atualizações": "Updates",
    "Você já tem a versão mais recente ({atual}).": (
        "You already have the latest version ({atual})."
    ),
    "Não foi possível verificar agora (sem internet ou o GitHub não respondeu).": (
        "Couldn't check right now (no internet, or GitHub didn't respond)."
    ),
    # Edição rápida
    "Edição rápid&a": "Quick edit&ing",
    "Atalhos de uma tecla para as ferramentas (E, R, A, G, 1, N, L, H, C, V)": (
        "One-key shortcuts for the tools (E, R, A, G, 1, N, L, H, C, V)"
    ),
    "Espaço cria um elemento: escolha antes um elemento.": (
        "Space creates an element: choose an element first."
    ),
    "Ponha o mouse sobre o desenho.": "Put the mouse over the drawing.",
    "{conexao} não liga {a} e {b}.": "{conexao} doesn't connect {a} and {b}.",
    # Atalhos do teclado
    "Atalhos do &teclado…": "&Keyboard shortcuts…",
    "Atalhos do teclado": "Keyboard shortcuts",
    "Buscar atalho…": "Search shortcuts…",
    "Edição rápida (Editar › Edição rápida)": "Quick editing (Edit › Quick editing)",
    "Ação": "Action",
    "Trocar o tipo do elemento selecionado (com Selecionar)": (
        "Change the selected element's type (with Select)"
    ),
    "Letra da família": "Family letter",
    "Atalho": "Shortcut",
    "Mouse e gestos": "Mouse and gestures",
    "Voltar uma posição no ciclo": "Go back one step in the cycle",
    "Shift + letra": "Shift + letter",
    "Criar onde está o mouse": "Create where the mouse is",
    "Espaço": "Space",
    "Voltar para Selecionar": "Back to Select",
    "Zoom": "Zoom",
    "Pinça, ou Ctrl + roda do mouse": "Pinch, or Ctrl + mouse wheel",
    "Rolar o desenho": "Scroll the drawing",
    "Dois dedos, ou a roda do mouse": "Two fingers, or the mouse wheel",
    "Mover o desenho": "Pan the drawing",
    "Botão do meio e arrastar": "Middle button and drag",
    "Manter a ferramenta depois de criar": "Keep the tool after creating",
    "Shift + clique": "Shift + click",
    "Editar o nome": "Edit the name",
    "Duplo clique no elemento": "Double-click the element",
    "Novo vértice na conexão": "New bend on the connection",
    "Duplo clique na linha": "Double-click the line",
    "Tirar um vértice": "Remove a bend",
    "Duplo clique no vértice": "Double-click the bend",
    # Trocar tipo
    "Trocar tipo": "Change type",
    "Trocar &tipo": "Change &type",
    "Ao virar {tipo}, o elemento perde {perdas}. Trocar mesmo assim?": (
        "As {tipo}, the element loses {perdas}. Change anyway?"
    ),
    "a instrução SQL do atributo derivado": "the derived attribute's SQL statement",
    "o tipo SQL e a anulabilidade do atributo": "the attribute's SQL type and nullability",
}
