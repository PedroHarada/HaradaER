"""Janela de um documento (RF-19): cada modelo abre na sua própria janela."""

from __future__ import annotations

import errno
from pathlib import Path

import shiboken6
from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from haradaer.core import io
from haradaer.core.commands import (
    PASTE_OFFSET,
    fix_attribute_types_command,
    invalid_attribute_types,
)
from haradaer.core.errors import ArquivoInvalidoError
from haradaer.core.figures.types import NodeFigure
from haradaer.core.model.document import Document
from haradaer.core.rules import (
    is_valid_connection,
    recommend_connections,
    recommend_elements,
    validate,
)
from haradaer.core.rules.tables import LINE_FREE, RECOMMENDATION_ORDER
from haradaer.gui.editor import Editor
from haradaer.gui.export import EXPORT_FORMATS, EmptyDiagramError, export_diagram, render_image
from haradaer.gui.inspector import ObjectInspector
from haradaer.gui.palette import CONNECTIONS, ELEMENTS
from haradaer.gui.properties import PropertiesPanel
from haradaer.gui.scene import DiagramScene
from haradaer.gui.settings import RecentFiles, save_window_layout, window_layout
from haradaer.gui.theme import THEMES, apply_theme, current_theme
from haradaer.gui.theme import manager as theme_manager
from haradaer.gui.tool_icons import (
    SHORT_NAMES,
    connection_icon,
    element_icon,
    select_icon,
)
from haradaer.gui.tool_strip import ToolStrip
from haradaer.gui.verification import name_of, pairs_text
from haradaer.gui.view import SELECT, DiagramView, Tool

TITLE = "HaradaER"
DOCK_MIN_WIDTH = 230
CLIPBOARD_MIME = "application/x-haradaer-figuras"  # pedaço de arquivo no formato do TerraER
UNTITLED = "Sem título"

ALIGN_NAMES = [
    ("left", "À &esquerda"),
    ("center", "Centro &horizontal"),
    ("right", "À &direita"),
    ("top", "No &topo"),
    ("middle", "Centro &vertical"),
    ("bottom", "Na &base"),
]

_SAVE_ERRORS = {
    errno.ENOSPC: "Não há espaço livre no disco.",
    errno.EROFS: "O disco é somente leitura.",
}


def save_error_text(erro: OSError) -> str:
    """Explica em português por que a gravação falhou (RF-17); o detalhe técnico vai embaixo."""
    if isinstance(erro, PermissionError):
        motivo = "Sem permissão para gravar neste local."
    elif isinstance(erro, IsADirectoryError):
        motivo = "Já existe uma pasta com esse nome."
    elif isinstance(erro, FileNotFoundError):
        motivo = "A pasta de destino não existe."
    else:
        motivo = _SAVE_ERRORS.get(erro.errno, "Ocorreu um erro ao gravar o arquivo.")
    detalhe = erro.strerror or str(erro)
    return f"{motivo}\n\nDetalhe: {detalhe}"


class DocumentWindow(QMainWindow):
    closed = Signal(object)
    open_requested = Signal()
    new_requested = Signal()
    open_path_requested = Signal(object)

    def __init__(self, recent: RecentFiles | None = None) -> None:
        super().__init__()
        self.path: Path | None = None
        self.recent = recent if recent is not None else RecentFiles()
        self._last_paste: str | None = None
        self._paste_count = 0
        self.diagram_scene = DiagramScene()
        self.view = DiagramView(self.diagram_scene)
        self.setCentralWidget(self.view)
        self.resize(960, 640)
        self._tool_actions: dict[Tool, QAction] = {}

        self._zoom_label = QLabel("100%")
        self.statusBar().addPermanentWidget(self._zoom_label)
        self.view.zoom_changed.connect(self._show_zoom)
        self.view.message.connect(self.statusBar().showMessage)
        self.view.tool_changed.connect(self._tool_changed)
        self.diagram_scene.selectionChanged.connect(self._selection_changed)
        self._build_docks()
        self._build_menus()
        self._build_toolbar()
        self._restore_layout()
        self._attach(Document.new(), None)

    # --- menus e ferramentas -----------------------------------------------------------------

    def _action(self, texto: str, atalho, funcao) -> QAction:
        acao = QAction(texto, self)
        if atalho is not None:
            acao.setShortcut(atalho)
        acao.triggered.connect(funcao)
        return acao

    def _build_menus(self) -> None:
        arquivo = self.menuBar().addMenu("&Arquivo")
        self.action_new = self._action(
            "&Novo", QKeySequence.StandardKey.New, self.new_requested.emit
        )
        self.action_open = self._action(
            "&Abrir...", QKeySequence.StandardKey.Open, self.open_requested.emit
        )
        self.action_save = self._action("&Salvar", QKeySequence.StandardKey.Save, self.save)
        self.action_save_as = self._action(
            "Salvar &como...", QKeySequence.StandardKey.SaveAs, self.save_as
        )
        self.action_close = self._action("&Fechar", QKeySequence.StandardKey.Close, self.close)
        self.action_quit = self._action("&Sair", QKeySequence.StandardKey.Quit, self._quit)
        arquivo.addActions([self.action_new, self.action_open])
        self.recent_menu = arquivo.addMenu("Abrir &recente")
        self.recent_menu.aboutToShow.connect(self._fill_recent_menu)
        arquivo.addSeparator()
        arquivo.addActions([self.action_save, self.action_save_as])
        arquivo.addSeparator()
        self.action_export = self._action("&Exportar desenho...", "Ctrl+E", self.export)
        arquivo.addAction(self.action_export)
        arquivo.addSeparator()
        arquivo.addActions([self.action_close, self.action_quit])

        editar = self.menuBar().addMenu("&Editar")
        self.action_undo = self._action("&Desfazer", QKeySequence.StandardKey.Undo, self._undo)
        self.action_redo = self._action("&Refazer", QKeySequence.StandardKey.Redo, self._redo)
        self.action_delete = self._action("E&xcluir", QKeySequence.StandardKey.Delete, self._delete)
        editar.addActions([self.action_undo, self.action_redo])
        editar.addSeparator()
        self.action_cut = self._action("Recor&tar", QKeySequence.StandardKey.Cut, self.cut)
        self.action_copy = self._action("&Copiar", QKeySequence.StandardKey.Copy, self.copy)
        self.action_paste = self._action("C&olar", QKeySequence.StandardKey.Paste, self.paste)
        self.action_duplicate = self._action("D&uplicar", "Ctrl+D", self.duplicate)
        editar.addActions([self.action_cut, self.action_copy, self.action_paste])
        editar.addAction(self.action_duplicate)
        editar.addSeparator()
        editar.addAction(self.action_delete)
        editar.addSeparator()
        self.action_select_all = self._action(
            "Selecionar &tudo", QKeySequence.StandardKey.SelectAll, self._select_all
        )
        self.action_select_same = self._action(
            "Selecionar do &mesmo tipo", "Ctrl+Shift+A", self._select_same_kind
        )
        editar.addActions([self.action_select_all, self.action_select_same])
        editar.addSeparator()
        self.action_find = self._action("&Localizar...", QKeySequence.StandardKey.Find, self._find)
        editar.addAction(self.action_find)
        editar.addSeparator()
        self.action_copy_image = self._action(
            "Copiar como &imagem", "Ctrl+Shift+C", self.copy_image
        )
        editar.addAction(self.action_copy_image)

        organizar = self.menuBar().addMenu("&Organizar")
        self.action_front = self._action("&Trazer para a frente", "Ctrl+]", self._bring_to_front)
        self.action_back = self._action("&Enviar para trás", "Ctrl+[", self._send_to_back)
        organizar.addActions([self.action_front, self.action_back])
        organizar.addSeparator()
        self.action_group = self._action("A&grupar", "Ctrl+G", self.group)
        self.action_ungroup = self._action("&Desagrupar", "Ctrl+Shift+G", self.ungroup)
        organizar.addActions([self.action_group, self.action_ungroup])
        organizar.addSeparator()
        alinhar = organizar.addMenu("&Alinhar")
        self.align_actions: dict[str, QAction] = {}
        for modo, texto in ALIGN_NAMES:
            acao = self._action(texto, None, lambda _=False, m=modo: self._align(m))
            self.align_actions[modo] = acao
            alinhar.addAction(acao)
            if modo == "right":
                alinhar.addSeparator()

        exibir = self.menuBar().addMenu("E&xibir")
        self.action_zoom_in = self._action(
            "&Ampliar", QKeySequence.StandardKey.ZoomIn, self.view.zoom_in
        )
        self.action_zoom_out = self._action(
            "&Reduzir", QKeySequence.StandardKey.ZoomOut, self.view.zoom_out
        )
        self.action_zoom_actual = self._action("&Tamanho real", "Ctrl+0", self.view.zoom_actual)
        self.action_zoom_fit = self._action("A&justar à janela", "Ctrl+9", self.view.zoom_fit)
        exibir.addActions(
            [
                self.action_zoom_in,
                self.action_zoom_out,
                self.action_zoom_actual,
                self.action_zoom_fit,
            ]
        )
        exibir.addSeparator()
        self.action_validate = QAction("&Verificar modelo", self)
        self.action_validate.setCheckable(True)
        self.action_validate.setChecked(True)
        self.action_validate.toggled.connect(self._refresh_issues)
        self.action_grid = QAction("&Grade", self)
        self.action_grid.setShortcut("Ctrl+'")
        self.action_grid.setCheckable(True)
        self.action_grid.toggled.connect(self.view.set_grid)
        exibir.addActions([self.action_validate, self.action_grid])
        tema = exibir.addMenu("&Tema")
        temas = QActionGroup(self)
        self.theme_actions: dict[str, QAction] = {}
        for nome, opcao in THEMES.items():
            acao = QAction(opcao.label, self, checkable=True)
            acao.setChecked(nome == current_theme().name)
            acao.triggered.connect(lambda _=False, t=opcao: apply_theme(t))
            temas.addAction(acao)
            tema.addAction(acao)
            self.theme_actions[nome] = acao
        theme_manager().changed.connect(self._theme_changed)
        exibir.addSeparator()
        exibir.addActions(
            [self.inspector_dock.toggleViewAction(), self.properties_dock.toggleViewAction()]
        )

    def _build_docks(self) -> None:
        """Painéis acopláveis à direita do desenho (RNF-09)."""
        self.inspector = ObjectInspector()
        self.inspector.selection_requested.connect(self._select_from_inspector)
        self.inspector.locate_requested.connect(self.locate)
        self.inspector_dock = QDockWidget("Inspetor de objetos", self)
        self.inspector_dock.setObjectName("inspetor")
        self.inspector_dock.setWidget(self.inspector)
        self.properties = PropertiesPanel()
        self.properties_dock = QDockWidget("Propriedades", self)
        self.properties_dock.setObjectName("propriedades")
        self.properties_dock.setWidget(self.properties)
        for dock in (self.inspector_dock, self.properties_dock):
            dock.setMinimumWidth(DOCK_MIN_WIDTH)  # sem isso os nomes ficavam cortados
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _build_toolbar(self) -> None:
        """Uma faixa no alto com todas as ferramentas, que rola na horizontal (`ToolStrip`).

        Fica dentro de uma barra fixa, com nome novo: uma disposição de janela salva antes não
        consegue mudá-la de lugar nem quebrá-la em duas linhas.
        """
        barra = QToolBar("Ferramentas", self)
        barra.setObjectName("faixa-ferramentas")
        barra.setMovable(False)
        barra.setFloatable(False)
        barra.toggleViewAction().setEnabled(False)
        self.tool_strip = ToolStrip()
        barra.addWidget(self.tool_strip)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, barra)
        self.tool_bar = barra
        grupo = QActionGroup(self)

        def adicionar(tool: Tool, texto: str) -> None:
            if tool.kind == "select":
                icone, curto = select_icon(), "Selecionar"
            elif tool.kind == "create":
                icone, curto = element_icon(tool.tag), SHORT_NAMES[tool.tag]
            else:
                icone, curto = connection_icon(tool.tag), SHORT_NAMES[tool.tag]
            acao = QAction(icone, curto, self)
            acao.setToolTip(texto)
            acao.setStatusTip(texto)
            acao.setCheckable(True)
            acao.triggered.connect(lambda _=False, t=tool: self._tool_clicked(t))
            grupo.addAction(acao)
            self.tool_strip.add_action(acao)
            self._tool_actions[tool] = acao

        adicionar(SELECT, "Selecionar")
        self.tool_strip.add_separator()
        for tag, nome in ELEMENTS:
            adicionar(Tool("create", tag), nome)
        self.tool_strip.add_separator()
        for tag, nome in CONNECTIONS:
            adicionar(Tool("connect", tag), nome)
        self.tool_strip.finish()
        self._tool_actions[SELECT].setChecked(True)

    def _theme_changed(self, tema) -> None:
        """Marca o tema no menu e redesenha os ícones da faixa (as linhas seguem o tema)."""
        self.theme_actions[tema.name].setChecked(True)
        self.tool_strip.refresh_style()
        for tool, acao in self._tool_actions.items():
            if tool.kind == "create":
                acao.setIcon(element_icon(tool.tag))
            elif tool.kind == "connect":
                acao.setIcon(connection_icon(tool.tag))
        self.view.viewport().update()

    def _tool_changed(self, tool: Tool) -> None:
        self._tool_actions[tool].setChecked(True)
        self.tool_strip.ensure_visible(self._tool_actions[tool])
        if tool.kind == "connect" and tool.tag != LINE_FREE:
            self.statusBar().showMessage(f"Liga: {pairs_text(recommend_elements(tool.tag))}")
        else:
            self.statusBar().clearMessage()

    # --- recomendação (RF-10) ----------------------------------------------------------------

    def _selected_pair(self) -> tuple[NodeFigure, NodeFigure] | None:
        figuras = self.diagram_scene.selected_figures()
        if len(figuras) == 2 and all(isinstance(f, NodeFigure) for f in figuras):
            return figuras[0], figuras[1]
        return None

    def _update_recommendation(self) -> None:
        """Com dois elementos selecionados, põe em negrito as conexões aceitas entre eles."""
        par = self._selected_pair()
        validos = set() if par is None else self._valid_for(*par)
        for tool, acao in self._tool_actions.items():
            if tool.kind == "connect":
                fonte = acao.font()
                fonte.setBold(tool.tag in validos)
                acao.setFont(fonte)
        if par is None:
            return
        a, b = (name_of(f.tag) for f in par)
        if validos:
            nomes = ", ".join(name_of(t) for t in RECOMMENDATION_ORDER if t in validos)
            self.statusBar().showMessage(f"Conexões aceitas entre {a} e {b}: {nomes}")
        else:
            self.statusBar().showMessage(f"Nenhuma conexão aceita entre {a} e {b}")

    @staticmethod
    def _valid_for(a: NodeFigure, b: NodeFigure) -> set[str]:
        # Nos dois sentidos: `generalizacaoLine` só vale com o círculo na origem.
        return {*recommend_connections(a.tag, b.tag), *recommend_connections(b.tag, a.tag)}

    def _tool_clicked(self, tool: Tool) -> None:
        """Um tipo de conexão aceito, com dois elementos selecionados, liga os dois na hora."""
        par = self._selected_pair()
        if tool.kind == "connect" and par is not None and tool.tag in self._valid_for(*par):
            a, b = par
            origem, destino = (a, b) if is_valid_connection(tool.tag, a.tag, b.tag) else (b, a)
            conexao = self._editor.connect(tool.tag, origem, destino)
            self.diagram_scene.select_only(conexao)
            self._tool_actions[self.view.tool].setChecked(True)
            return
        self.view.set_tool(tool)

    @staticmethod
    def _quit() -> None:
        QApplication.closeAllWindows()

    # --- documento ---------------------------------------------------------------------------

    @property
    def editor(self) -> Editor:
        return self._editor

    @property
    def is_empty(self) -> bool:
        """Janela virgem, que pode ser reaproveitada para abrir um arquivo."""
        return self.path is None and not self._editor.history.is_dirty

    def _attach(self, documento: Document, caminho: Path | None) -> None:
        self.path = caminho
        self._editor = Editor(documento)
        self._editor.history.subscribe(self._history_changed)
        self.diagram_scene.set_document(documento)
        self.view.set_editor(self._editor)
        self.properties.set_editor(self._editor)
        self.view.set_tool(SELECT)
        self._history_changed()

    def load(self, caminho: Path) -> bool:
        """Abre o arquivo nesta janela. Em caso de erro mostra a mensagem e devolve `False`."""
        try:
            documento = io.load(caminho)
        except (ArquivoInvalidoError, OSError) as erro:
            QMessageBox.critical(
                self, "Não foi possível abrir o arquivo", f"{caminho.name}\n\n{erro}"
            )
            return False
        self._attach(documento, caminho)
        self.recent.add(caminho)
        self._fix_invalid_attribute_types()
        self.view.zoom_actual()
        self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().minimum())
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().minimum())
        return True

    def _fix_invalid_attribute_types(self) -> None:
        """RNF-16: tipo de atributo inválido vira o tipo padrão, com aviso (o TerraER abriria o
        arquivo, mas falharia ao salvar). A troca fica no histórico e pode ser desfeita."""
        invalidos = invalid_attribute_types(self._editor.document)
        if not invalidos:
            return
        linhas = [f"• {no.name or '(sem nome)'}: {no.attribute_type}" for no in invalidos[:10]]
        if len(invalidos) > 10:
            linhas.append(f"... e mais {len(invalidos) - 10}")
        self._editor.history.execute(fix_attribute_types_command(self._editor.document))
        QMessageBox.warning(
            self,
            "Tipos de atributo inválidos",
            "Estes atributos tinham um tipo que o TerraER não reconhece e passaram a usar o tipo "
            "padrão. O TerraER abriria o arquivo, mas não conseguiria salvá-lo.\n\n"
            + "\n".join(linhas),
        )

    def save(self) -> bool:
        """Grava no arquivo atual (ou pergunta onde). Devolve `False` se não gravou."""
        if self.path is None:
            return self.save_as()
        return self._write(self.path)

    def save_as(self) -> bool:
        inicial = str(self.path) if self.path else f"{UNTITLED}.xml"
        nome, _ = QFileDialog.getSaveFileName(
            self, "Salvar modelo", inicial, "Modelos do TerraER (*.xml)"
        )
        if not nome:
            return False
        caminho = Path(nome)
        if caminho.suffix.lower() != ".xml":
            caminho = caminho.with_name(caminho.name + ".xml")
        return self._write(caminho)

    def _write(self, caminho: Path) -> bool:
        try:
            io.save(self._editor.document, caminho)
        except OSError as erro:
            QMessageBox.critical(
                self,
                "Não foi possível salvar o arquivo",
                f"{caminho.name}\n\n{save_error_text(erro)}",
            )
            return False
        self.path = caminho.resolve()
        self.recent.add(self.path)
        self._editor.history.mark_clean()
        self.statusBar().showMessage(f"Salvo em {caminho}", 4000)
        return True

    # --- edição ------------------------------------------------------------------------------

    def _undo(self) -> None:
        self._editor.history.undo()

    def _redo(self) -> None:
        self._editor.history.redo()

    # --- recentes, exportação e disposição ---------------------------------------------------

    def _fill_recent_menu(self) -> None:
        self.recent_menu.clear()
        caminhos = self.recent.paths()
        for numero, caminho in enumerate(caminhos, start=1):
            rotulo = f"&{numero} {caminho.name}" if numero < 10 else caminho.name
            acao = self.recent_menu.addAction(f"{rotulo}  ({caminho.parent})")
            acao.triggered.connect(lambda _=False, c=caminho: self.open_recent(c))
        if not caminhos:
            vazio = self.recent_menu.addAction("Nenhum arquivo recente")
            vazio.setEnabled(False)
            return
        self.recent_menu.addSeparator()
        self.recent_menu.addAction("&Limpar lista", self.recent.clear)

    def open_recent(self, caminho: Path) -> None:
        if not caminho.is_file():
            self.recent.remove(caminho)
            QMessageBox.critical(
                self, "Não foi possível abrir o arquivo", f"{caminho}\n\nO arquivo não existe mais."
            )
            return
        self.open_path_requested.emit(caminho)

    def export(self) -> bool:
        """Pergunta onde e grava o desenho como imagem, SVG ou PDF (RF-11)."""
        filtros = ";;".join(
            f"{nome} (*.{ext}{' *.jpeg' if ext == 'jpg' else ''})" for ext, nome in EXPORT_FORMATS
        )
        base = self.path.with_suffix(".png") if self.path else Path(f"{UNTITLED}.png")
        nome, filtro = QFileDialog.getSaveFileName(self, "Exportar desenho", str(base), filtros)
        if not nome:
            return False
        caminho = Path(nome)
        extensoes = {f".{ext}" for ext, _ in EXPORT_FORMATS} | {".jpeg"}
        if caminho.suffix.lower() not in extensoes:
            escolhida = next(
                (ext for ext, rotulo in EXPORT_FORMATS if filtro.startswith(rotulo)), "png"
            )
            caminho = caminho.with_name(f"{caminho.name}.{escolhida}")
        try:
            export_diagram(self.diagram_scene, caminho, self.path.stem if self.path else UNTITLED)
        except EmptyDiagramError:
            QMessageBox.information(self, "Exportar desenho", "O desenho está vazio.")
            return False
        except OSError as erro:
            QMessageBox.critical(
                self,
                "Não foi possível exportar o desenho",
                f"{caminho.name}\n\n{save_error_text(erro)}",
            )
            return False
        self.statusBar().showMessage(f"Exportado para {caminho}", 4000)
        return True

    def copy_image(self) -> bool:
        try:
            imagem = render_image(self.diagram_scene)
        except EmptyDiagramError:
            self.statusBar().showMessage("O desenho está vazio.", 4000)
            return False
        QApplication.clipboard().setImage(imagem)
        self.statusBar().showMessage("Desenho copiado como imagem.", 4000)
        return True

    def _restore_layout(self) -> None:
        """Volta o tamanho da janela e a posição dos painéis da última sessão (RNF-09)."""
        geometria, estado = window_layout()
        if geometria is not None:
            self.restoreGeometry(geometria)
        if estado is not None:
            self.restoreState(estado)

    def _selection_changed(self) -> None:
        if not shiboken6.isValid(self.diagram_scene) or not shiboken6.isValid(self.inspector):
            return  # a cena avisa a seleção também enquanto é destruída
        selecionadas = self.diagram_scene.selected_figures()
        self._update_recommendation()
        self.inspector.select_figures(selecionadas)
        self.properties.show_figures(selecionadas)

    def _select_from_inspector(self, figuras: list) -> None:
        """Seleciona as figuras; um elemento dentro de grupo seleciona o grupo."""
        itens = {self.diagram_scene.item_containing(f) for f in figuras} - {None}
        self.diagram_scene.select_where(lambda f: self.diagram_scene.item_for(f) in itens)
        if len(figuras) == 1:
            self._show_in_view(figuras[0])

    def _show_in_view(self, figura) -> None:
        item = self.diagram_scene.item_containing(figura)
        if item is not None:
            self.view.ensureVisible(item, 40, 40)

    def locate(self, figura) -> None:
        """Seleciona a figura e a traz para o centro do desenho (RF-08)."""
        item = self.diagram_scene.item_containing(figura)
        if item is not None:
            self.diagram_scene.select_only(item.figure)
            self.view.centerOn(item)

    def _find(self) -> None:
        self.inspector_dock.show()
        self.inspector_dock.raise_()
        self.inspector.focus_search()

    # --- copiar, colar, duplicar, agrupar --------------------------------------------------------

    def copy(self) -> bool:
        texto = self._editor.copy_text(self.diagram_scene.selected_figures())
        if texto is None:
            self.statusBar().showMessage("Nada para copiar.", 3000)
            return False
        dados = QMimeData()
        dados.setData(CLIPBOARD_MIME, texto.encode("ascii"))
        QApplication.clipboard().setMimeData(dados)
        return True

    def cut(self) -> None:
        if self.copy():
            self._delete()

    def paste(self) -> bool:
        dados = QApplication.clipboard().mimeData()
        if dados is None or not dados.hasFormat(CLIPBOARD_MIME):
            return False
        texto = bytes(dados.data(CLIPBOARD_MIME).data()).decode("ascii", errors="replace")
        # colar de novo o mesmo conteúdo desloca mais um pouco, para não cair em cima
        vezes = self._paste_count + 1 if texto == self._last_paste else 1
        novas = self._editor.paste(texto, PASTE_OFFSET * vezes)
        if novas is None:
            self.statusBar().showMessage("A área de transferência não tem um modelo.", 3000)
            return False
        self._last_paste, self._paste_count = texto, vezes
        self._select_figures(novas)
        return True

    def duplicate(self) -> None:
        novas = self._editor.duplicate(self.diagram_scene.selected_figures())
        if novas:
            self._select_figures(novas)

    def group(self) -> None:
        grupo = self._editor.group(self.diagram_scene.selected_figures())
        if grupo is not None:
            self.diagram_scene.select_only(grupo)

    def ungroup(self) -> None:
        soltas = []
        for figura in self.diagram_scene.selected_figures():
            if figura.tag == "g":
                soltas += self._editor.ungroup(figura)
        if soltas:
            self._select_figures(soltas)

    def _select_figures(self, figuras: list) -> None:
        chaves = {id(f) for f in figuras}
        self.diagram_scene.select_where(lambda f: id(f) in chaves)

    def _delete(self) -> None:
        self._editor.delete(self.diagram_scene.selected_figures())

    def _select_all(self) -> None:
        self.diagram_scene.select_where(lambda _: True)

    def _select_same_kind(self) -> None:
        tipos = {f.tag for f in self.diagram_scene.selected_figures()}
        self.diagram_scene.select_where(lambda f: f.tag in tipos)

    def _bring_to_front(self) -> None:
        self._editor.bring_to_front(self.diagram_scene.selected_figures())

    def _send_to_back(self) -> None:
        self._editor.send_to_back(self.diagram_scene.selected_figures())

    def _align(self, modo: str) -> None:
        self._editor.align(self.diagram_scene.selected_figures(), modo)

    def _history_changed(self) -> None:
        historico = self._editor.history
        self.action_undo.setEnabled(historico.can_undo)
        self.action_redo.setEnabled(historico.can_redo)
        self.action_undo.setText(f"&Desfazer {historico.undo_label}".rstrip())
        self.action_redo.setText(f"&Refazer {historico.redo_label}".rstrip())
        self._update_title()
        self._refresh_issues()
        self.inspector.refresh(self._editor.document)
        self._selection_changed()

    def _refresh_issues(self) -> None:
        """Refaz a verificação do modelo inteiro; os diagramas de ER são pequenos."""
        ligada = self.action_validate.isChecked()
        self.diagram_scene.show_issues(validate(self._editor.document) if ligada else [])

    def _update_title(self) -> None:
        nome = self.path.name if self.path else UNTITLED
        self.setWindowTitle(f"{nome}[*] - {TITLE}")
        self.setWindowModified(self._editor.history.is_dirty)

    def _show_zoom(self, zoom: float) -> None:
        self._zoom_label.setText(f"{round(zoom * 100)}%")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._editor.history.is_dirty and not self._confirm_discard():
            event.ignore()
            return
        save_window_layout(self.saveGeometry(), self.saveState())
        self.closed.emit(self)
        super().closeEvent(event)

    def _confirm_discard(self) -> bool:
        """Pergunta o que fazer com as alterações. `False` cancela o fechamento."""
        botoes = QMessageBox.StandardButton
        resposta = QMessageBox.question(
            self,
            TITLE,
            f"Salvar as alterações em {self.path.name if self.path else UNTITLED}?",
            botoes.Save | botoes.Discard | botoes.Cancel,
            botoes.Save,
        )
        if resposta == botoes.Save:
            return self.save()
        return resposta == botoes.Discard
