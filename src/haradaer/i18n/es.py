"""Traduções para o espanhol: texto em português -> texto em espanhol.

Os nomes dos elementos e conexões seguem os termos usuais do modelo ER em espanhol (a tradução
de Elmasri e Navathe: "entidad débil", "atributo multivalor", "clave parcial"). O `&` marca a
letra de atalho do menu; `{nome}` é preenchido pelo programa.
"""

ES: dict[str, str] = {
    # --- elementos (nome padrão ao criar e nome na interface) --------------------------------
    "Entidade": "Entidad",
    "Entidade fraca": "Entidad débil",
    "Relacionamento": "Relación",
    "Relacionamento fraco": "Relación débil",
    "Entidade associativa": "Entidad asociativa",
    "Atributo": "Atributo",
    "Atributo chave": "Atributo clave",
    "Chave parcial": "Clave parcial",
    "Atributo chave parcial": "Atributo clave parcial",
    "Atributo derivado": "Atributo derivado",
    "Atributo multivalorado": "Atributo multivalor",
    "União": "Unión",
    "Disjunção": "Disyunción",
    "Sobreposição": "Solapamiento",
    "Grupo": "Grupo",
    "característica": "característica",
    # --- conexões ----------------------------------------------------------------------------
    'Participação, lado "1"': 'Participación, lado "1"',
    'Participação, lado "N"': 'Participación, lado "N"',
    'Participação total, lado "1"': 'Participación total, lado "1"',
    'Participação total, lado "N"': 'Participación total, lado "N"',
    "Ligação de atributo": "Enlace de atributo",
    "Generalização simples": "Generalización simple",
    "Participação opcional em generalização": "Participación opcional en generalización",
    "Participação obrigatória em generalização": "Participación obligatoria en generalización",
    # --- nomes curtos da faixa de ferramentas -----------------------------------------------
    "Selecionar": "Seleccionar",
    "Ent. fraca": "Ent. débil",
    "Relacion.": "Relación",
    "Rel. fraco": "Rel. débil",
    "Ent. assoc.": "Ent. asoc.",
    "Chave": "Clave",
    "Ch. parcial": "Cl. parcial",
    "Derivado": "Derivado",
    "Multival.": "Multival.",
    "Sobrepos.": "Solap.",
    "Lado 1": "Lado 1",
    "Lado N": "Lado N",
    "Total 1": "Total 1",
    "Total N": "Total N",
    "Lig. atrib.": "Enl. atrib.",
    "General.": "General.",
    "Gen. opc.": "Gen. opc.",
    "Gen. obrig.": "Gen. oblig.",
    # --- menus -------------------------------------------------------------------------------
    "&Arquivo": "&Archivo",
    "&Novo": "&Nuevo",
    "&Abrir...": "&Abrir...",
    "Abrir &recente": "Abrir &reciente",
    "&Salvar": "&Guardar",
    "Salvar &como...": "Guardar co&mo...",
    "Exportar &desenho...": "Exportar &dibujo...",
    "&Fechar": "&Cerrar",
    "Sa&ir": "&Salir",
    "Nenhum arquivo recente": "Ningún archivo reciente",
    "&Limpar lista": "&Borrar lista",
    "&Editar": "&Editar",
    "&Desfazer": "&Deshacer",
    "&Refazer": "&Rehacer",
    "Recor&tar": "Cor&tar",
    "&Copiar": "&Copiar",
    "C&olar": "&Pegar",
    "D&uplicar": "D&uplicar",
    "E&xcluir": "E&liminar",
    "&Selecionar tudo": "Seleccionar t&odo",
    "Selecionar do &mesmo tipo": "Seleccionar del &mismo tipo",
    "&Localizar...": "&Buscar...",
    "Copiar como ima&gem": "Copiar como &imagen",
    "&Organizar": "&Organizar",
    "&Trazer para a frente": "Traer al &frente",
    "&Enviar para trás": "&Enviar al fondo",
    "A&grupar": "A&grupar",
    "&Desagrupar": "&Desagrupar",
    "&Alinhar": "A&linear",
    "À &esquerda": "A la &izquierda",
    "Centro &horizontal": "Centro &horizontal",
    "À &direita": "A la &derecha",
    "No &topo": "&Arriba",
    "Centro &vertical": "Centro &vertical",
    "Na &base": "A&bajo",
    "E&xibir": "&Ver",
    "&Ampliar": "&Acercar",
    "&Reduzir": "A&lejar",
    "&Tamanho real": "&Tamaño real",
    "A&justar à janela": "A&justar a la ventana",
    "&Verificar modelo": "&Verificar modelo",
    "Avisos de &estrutura": "Avi&sos de estructura",
    "Laranja: o que a teoria do modelo ER pede além das ligações (entidade sem chave,"
    " relacionamento com um participante só...)": "Naranja: lo que la teoría del modelo ER pide"
    " además de los enlaces (entidad sin clave, relación con un solo participante...)",
    "&Grade": "&Cuadrícula",
    "&Claro": "&Claro",
    "&Escuro": "&Oscuro",
    "Do &sistema (qt6ct)": "Del &sistema (qt6ct)",
    "Idioma": "Idioma",
    "O idioma muda quando o HaradaER for fechado e aberto de novo.": "El idioma cambia cuando"
    " HaradaER se cierre y se vuelva a abrir.",
    "&Remover vértice": "&Quitar vértice",
    "&Adicionar vértice aqui": "&Añadir vértice aquí",
    "&Endireitar linha": "&Enderezar línea",
    # --- painéis e barra de ferramentas -----------------------------------------------------
    "Inspetor de objetos": "Inspector de objetos",
    "Propriedades": "Propiedades",
    "Mensagens": "Mensajes",
    "Ferramentas": "Herramientas",
    "Entidades": "Entidades",
    "Relacionamentos": "Relaciones",
    "Generalizações": "Generalizaciones",
    "Atributos sem dono": "Atributos sin dueño",
    "Outros": "Otros",
    "Conexões": "Conexiones",
    "Localizar elemento ou texto...": "Buscar elemento o texto...",
    "Nome": "Nombre",
    "Tipo": "Tipo",
    "Nada encontrado": "No se encontró nada",
    "{n} encontrado(s)": "{n} encontrado(s)",
    "(sem nome)": "(sin nombre)",
    "Erro": "Error",
    "Aviso": "Aviso",
    "Elemento": "Elemento",
    "Mensagem": "Mensaje",
    "Nenhum problema no modelo.": "Ningún problema en el modelo.",
    "{erros} erro(s), {avisos} aviso(s)": "{erros} error(es), {avisos} aviso(s)",
    "Tipo:": "Tipo:",
    "Nome:": "Nombre:",
    "Tipo SQL:": "Tipo SQL:",
    "Pode ser nulo": "Admite nulos",
    "Conexão:": "Conexión:",
    "Liga:": "Une:",
    "Rótulo:": "Etiqueta:",
    "Nada selecionado.": "Nada seleccionado.",
    "{n} figuras selecionadas.": "{n} figuras seleccionadas.",
    "Atributo derivado não tem tipo.": "Un atributo derivado no tiene tipo.",
    # --- verificação e recomendação ---------------------------------------------------------
    "as duas pontas estão soltas": "los dos extremos están sueltos",
    "a ponta de início está solta": "el extremo inicial está suelto",
    "a ponta de fim está solta": "el extremo final está suelto",
    "ponta solta": "extremo suelto",
    "{conexao} não é aceita entre {inicio} e {fim}": "{conexao} no se acepta entre {inicio}"
    " y {fim}",
    "entidade sem atributo chave": "entidad sin atributo clave",
    "entidade fraca sem relacionamento identificador": "entidad débil sin relación identificadora",
    "relacionamento identificador sem entidade fraca": "relación identificadora sin entidad débil",
    "relacionamento com menos de dois participantes (no recursivo, ligue a entidade duas vezes)": (
        "relación con menos de dos participantes (en una recursiva, una la entidad dos veces)"
    ),
    "especialização sem superclasse ou sem subclasse": "especialización sin superclase o sin"
    " subclase",
    "atributo sem ligação de atributo com um dono": "atributo sin enlace de atributo con un dueño",
    "Aviso: {aviso}": "Aviso: {aviso}",
    "aviso de estrutura": "aviso de estructura",
    "avisos de estrutura": "avisos de estructura",
    "erro de conexão": "error de conexión",
    "erros de conexão": "errores de conexión",
    " e ": " y ",
    "{primeiros} e {ultimo}": "{primeiros} y {ultimo}",
    "{partes} (veja o painel Mensagens)": "{partes} (vea el panel Mensajes)",
    "Liga: {pares}": "Une: {pares}",
    "Conexões aceitas entre {a} e {b}: {nomes}": "Conexiones aceptadas entre {a} y {b}: {nomes}",
    "Nenhuma conexão aceita entre {a} e {b}": "Ninguna conexión aceptada entre {a} y {b}",
    "Esta conexão não é aceita entre estes elementos (será marcada).": "Esta conexión no se"
    " acepta entre estos elementos (se marcará).",
    # --- desfazer e refazer (nomes dos passos) ----------------------------------------------
    "Adicionar elemento": "Añadir elemento",
    "Criar": "Crear",
    "Conectar": "Conectar",
    "Excluir": "Eliminar",
    "Mover": "Mover",
    "Alinhar": "Alinear",
    "Redimensionar": "Cambiar tamaño",
    "Renomear": "Renombrar",
    "Trazer para a frente": "Traer al frente",
    "Enviar para trás": "Enviar al fondo",
    "Mudar tipo": "Cambiar tipo",
    "Mudar anulabilidade": "Cambiar nulabilidad",
    "Mudar rótulo": "Cambiar etiqueta",
    "Mudar tipo de conexão": "Cambiar tipo de conexión",
    "Adicionar vértice": "Añadir vértice",
    "Mover vértice": "Mover vértice",
    "Remover vértice": "Quitar vértice",
    "Endireitar linha": "Enderezar línea",
    "Reconectar": "Reconectar",
    "Corrigir tipos de atributo": "Corregir tipos de atributo",
    "Agrupar": "Agrupar",
    "Desagrupar": "Desagrupar",
    "Colar": "Pegar",
    "Duplicar": "Duplicar",
    # --- arquivos ----------------------------------------------------------------------------
    "Sem título": "Sin título",
    "Abrir modelo": "Abrir modelo",
    "Salvar modelo": "Guardar modelo",
    "Modelos do TerraER (*.xml)": "Modelos de TerraER (*.xml)",
    "Modelos do TerraER (*.xml);;Todos os arquivos (*)": "Modelos de TerraER (*.xml);;Todos los"
    " archivos (*)",
    "Salvar as alterações em {nome}?": "¿Guardar los cambios en {nome}?",
    "Salvo em {caminho}": "Guardado en {caminho}",
    "Não foi possível abrir o arquivo": "No se pudo abrir el archivo",
    "O arquivo não existe mais.": "El archivo ya no existe.",
    "Não foi possível salvar o arquivo": "No se pudo guardar el archivo",
    "Sem permissão para gravar neste local.": "Sin permiso para escribir en esta ubicación.",
    "Já existe uma pasta com esse nome.": "Ya existe una carpeta con ese nombre.",
    "A pasta de destino não existe.": "La carpeta de destino no existe.",
    "Não há espaço livre no disco.": "No hay espacio libre en el disco.",
    "O disco é somente leitura.": "El disco es de solo lectura.",
    "Ocorreu um erro ao gravar o arquivo.": "Ocurrió un error al escribir el archivo.",
    "{motivo}\n\nDetalhe: {detalhe}": "{motivo}\n\nDetalle: {detalhe}",
    "Tipos de atributo inválidos": "Tipos de atributo no válidos",
    "Estes atributos tinham um tipo que o TerraER não reconhece e passaram a usar o tipo padrão."
    " O TerraER abriria o arquivo, mas não conseguiria salvá-lo.": "Estos atributos tenían un"
    " tipo que TerraER no reconoce y pasaron a usar el tipo predeterminado. TerraER abriría el"
    " archivo, pero no podría guardarlo.",
    "... e mais {n}": "... y {n} más",
    # Conexão livre (RF-25)
    "Conexões livres apagadas": "Conexiones libres borradas",
    "O HaradaER não usa a conexão livre, que não tem significado no modelo ER."
    " Foi apagada 1 deste arquivo, entre:": (
        "HaradaER no usa la conexión libre, que no tiene significado en el modelo ER."
        " Se borró 1 de este archivo, entre:"
    ),
    "O HaradaER não usa a conexão livre, que não tem significado no modelo ER."
    " Foram apagadas {n} deste arquivo, entre:": (
        "HaradaER no usa la conexión libre, que no tiene significado en el modelo ER."
        " Se borraron {n} de este archivo, entre:"
    ),
    "O arquivo em disco só muda quando você salvar.": (
        "El archivo en disco solo cambia cuando usted lo guarde."
    ),
    # Texto (RF-26, RF-27)
    "Texto": "Texto",
    "Textos": "Textos",
    "Criar texto": "Crear texto",
    "Editar texto": "Editar texto",
    "Textos convertidos": "Textos convertidos",
    "{link} ({tecla}+clique abre)": "{link} ({tecla}+clic lo abre)",
    "{tecla}+clique marca ou desmarca a tarefa": "{tecla}+clic marca o desmarca la tarea",
    "Marcar tarefa": "Marcar tarea",
    "Só links da web (http, https) e de e-mail abrem: {link}": (
        "Solo se abren enlaces web (http, https) y de correo: {link}"
    ),
    "texto": "texto",
    "texto em negrito": "texto en negrita",
    "papel": "papel",
    "O HaradaER tem um só tipo de texto, o Texto (a Área de Texto do TerraER)."
    " 1 texto deste arquivo virou Texto, no mesmo lugar e com a mesma fonte:": (
        "HaradaER tiene un solo tipo de texto, el Texto (el Área de Texto de TerraER)."
        " 1 texto de este archivo pasó a ser Texto, en el mismo lugar y con la misma fuente:"
    ),
    "O HaradaER tem um só tipo de texto, o Texto (a Área de Texto do TerraER)."
    " {n} textos deste arquivo viraram Texto, no mesmo lugar e com a mesma fonte:": (
        "HaradaER tiene un solo tipo de texto, el Texto (el Área de Texto de TerraER)."
        " {n} textos de este archivo pasaron a ser Texto, en el mismo lugar y con la misma"
        " fuente:"
    ),
    # --- exportar e copiar -------------------------------------------------------------------
    "Exportar desenho": "Exportar dibujo",
    "Imagem PNG": "Imagen PNG",
    "Imagem JPG": "Imagen JPG",
    "Desenho vetorial SVG": "Dibujo vectorial SVG",
    "Documento PDF": "Documento PDF",
    "O desenho está vazio.": "El dibujo está vacío.",
    "Não foi possível exportar o desenho": "No se pudo exportar el dibujo",
    "Exportado para {caminho}": "Exportado a {caminho}",
    "não foi possível gravar {caminho}": "no se pudo escribir {caminho}",
    "formato não suportado: {formato}": "formato no admitido: {formato}",
    "(sem extensão)": "(sin extensión)",
    "Desenho copiado como imagem.": "Dibujo copiado como imagen.",
    "Nada para copiar.": "Nada que copiar.",
    "A área de transferência não tem um modelo.": "El portapapeles no contiene un modelo.",
    # --- erros ao abrir um arquivo (RNF-14) -------------------------------------------------
    "{mensagem} (linha {linha})": "{mensagem} (línea {linha})",
    "o elemento raiz deve ser <drawing>, mas é <{tag}>": "el elemento raíz debe ser <drawing>,"
    " pero es <{tag}>",
    "o desenho não tem o elemento <figures>": "el dibujo no tiene el elemento <figures>",
    "tag desconhecida <{tag}> dentro de <{pai}>: o TerraER também não abre arquivos com essa tag": (
        "etiqueta desconocida <{tag}> dentro de <{pai}>: TerraER tampoco abre archivos con esa"
        " etiqueta"
    ),
    "o arquivo está vazio ou foi cortado antes do fim": "el archivo está vacío o se cortó antes"
    " del final",
    "o arquivo foi cortado no meio de um elemento": "el archivo se cortó en medio de un elemento",
    "uma tag foi aberta e fechada com nomes diferentes": "una etiqueta se abrió y se cerró con"
    " nombres distintos",
    "há conteúdo depois do fim do desenho": "hay contenido después del final del dibujo",
    "o arquivo usa uma entidade não definida": "el archivo usa una entidad no definida",
    "o texto contém um caractere que o XML não aceita (por exemplo um caractere de controle)": (
        "el texto contiene un carácter que XML no acepta (por ejemplo, un carácter de control)"
    ),
    "o XML tem um erro de sintaxe": "el XML tiene un error de sintaxis",
    "o XML tem um caractere ou símbolo inválido": "el XML tiene un carácter o símbolo no válido",
    "o arquivo declara entidades no DOCTYPE, o que não é aceito por segurança": "el archivo"
    " declara entidades en el DOCTYPE, lo que no se acepta por seguridad",
    "declaração de entidade não é aceita por segurança": "las declaraciones de entidad no se"
    " aceptan por seguridad",
    "o arquivo tem elementos aninhados demais (limite {limite})": "el archivo tiene demasiados"
    " elementos anidados (límite {limite})",
    "<{nome}> tem 'ref' junto com outros atributos": "<{nome}> tiene 'ref' junto con otros"
    " atributos",
    '<{nome}> aponta para o id "{ref}", que não existe (ou aparece só depois)': "<{nome}> apunta"
    ' al id "{ref}", que no existe (o solo aparece después)',
    "o elemento raiz não pode ser uma referência": "el elemento raíz no puede ser una referencia",
    'o id "{id}" aparece em mais de um elemento (<{nome}>)': 'el id "{id}" aparece en más de un'
    " elemento (<{nome}>)",
    "<{nome}> mistura texto e elementos, o que o formato não permite": "<{nome}> mezcla texto y"
    " elementos, lo que el formato no permite",
    "o arquivo é grande demais (limite {limite} MiB)": "el archivo es demasiado grande (límite"
    " {limite} MiB)",
    "XML inválido: {motivo}": "XML no válido: {motivo}",
    "o arquivo não tem nenhum elemento": "el archivo no tiene ningún elemento",
    # Ajuda (RF-21)
    "Aj&uda": "Ay&uda",
    "&Relatar um problema…": "&Informar de un problema…",
    "&Sugerir uma melhoria…": "&Sugerir una mejora…",
    "Abrir no navegador": "Abrir en el navegador",
    "Não foi possível abrir o navegador. Copie este endereço:": (
        "No se pudo abrir el navegador. Copie esta dirección:"
    ),
    # Atualizações (RF-22)
    "Verificar &atualizações…": "Buscar &actualizaciones…",
    "Verificar ao a&brir": "Buscar al a&brir",
    "Versão nova": "Versión nueva",
    "O HaradaER {nova} está disponível (você tem a {atual}).": (
        "HaradaER {nova} está disponible (usted tiene la {atual})."
    ),
    "&Baixar": "&Descargar",
    "Agora &não": "Ahora &no",
    "Atualizações": "Actualizaciones",
    "Você já tem a versão mais recente ({atual}).": ("Ya tiene la versión más reciente ({atual})."),
    "Não foi possível verificar agora (sem internet ou o GitHub não respondeu).": (
        "No se pudo comprobar ahora (sin internet o GitHub no respondió)."
    ),
    "Atualizar e &reiniciar": "Actualizar y &reiniciar",
    "Baixando o HaradaER {versao}…": "Descargando HaradaER {versao}…",
    "Conferindo a versão nova…": "Comprobando la versión nueva…",
    "O HaradaER {versao} está pronto.": "HaradaER {versao} está listo.",
    "Se continuar agora, a atualização é instalada quando você fechar o HaradaER.": (
        "Si sigue trabajando ahora, la actualización se instala cuando cierre HaradaER."
    ),
    "&Reiniciar agora": "&Reiniciar ahora",
    "Ao &fechar": "Al &cerrar",
    "HaradaER atualizado para a {versao}.": "HaradaER actualizado a la {versao}.",
    "Atualização cancelada.": "Actualización cancelada.",
    "Cancelar": "Cancelar",
    "A atualização automática só funciona no programa baixado em Releases.": (
        "La actualización automática solo funciona en el programa descargado de Releases."
    ),
    "Não há pacote do HaradaER para este processador.": (
        "No hay paquete de HaradaER para este procesador."
    ),
    "Não há pacote do HaradaER para este processador ({maquina}).": (
        "No hay paquete de HaradaER para este procesador ({maquina})."
    ),
    "Mova o HaradaER para a pasta Aplicativos e abra de lá para poder atualizar.": (
        "Mueva HaradaER a la carpeta Aplicaciones y ábralo desde allí para poder actualizar."
    ),
    "Sem permissão para gravar na pasta {pasta}.": "Sin permiso para escribir en la carpeta"
    " {pasta}.",
    "A versão {versao} ainda não está completa no GitHub. Tente mais tarde.": (
        "La versión {versao} aún no está completa en GitHub. Inténtelo más tarde."
    ),
    "O download veio corrompido. Tente de novo.": "La descarga llegó dañada. Inténtelo de nuevo.",
    "O pacote baixado não pôde ser aberto.": "No se pudo abrir el paquete descargado.",
    "O pacote baixado tem um caminho inválido.": "El paquete descargado tiene una ruta no válida.",
    "O pacote baixado não tem o programa.": "El paquete descargado no contiene el programa.",
    "A versão nova não abriu neste computador.": "La versión nueva no se abrió en este equipo.",
    "Não foi possível baixar a versão nova ({erro}).": (
        "No se pudo descargar la versión nueva ({erro})."
    ),
    "Não foi possível trocar o programa ({erro}).": "No se pudo reemplazar el programa ({erro}).",
    "Não foi possível verificar agora ({erro}).": "No se pudo comprobar ahora ({erro}).",
    # Edição rápida
    "Edição rápid&a": "Edición rápid&a",
    "Atalhos de uma tecla para as ferramentas ({teclas})": "Atajos de una tecla para las"
    " herramientas ({teclas})",
    "Espaço cria um elemento: escolha antes um elemento.": (
        "Espacio crea un elemento: elija antes un elemento."
    ),
    "Ponha o mouse sobre o desenho.": "Ponga el ratón sobre el dibujo.",
    "{conexao} não liga {a} e {b}.": "{conexao} no une {a} y {b}.",
    # Atalhos do teclado
    "Atalhos do &teclado…": "Atajos de &teclado…",
    "Atalhos do teclado": "Atajos de teclado",
    "Buscar atalho…": "Buscar atajo…",
    "Edição rápida (Ctrl+Shift+E)": "Edición rápida (Ctrl+Shift+E)",
    "Ação": "Acción",
    "Trocar o tipo do elemento selecionado (com Selecionar)": (
        "Cambiar el tipo del elemento seleccionado (con Seleccionar)"
    ),
    "Letra da família": "Letra de la familia",
    "Atalho": "Atajo",
    "Mouse e gestos": "Ratón y gestos",
    "Voltar uma posição no ciclo": "Retroceder una posición en el ciclo",
    "Shift + letra": "Mayús + letra",
    "Criar onde está o mouse": "Crear donde está el ratón",
    "Espaço": "Espacio",
    "Voltar para Selecionar": "Volver a Seleccionar",
    "Zoom": "Zoom",
    "Pinça, ou Ctrl + roda do mouse": "Pellizcar, o Ctrl + rueda del ratón",
    "Rolar o desenho": "Desplazar el dibujo",
    "Dois dedos, ou a roda do mouse": "Dos dedos, o la rueda del ratón",
    "Mover o desenho": "Mover el dibujo",
    "Botão do meio e arrastar": "Botón central y arrastrar",
    "Manter a ferramenta depois de criar": "Mantener la herramienta después de crear",
    "Shift + clique": "Mayús + clic",
    "Editar o nome": "Editar el nombre",
    "Duplo clique no elemento": "Doble clic en el elemento",
    "Novo vértice na conexão": "Nuevo vértice en la conexión",
    "Duplo clique na linha": "Doble clic en la línea",
    "Tirar um vértice": "Quitar un vértice",
    "Duplo clique no vértice": "Doble clic en el vértice",
    # Trocar tipo
    "Trocar tipo": "Cambiar tipo",
    "Trocar &tipo": "Cambiar &tipo",
    "Ao virar {tipo}, o elemento perde {perdas}. Trocar mesmo assim?": (
        "Al pasar a {tipo}, el elemento pierde {perdas}. ¿Cambiar de todos modos?"
    ),
    "a instrução SQL do atributo derivado": "la instrucción SQL del atributo derivado",
    "o tipo SQL e a anulabilidade do atributo": "el tipo SQL y la nulabilidad del atributo",
    # Preferências e barra de comandos
    "&Preferências…": "Pre&ferencias…",
    "Preferências": "Preferencias",
    "Vale quando o HaradaER for fechado e aberto de novo.": (
        "Se aplica cuando HaradaER se cierre y se vuelva a abrir."
    ),
    "Verificar &agora": "Comprobar &ahora",
    "Você tem a {atual}.": "Usted tiene la {atual}.",
    "No máximo uma vez por dia, no GitHub.": "Como máximo una vez al día, en GitHub.",
    # Sobre, tela cheia e menu Janela (macOS)
    "S&obre o HaradaER": "&Acerca de HaradaER",
    "Sobre o HaradaER": "Acerca de HaradaER",
    "Ferramenta de modelagem Entidade-Relacionamento compatível com o TerraER 3.14.": (
        "Herramienta de modelado Entidad-Relación compatible con TerraER 3.14."
    ),
    "Software livre, sob a licença GNU GPL versão 3.": (
        "Software libre, bajo la licencia GNU GPL versión 3."
    ),
    "Tela c&heia": "&Pantalla completa",
    # Zoom digitado, contagem de erros e Restaurar padrões
    "Zoom: digite a porcentagem e tecle Enter": "Zoom: escriba el porcentaje y pulse Enter",
    "erro": "error",
    "erros": "errores",
    "aviso": "aviso",
    "avisos": "avisos",
    "Verificação desligada": "Verificación desactivada",
    "Restaurar": "Restablecer",
    "&Configurações": "&Configuración",
    "&Tema": "&Tema",
    "Mostrar &faixa de ferramentas": "Mostrar barra de &herramientas",
    "Mostrar &barra de status": "Mostrar barra de &estado",
    "&Restaurar todos os padrões": "&Restablecer todos los valores",
    "A verificação está desligada (Configurações › Verificar modelo).": (
        "La verificación está desactivada (Configuración › Verificar modelo)."
    ),
    "Voltar ao padrão o tema, as barras, a grade, os painéis, a verificação, a"
    " Edição rápida e as atualizações? O idioma e os arquivos recentes não mudam.": (
        "¿Volver a los valores predeterminados el tema, las barras, la cuadrícula, los"
        " paneles, la verificación, la Edición rápida y las actualizaciones? El idioma y los"
        " archivos recientes no cambian."
    ),
    "Trocar o &idioma…": "Cambiar el idio&ma…",
    "&Manual do HaradaER": "Ma&nual de HaradaER",
    "Manual do HaradaER": "Manual de HaradaER",
    "Buscar no manual…": "Buscar en el manual…",
    "&Anterior": "&Anterior",
    "Pró&ximo": "&Siguiente",
    "{atual} de {total}": "{atual} de {total}",
    "D&esmarcar tudo": "D&eseleccionar todo",
}
