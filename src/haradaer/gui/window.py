"""Janela de um documento (RF-19): cada modelo abre na sua própria janela."""

from __future__ import annotations

import errno
from pathlib import Path

import shiboken6
from PySide6.QtCore import QEvent, QMimeData, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QToolBar,
    QToolButton,
)

import haradaer
from haradaer.core import io
from haradaer.core.commands import (
    PASTE_OFFSET,
    convert_free_texts,
    fix_attribute_types_command,
    invalid_attribute_types,
    node_type_family,
    remove_free_connections,
)
from haradaer.core.errors import ArquivoInvalidoError
from haradaer.core.figures.factory import KINDS
from haradaer.core.figures.types import NodeFigure
from haradaer.core.model.document import Document
from haradaer.core.model.element import Element
from haradaer.core.rules import (
    check_structure,
    is_valid_connection,
    recommend_connections,
    recommend_elements,
    validate,
)
from haradaer.core.rules.tables import RECOMMENDATION_ORDER
from haradaer.feedback import REPOSITORIO, Tipo, issue_url, system_description
from haradaer.gui.editor import Editor
from haradaer.gui.export import EXPORT_FORMATS, EmptyDiagramError, export_diagram, render_image
from haradaer.gui.inspector import ObjectInspector, display_name
from haradaer.gui.manual_dialog import ManualDialog, manual_path
from haradaer.gui.messages import OFF_TEXT, MessagesPanel
from haradaer.gui.palette import CONNECTIONS, ELEMENTS, TEXTS
from haradaer.gui.preferences_dialog import PreferencesDialog
from haradaer.gui.properties import PropertiesPanel
from haradaer.gui.qt_utils import QtMeasurer
from haradaer.gui.recovery import Leftover, RecoveryCopy
from haradaer.gui.scene import DiagramScene
from haradaer.gui.scene.items import WARNING_COLOR
from haradaer.gui.settings import (
    RecentFiles,
    quick_edit_enabled,
    recovery_interval,
    save_window_layout,
    saved_language,
    set_quick_edit_enabled,
    set_saved_language,
    set_status_bar_enabled,
    set_structure_warnings_enabled,
    set_update_check_enabled,
    status_bar_enabled,
    structure_warnings_enabled,
    update_check_enabled,
    window_layout,
)
from haradaer.gui.shortcuts import FAMILIES, key_of, next_tool, position
from haradaer.gui.shortcuts_dialog import MANUALS, ShortcutsDialog
from haradaer.gui.theme import apply_theme, available_themes, current_theme, theme_named
from haradaer.gui.theme import manager as theme_manager
from haradaer.gui.tool_icons import (
    SHORT_NAMES,
    connection_icon,
    element_icon,
    select_icon,
)
from haradaer.gui.tool_strip import ToolStrip
from haradaer.gui.updates import UpdateChecker
from haradaer.gui.verification import issue_count, name_of, pairs_text, summary_text
from haradaer.gui.view import INVALID_COLOR, SELECT, DiagramView, Tool
from haradaer.i18n import LANGUAGES, N_, _, language, translate

TITLE = "HaradaER"
DOCK_MIN_WIDTH = 230
CLIPBOARD_MIME = "application/x-haradaer-figuras"  # pedaço de arquivo no formato do TerraER
UNTITLED = N_("Sem título")

ALIGN_NAMES = [
    ("left", N_("À &esquerda")),
    ("center", N_("Centro &horizontal")),
    ("right", N_("À &direita")),
    ("top", N_("No &topo")),
    ("middle", N_("Centro &vertical")),
    ("bottom", N_("Na &base")),
]

_SAVE_ERRORS = {
    errno.ENOSPC: N_("Não há espaço livre no disco."),
    errno.EROFS: N_("O disco é somente leitura."),
}


class _ZoomField(QLineEdit):
    """Campo do zoom na barra de status: Esc desiste do que foi digitado."""

    def keyPressEvent(self, evento) -> None:  # noqa: N802 (nome do Qt)
        if evento.key() == Qt.Key.Key_Escape:
            self.clearFocus()  # `editingFinished` reescreve o zoom atual
            return
        super().keyPressEvent(evento)


def _menu_actions(barra, *, todas: bool = False) -> list[QAction]:
    """As ações com atalho dos menus (ou todas, com `todas`), inclusive dos submenus."""
    acoes = []
    for acao in barra.actions():
        if acao.menu() is not None:
            acoes += _menu_actions(acao.menu(), todas=todas)
        elif todas or not acao.shortcut().isEmpty():
            acoes.append(acao)
    return acoes


def save_error_text(erro: OSError) -> str:
    """Explica no idioma da interface por que a gravação falhou (RF-17); o detalhe vai embaixo."""
    if isinstance(erro, PermissionError):
        motivo = _("Sem permissão para gravar neste local.")
    elif isinstance(erro, IsADirectoryError):
        motivo = _("Já existe uma pasta com esse nome.")
    elif isinstance(erro, FileNotFoundError):
        motivo = _("A pasta de destino não existe.")
    else:
        motivo = _(_SAVE_ERRORS.get(erro.errno, N_("Ocorreu um erro ao gravar o arquivo.")))
    detalhe = erro.strerror or str(erro)
    return _("{motivo}\n\nDetalhe: {detalhe}").format(motivo=motivo, detalhe=detalhe)


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
        self._manual: ManualDialog | None = None

        # Zoom que se digita (como no Inkscape): Enter aplica, Esc volta ao valor atual
        self._zoom_field = _ZoomField("100%")
        self._zoom_field.setAlignment(Qt.AlignmentFlag.AlignRight)
        largura = self._zoom_field.fontMetrics().horizontalAdvance("88888%")
        self._zoom_field.setFixedWidth(largura + 12)
        self._zoom_field.setToolTip(_("Digite a porcentagem e tecle Enter"))
        self._zoom_field.returnPressed.connect(self._zoom_typed)
        self._zoom_field.editingFinished.connect(lambda: self._show_zoom(self.view.zoom))
        # Erros e avisos à esquerda, sempre à vista, e o clique abre o painel Mensagens
        # (como no VS Code); o resumo detalhado fica na dica
        self.issues_button = QToolButton()
        self.issues_button.setAutoRaise(True)
        self.issues_button.clicked.connect(self.show_messages)
        self._recommendation_label = QLabel()
        self._recommendation_label.setStyleSheet("font-weight: bold;")
        self._recommendation_label.hide()
        self.statusBar().addPermanentWidget(self._recommendation_label)  # mensagens não a cobrem
        self.statusBar().addPermanentWidget(self._zoom_field)
        self.view.zoom_changed.connect(self._show_zoom)
        self.view.message.connect(self.statusBar().showMessage)
        self.view.tool_changed.connect(self._tool_changed)
        self.view.shortcut_key.connect(self._shortcut_key)
        self.diagram_scene.selectionChanged.connect(self._selection_changed)
        self._build_docks()
        self.update_checker = UpdateChecker(self)  # aviso de versão nova (RF-22)
        self._build_menus()
        self._same_menus_everywhere()
        self._add_shortcut_actions()
        self.view.context_filler = self._fill_context_menu
        self._build_toolbar()
        self._quick_edit_button = QToolButton()  # indicador clicável na barra de status
        self._quick_edit_button.setDefaultAction(self.action_quick_edit)
        self._quick_edit_button.setAutoRaise(True)
        self.statusBar().insertPermanentWidget(0, self._quick_edit_button)
        self.statusBar().insertPermanentWidget(0, self.issues_button)
        self._quick_edit_toggled(self.action_quick_edit.isChecked())
        self._restore_layout()
        # Cópia de recuperação de tempos em tempos, fora do arquivo do usuário
        self.recovery = RecoveryCopy()
        self._recovery_failed = False
        self._recovery_timer = QTimer(self)
        self._recovery_timer.timeout.connect(self.save_recovery)
        self.apply_recovery_interval()
        self._attach(Document.new(), None)

    # --- menus e ferramentas -----------------------------------------------------------------

    def _action(self, texto: str, atalho, funcao) -> QAction:
        acao = QAction(texto, self)
        if atalho is not None:
            acao.setShortcut(atalho)
        acao.triggered.connect(funcao)
        return acao

    def _build_menus(self) -> None:
        arquivo = self.menuBar().addMenu(_("&Arquivo"))
        self.file_menu = arquivo
        self.action_new = self._action(
            _("&Novo"), QKeySequence.StandardKey.New, self.new_requested.emit
        )
        self.action_open = self._action(
            _("&Abrir..."), QKeySequence.StandardKey.Open, self.open_requested.emit
        )
        self.action_save = self._action(_("&Salvar"), QKeySequence.StandardKey.Save, self.save)
        self.action_save_as = self._action(
            _("Salvar &como..."), QKeySequence.StandardKey.SaveAs, self.save_as
        )
        # Atalhos fixos onde o padrão do Qt muda de um sistema para outro (e os manuais, gerados
        # sem tela, mostravam os do Windows): o primeiro é o que aparece no menu. No macOS, o
        # Qt troca Ctrl por Cmd sozinho.
        self.action_close = self._action(_("&Fechar"), None, self.close)
        self.action_close.setShortcuts([QKeySequence("Ctrl+W"), QKeySequence("Ctrl+F4")])
        self.action_quit = self._action(_("Sa&ir"), "Ctrl+Q", self._quit)
        arquivo.addActions([self.action_new, self.action_open])
        self.recent_menu = arquivo.addMenu(_("Abrir &recente"))
        self.recent_menu.aboutToShow.connect(self._fill_recent_menu)
        arquivo.addSeparator()
        arquivo.addActions([self.action_save, self.action_save_as])
        arquivo.addSeparator()
        self.action_export = self._action(_("Exportar &desenho..."), "Ctrl+E", self.export)
        self.action_copy_image = self._action(
            _("Copiar como ima&gem"), "Ctrl+Shift+C", self.copy_image
        )
        arquivo.addActions([self.action_export, self.action_copy_image])
        arquivo.addSeparator()
        arquivo.addActions([self.action_close, self.action_quit])

        editar = self.menuBar().addMenu(_("&Editar"))
        self.edit_menu = editar
        self.action_undo = self._action(_("&Desfazer"), QKeySequence.StandardKey.Undo, self._undo)
        self.action_redo = self._action(_("&Refazer"), None, self._redo)
        self.action_redo.setShortcuts([QKeySequence("Ctrl+Shift+Z"), QKeySequence("Ctrl+Y")])
        self.action_delete = self._action(
            # Só Del: no Linux o padrão do Qt inclui Ctrl+D, que é o Duplicar, e um atalho
            # repetido não faz nada
            _("E&xcluir"),
            "Del",
            self._delete,
        )
        editar.addActions([self.action_undo, self.action_redo])
        editar.addSeparator()
        self.action_cut = self._action(_("Recor&tar"), QKeySequence.StandardKey.Cut, self.cut)
        self.action_copy = self._action(_("&Copiar"), QKeySequence.StandardKey.Copy, self.copy)
        self.action_paste = self._action(_("C&olar"), QKeySequence.StandardKey.Paste, self.paste)
        self.action_duplicate = self._action(_("D&uplicar"), "Ctrl+D", self.duplicate)
        editar.addActions([self.action_cut, self.action_copy, self.action_paste])
        editar.addAction(self.action_duplicate)
        editar.addSeparator()
        editar.addAction(self.action_delete)
        editar.addSeparator()
        self.action_select_all = self._action(
            _("&Selecionar tudo"), QKeySequence.StandardKey.SelectAll, self._select_all
        )
        self.action_select_same = self._action(
            # Ctrl+Alt+A, como o "selecionar iguais" do Figma: Ctrl+Shift+A é Desmarcar tudo
            # na Apple e no KDE
            _("Selecionar do &mesmo tipo"),
            "Ctrl+Alt+A",
            self._select_same_kind,
        )
        self.action_deselect = self._action(
            _("D&esmarcar tudo"), "Ctrl+Shift+A", self.diagram_scene.clearSelection
        )
        editar.addActions([self.action_select_all, self.action_deselect, self.action_select_same])
        editar.addSeparator()
        self.action_find = self._action(
            _("&Localizar..."), QKeySequence.StandardKey.Find, self._find
        )
        editar.addAction(self.action_find)
        self.action_quick_edit = self._action(_("Edição rápid&a"), "Ctrl+Shift+E", lambda: None)
        self.action_quick_edit.setCheckable(True)
        self.action_quick_edit.setChecked(quick_edit_enabled())
        self.action_quick_edit.setStatusTip(
            _("Atalhos de uma tecla para as ferramentas ({teclas})").format(
                teclas=", ".join(tecla for tecla, _ferramentas in FAMILIES)  # nunca desatualiza
            )
        )
        self.action_quick_edit.toggled.connect(self._quick_edit_toggled)

        organizar = self.menuBar().addMenu(_("&Organizar"))  # e também no botão direito
        self.arrange_menu = organizar
        # Atalhos iguais nos três sistemas, sem colidir com a Apple nem com o KDE (2026-11-19):
        # Home e End, como no Inkscape (Fn+setas nos notebooks e no Mac), e uma combinação de
        # letras para teclados sem nenhum jeito de mandar Home e End. Só valem no desenho: num
        # campo de texto, Home e End continuam indo ao começo e ao fim da linha.
        self.action_front = self._action(_("&Trazer para a frente"), None, self._bring_to_front)
        self.action_front.setShortcuts([QKeySequence("Home"), QKeySequence("Ctrl+Alt+Shift+F")])
        self.action_back = self._action(_("&Enviar para trás"), None, self._send_to_back)
        self.action_back.setShortcuts([QKeySequence("End"), QKeySequence("Ctrl+Alt+Shift+B")])
        for acao in (self.action_front, self.action_back):
            acao.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            acao.setProperty("todos_os_atalhos", True)  # a lista do F1 mostra os dois
            self.view.addAction(acao)
        organizar.addActions([self.action_front, self.action_back])
        organizar.addSeparator()
        # Como no Keynote e no Pages: Ctrl+G e Ctrl+Shift+G são buscar o próximo e o anterior
        self.action_group = self._action(_("A&grupar"), "Ctrl+Alt+G", self.group)
        self.action_ungroup = self._action(_("&Desagrupar"), "Ctrl+Alt+Shift+G", self.ungroup)
        organizar.addActions([self.action_group, self.action_ungroup])
        organizar.addSeparator()
        alinhar = organizar.addMenu(_("&Alinhar"))
        self.align_menu = alinhar
        self.align_actions: dict[str, QAction] = {}
        for modo, texto in ALIGN_NAMES:
            acao = self._action(_(texto), None, lambda _x=False, m=modo: self._align(m))
            self.align_actions[modo] = acao
            alinhar.addAction(acao)
            if modo == "right":
                alinhar.addSeparator()

        exibir = self.menuBar().addMenu(_("E&xibir"))
        self.view_menu = exibir
        self.action_zoom_in = self._action(
            _("&Ampliar"), QKeySequence.StandardKey.ZoomIn, self.view.zoom_in
        )
        self.action_zoom_out = self._action(
            _("&Reduzir"), QKeySequence.StandardKey.ZoomOut, self.view.zoom_out
        )
        self.action_zoom_actual = self._action(_("&Tamanho real"), "Ctrl+0", self.view.zoom_actual)
        self.action_zoom_fit = self._action(_("A&justar à janela"), "Ctrl+9", self.view.zoom_fit)
        exibir.addActions(
            [
                self.action_zoom_in,
                self.action_zoom_out,
                self.action_zoom_actual,
                self.action_zoom_fit,
            ]
        )
        self.action_validate = QAction(_("&Verificar modelo"), self)
        self.action_validate.setCheckable(True)
        self.action_validate.setChecked(True)
        self.action_validate.toggled.connect(self._refresh_issues)
        self.action_structure = QAction(_("Avisos de &estrutura"), self)
        self.action_structure.setCheckable(True)
        self.action_structure.setChecked(structure_warnings_enabled())
        self.action_structure.setToolTip(
            _(
                "Laranja: o que a teoria do modelo ER pede além das ligações (entidade sem chave,"
                " relacionamento com um participante só...)"
            )
        )
        self.action_structure.toggled.connect(self._structure_toggled)
        self.action_grid = QAction(_("&Grade"), self)
        self.action_grid.setShortcut("Ctrl+'")
        self.action_grid.setCheckable(True)
        self.action_grid.toggled.connect(self.view.set_grid)
        self.extra_menus: list[QMenu] = []  # menus fora da barra, para os atalhos e o F1
        temas = QActionGroup(self)
        self.theme_actions: dict[str, QAction] = {}
        for opcao in available_themes():
            nome = opcao.name
            acao = QAction(_(opcao.label), self, checkable=True)
            acao.setChecked(nome == current_theme().name)
            # o tema do sistema é relido na hora: o usuário pode tê-lo trocado
            acao.triggered.connect(
                lambda _=False, n=nome: apply_theme(theme_named(n) or current_theme())
            )
            temas.addAction(acao)
            self.theme_actions[nome] = acao
        theme_manager().changed.connect(self._theme_changed)
        idiomas = QActionGroup(self)
        self.language_actions: dict[str, QAction] = {}
        escolhido = saved_language() or language()
        for codigo, nome in LANGUAGES.items():
            acao = QAction(nome, self, checkable=True)  # cada idioma com o próprio nome
            acao.setChecked(codigo == escolhido)
            acao.triggered.connect(lambda _x=False, c=codigo: self._language_chosen(c))
            idiomas.addAction(acao)
            self.language_actions[codigo] = acao
        exibir.addSeparator()
        exibir.addActions(
            [
                self.inspector_dock.toggleViewAction(),
                self.properties_dock.toggleViewAction(),
                self.messages_dock.toggleViewAction(),
            ]
        )
        # A grade mostra ou esconde parte da vista: fica em Exibir e nas Preferências (Apple)
        exibir.insertAction(self.inspector_dock.toggleViewAction(), self.action_grid)
        exibir.insertSeparator(self.inspector_dock.toggleViewAction())
        exibir.addSeparator()
        # O Qt só tem o atalho padrão de tela cheia em alguns sistemas (no Linux, nenhum): F11
        tela_cheia = QKeySequence.StandardKey.FullScreen
        self.action_full_screen = self._action(
            _("Tela c&heia"),
            tela_cheia if QKeySequence.keyBindings(tela_cheia) else "F11",
            self._toggle_full_screen,
        )
        self.action_full_screen.setCheckable(True)
        exibir.addAction(self.action_full_screen)

        # Configurações antes de Ajuda, como o menu padrão do KDE: o tema (o "esquema de
        # cores" do Kate e do Okular), as barras que se mostram e as Preferências ("Configurar
        # o aplicativo"). No macOS, o Qt leva as Preferências para o menu do app (Apple).
        configuracoes = self.menuBar().addMenu(_("&Configurações"))
        self.settings_menu = configuracoes
        tema_menu = configuracoes.addMenu(_("&Tema"))
        tema_menu.addActions(list(self.theme_actions.values()))
        configuracoes.addSeparator()
        self.action_show_tools = QAction(_("Mostrar &faixa de ferramentas"), self)
        self.action_show_tools.setCheckable(True)
        self.action_show_tools.setChecked(True)
        self.action_show_tools.toggled.connect(lambda ligado: self.tool_bar.setVisible(ligado))
        self.action_show_status = QAction(_("Mostrar &barra de status"), self)
        self.action_show_status.setCheckable(True)
        self.action_show_status.setChecked(status_bar_enabled())
        self.action_show_status.toggled.connect(self._status_bar_toggled)
        configuracoes.addActions([self.action_show_tools, self.action_show_status])
        configuracoes.addSeparator()
        # Usados durante o trabalho: ficam no menu, e não na janela (Apple, Settings)
        configuracoes.addActions(
            [self.action_validate, self.action_structure, self.action_quick_edit]
        )
        configuracoes.addSeparator()
        self.action_preferences = self._action(_("&Preferências…"), "Ctrl+,", self.show_preferences)
        configuracoes.addAction(self.action_preferences)

        ajuda = self.menuBar().addMenu(_("Aj&uda"))
        self.help_menu = ajuda
        # Como no menu Ajuda padrão do KDE: o manual primeiro, com F1
        self.manual_action = self._action(
            _("&Manual do HaradaER"), QKeySequence.StandardKey.HelpContents, self.open_manual
        )
        self.shortcuts_action = self._action(_("Atalhos do &teclado…"), None, self.show_shortcuts)
        ajuda.addActions([self.manual_action, self.shortcuts_action])
        ajuda.addSeparator()
        self.report_action = ajuda.addAction(_("&Relatar um problema…"))
        self.report_action.triggered.connect(lambda: self._open_issue("bug"))
        self.suggest_action = ajuda.addAction(_("&Sugerir uma melhoria…"))
        self.suggest_action.triggered.connect(lambda: self._open_issue("melhoria"))
        ajuda.addSeparator()
        # Como no menu Ajuda padrão do KDE; abre as Preferências, onde está o idioma
        self.language_action = ajuda.addAction(_("Trocar o &idioma…"))
        self.language_action.triggered.connect(lambda: self.show_preferences())
        self.about_action = ajuda.addAction(_("S&obre o HaradaER"))
        self.about_action.triggered.connect(self.show_about)
        self.check_updates_action = QAction(_("Verificar &atualizações…"), self)  # Preferências
        self.check_updates_action.triggered.connect(lambda: self.update_checker.check(manual=True))
        self.auto_updates_action = QAction(_("Verificar ao a&brir"), self)
        self.auto_updates_action.setCheckable(True)
        self.auto_updates_action.setChecked(update_check_enabled())
        self.auto_updates_action.toggled.connect(set_update_check_enabled)

    def _toggle_full_screen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def changeEvent(self, event) -> None:  # noqa: N802 (nome do Qt)
        if event.type() == QEvent.Type.WindowStateChange:
            self.action_full_screen.setChecked(self.isFullScreen())  # também se saiu pelo sistema
        super().changeEvent(event)

    def show_about(self) -> QMessageBox:
        """Ajuda › Sobre o HaradaER: versão, licença e repositório, só com texto."""
        caixa = QMessageBox(self)
        caixa.setWindowTitle(_("Sobre o HaradaER"))
        caixa.setIcon(QMessageBox.Icon.NoIcon)
        caixa.setTextFormat(Qt.TextFormat.RichText)
        caixa.setText(f"<b>{TITLE} {haradaer.__version__}</b>")
        caixa.setInformativeText(
            _("Ferramenta de modelagem Entidade-Relacionamento compatível com o TerraER 3.14.")
            + "<br><br>"
            + _("Software livre, sob a licença GNU GPL versão 3.")
            + f'<br><a href="{REPOSITORIO}">{REPOSITORIO}</a>'
        )
        caixa.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        caixa.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        caixa.open()
        return caixa

    def _same_menus_everywhere(self) -> None:
        """A interface é igual nos três sistemas (decisão do autor): no macOS o Qt não leva
        Preferências, Sobre e Sair para o menu do app, e cada item fica no seu menu."""
        for acao in _menu_actions(self.menuBar(), todas=True):
            acao.setMenuRole(QAction.MenuRole.NoRole)

    def _add_shortcut_actions(self) -> None:
        """As ações das opções que só estão nas Preferências também entram na janela, para os
        atalhos valerem sem estarem na barra."""
        for menu in self.extra_menus:
            self.addActions(_menu_actions(menu))

    def _fill_context_menu(self, menu: QMenu) -> None:
        """As ações sobre a seleção no botão direito, depois do que o desenho já pôs (trocar
        tipo, vértices). São cópias das ações da janela, com o atalho escrito ao lado; ficam
        cinza quando não se aplicam, sem desligar as originais (e os atalhos delas)."""
        selecao = self.diagram_scene.selected_figures()
        tem = bool(selecao)
        varios = len(selecao) > 1

        def copia(acao: QAction, ligada: bool = True, onde: QMenu = menu) -> None:
            texto = acao.text()
            atalho = acao.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
            nova = onde.addAction(f"{texto}\t{atalho}" if atalho else texto)
            nova.setEnabled(ligada)
            nova.triggered.connect(acao.trigger)

        if not menu.isEmpty():
            menu.addSeparator()
        for acao in (self.action_cut, self.action_copy):
            copia(acao, tem)
        copia(self.action_paste)
        copia(self.action_duplicate, tem)
        copia(self.action_delete, tem)
        menu.addSeparator()
        if not tem:
            copia(self.action_select_all)
            return
        copia(self.action_front)
        copia(self.action_back)
        menu.addSeparator()
        copia(self.action_group, varios)
        copia(self.action_ungroup, any(f.tag == "g" for f in selecao))
        alinhar = menu.addMenu(self.align_menu.title())
        alinhar.setEnabled(varios)
        for modo, _texto in ALIGN_NAMES:
            copia(self.align_actions[modo], onde=alinhar)
            if modo == "right":
                alinhar.addSeparator()

    def _status_bar_toggled(self, ligado: bool) -> None:
        self.statusBar().setVisible(ligado)
        set_status_bar_enabled(ligado)

    def show_preferences(self) -> PreferencesDialog:
        dialogo = PreferencesDialog(self)
        dialogo.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialogo.show()
        return dialogo

    def _build_docks(self) -> None:
        """Painéis acopláveis à direita do desenho (RNF-09)."""
        self.inspector = ObjectInspector()
        self.inspector.selection_requested.connect(self._select_from_inspector)
        self.inspector.locate_requested.connect(self.locate)
        self.inspector_dock = QDockWidget(_("Inspetor de objetos"), self)
        self.inspector_dock.setObjectName("inspetor")
        self.inspector_dock.setWidget(self.inspector)
        self.properties = PropertiesPanel()
        self.properties_dock = QDockWidget(_("Propriedades"), self)
        self.properties_dock.setObjectName("propriedades")
        self.properties_dock.setWidget(self.properties)
        for dock in (self.inspector_dock, self.properties_dock):
            dock.setMinimumWidth(DOCK_MIN_WIDTH)  # sem isso os nomes ficavam cortados
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.messages = MessagesPanel()
        self.messages.locate_requested.connect(self.locate)
        self.messages_dock = QDockWidget(_("Mensagens"), self)
        self.messages_dock.setObjectName("mensagens")
        self.messages_dock.setWidget(self.messages)
        self.messages_dock.setMinimumWidth(DOCK_MIN_WIDTH)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.messages_dock)
        # Padrão: os três em abas à direita, nesta ordem, com o inspetor à frente. A disposição
        # que o usuário escolher depois é lembrada e vale por cima desta.
        self.tabifyDockWidget(self.properties_dock, self.messages_dock)
        self.tabifyDockWidget(self.messages_dock, self.inspector_dock)
        self.inspector_dock.raise_()

    def _build_toolbar(self) -> None:
        """Uma faixa no alto com todas as ferramentas, que rola na horizontal (`ToolStrip`).

        Fica dentro de uma barra fixa, com nome novo: uma disposição de janela salva antes não
        consegue mudá-la de lugar nem quebrá-la em duas linhas.
        """
        barra = QToolBar(_("Ferramentas"), self)
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
                icone, curto = select_icon(), _("Selecionar")
            elif tool.kind == "create":
                icone, curto = element_icon(tool.tag), _(SHORT_NAMES[tool.tag])
            else:
                icone, curto = connection_icon(tool.tag), _(SHORT_NAMES[tool.tag])
            acao = QAction(icone, curto, self)
            acao.setToolTip(_(texto))
            acao.setStatusTip(_(texto))
            acao.setCheckable(True)
            acao.triggered.connect(lambda _=False, t=tool: self._tool_clicked(t))
            grupo.addAction(acao)
            self.tool_strip.add_action(acao)
            self._tool_actions[tool] = acao

        adicionar(SELECT, N_("Selecionar"))
        self.tool_strip.add_separator()
        for tag, nome in ELEMENTS:
            adicionar(Tool("create", tag), nome)
        self.tool_strip.add_separator()
        for tag, nome in CONNECTIONS:
            adicionar(Tool("connect", tag), nome)
        self.tool_strip.add_separator()
        for tag, nome in TEXTS:
            adicionar(Tool("create", tag), nome)
        self.tool_strip.finish()
        self._tool_actions[SELECT].setChecked(True)

    def _theme_changed(self, tema) -> None:
        """Marca o tema no menu e redesenha os ícones da faixa (as linhas seguem o tema)."""
        if tema.name in self.theme_actions:
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
        if tool.kind == "connect":
            self.statusBar().showMessage(
                _("Liga: {pares}").format(pares=pairs_text(recommend_elements(tool.tag)))
            )
        else:
            self.statusBar().clearMessage()

    # --- recomendação (RF-10) ----------------------------------------------------------------

    def _selected_pair(self) -> tuple[NodeFigure, NodeFigure] | None:
        figuras = self.diagram_scene.selected_figures()
        if len(figuras) == 2 and all(isinstance(f, NodeFigure) for f in figuras):
            return figuras[0], figuras[1]
        return None

    def _update_recommendation(self) -> None:
        """Com dois elementos selecionados, destaca na faixa as conexões aceitas entre eles,
        apaga as outras e diz quais são na barra de status (fica enquanto o par estiver
        selecionado, sem ser apagado por outras mensagens)."""
        par = self._selected_pair()
        validos = set() if par is None else self._valid_for(*par)
        conexoes = {t: a for t, a in self._tool_actions.items() if t.kind == "connect"}
        self.tool_strip.set_recommendation(
            list(conexoes.values()),
            None if par is None else {a for t, a in conexoes.items() if t.tag in validos},
        )
        if par is None:
            self._recommendation_label.clear()
            self._recommendation_label.hide()
            return
        a, b = (name_of(f.tag) for f in par)
        if validos:
            # os nomes escritos nos botões, para achá-los na faixa
            nomes = ", ".join(_(SHORT_NAMES[t]) for t in RECOMMENDATION_ORDER if t in validos)
            texto = _("Conexões aceitas entre {a} e {b}: {nomes}").format(a=a, b=b, nomes=nomes)
        else:
            texto = _("Nenhuma conexão aceita entre {a} e {b}").format(a=a, b=b)
        self._recommendation_label.setText(texto)
        self._recommendation_label.show()

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
                self, _("Não foi possível abrir o arquivo"), f"{caminho.name}\n\n{erro}"
            )
            return False
        livres = remove_free_connections(documento)  # RF-25: antes de mostrar o modelo
        textos = convert_free_texts(documento, QtMeasurer())  # RF-27
        self._attach(documento, caminho)
        self.recent.add(caminho)
        if livres or textos:
            self._editor.history.mark_dirty()
        if livres:
            self._report_free_connections(livres)
        if textos:
            self._report_converted_texts(textos)
        self._fix_invalid_attribute_types()
        self.view.zoom_actual()
        self.view.horizontalScrollBar().setValue(self.view.horizontalScrollBar().minimum())
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().minimum())
        return True

    def _report_free_connections(self, pontas: list[tuple[Element | None, Element | None]]) -> None:
        """RF-25: as conexões livres já foram apagadas; o aviso diz quantas e entre o quê."""

        def ponta(figura: Element | None) -> str:
            if figura is None:
                return _("ponta solta")
            return f"{display_name(figura)} ({name_of(figura.tag)})"

        linhas = [f"• {ponta(a)} ↔ {ponta(b)}" for a, b in pontas[:10]]
        if len(pontas) > 10:
            linhas.append(_("... e mais {n}").format(n=len(pontas) - 10))
        QMessageBox.information(
            self,
            _("Conexões livres apagadas"),
            (
                _(
                    "O HaradaER não usa a conexão livre, que não tem significado no modelo ER."
                    " Foi apagada 1 deste arquivo, entre:"
                )
                if len(pontas) == 1
                else _(
                    "O HaradaER não usa a conexão livre, que não tem significado no modelo ER."
                    " Foram apagadas {n} deste arquivo, entre:"
                ).format(n=len(pontas))
            )
            + "\n\n"
            + "\n".join(linhas)
            + "\n\n"
            + _("O arquivo em disco só muda quando você salvar."),
        )

    def _report_converted_texts(self, textos: list[tuple[str, str]]) -> None:
        """RF-27: os textos soltos do TerraER já viraram Texto; o aviso diz quantos e quais."""
        origem = {"t": N_("texto"), "tn": N_("texto em negrito"), "ti": N_("papel")}

        def linha(tag: str, texto: str) -> str:
            resumo = " ".join(texto.split())
            if len(resumo) > 40:
                resumo = resumo[:39] + "…"
            return f"• “{resumo}” ({_(origem[tag])})"

        linhas = [linha(tag, texto) for tag, texto in textos[:10]]
        if len(textos) > 10:
            linhas.append(_("... e mais {n}").format(n=len(textos) - 10))
        QMessageBox.information(
            self,
            _("Textos convertidos"),
            (
                _(
                    "O HaradaER tem um só tipo de texto, o Texto (a Área de Texto do TerraER)."
                    " 1 texto deste arquivo virou Texto, no mesmo lugar e com a mesma fonte:"
                )
                if len(textos) == 1
                else _(
                    "O HaradaER tem um só tipo de texto, o Texto (a Área de Texto do TerraER)."
                    " {n} textos deste arquivo viraram Texto, no mesmo lugar e com a mesma fonte:"
                ).format(n=len(textos))
            )
            + "\n\n"
            + "\n".join(linhas)
            + "\n\n"
            + _("O arquivo em disco só muda quando você salvar."),
        )

    def _fix_invalid_attribute_types(self) -> None:
        """RNF-16: tipo de atributo inválido vira o tipo padrão, com aviso (o TerraER abriria o
        arquivo, mas falharia ao salvar). A troca fica no histórico e pode ser desfeita."""
        invalidos = invalid_attribute_types(self._editor.document)
        if not invalidos:
            return
        linhas = [f"• {no.name or _('(sem nome)')}: {no.attribute_type}" for no in invalidos[:10]]
        if len(invalidos) > 10:
            linhas.append(_("... e mais {n}").format(n=len(invalidos) - 10))
        self._editor.history.execute(fix_attribute_types_command(self._editor.document))
        QMessageBox.warning(
            self,
            _("Tipos de atributo inválidos"),
            _(
                "Estes atributos tinham um tipo que o TerraER não reconhece e passaram a usar o"
                " tipo padrão. O TerraER abriria o arquivo, mas não conseguiria salvá-lo."
            )
            + "\n\n"
            + "\n".join(linhas),
        )

    def restore(self, sobra: Leftover) -> bool:
        """Abre uma cópia de recuperação que sobrou, como modelo alterado e ainda não salvo:
        o arquivo original só muda quando o usuário salvar."""
        try:
            documento = io.load(sobra.copy)
        except (ArquivoInvalidoError, OSError) as erro:
            QMessageBox.critical(
                self, _("Não foi possível recuperar o modelo"), f"{sobra.copy.name}\n\n{erro}"
            )
            return False
        self._attach(documento, sobra.original)
        self._editor.history.mark_dirty()
        self.save_recovery()  # a cópia passa a ser desta janela antes de apagar a antiga
        sobra.discard()
        return True

    def apply_recovery_interval(self) -> None:
        """Segue o intervalo das Preferências; 0 desliga a cópia de recuperação."""
        minutos = recovery_interval()
        if minutos:
            self._recovery_timer.start(minutos * 60_000)
        else:
            self._recovery_timer.stop()

    def save_recovery(self) -> None:
        """Grava a cópia de recuperação se houver alteração não salva."""
        minutos = recovery_interval()
        ativo = self._recovery_timer.isActive()
        if (ativo and self._recovery_timer.interval()) != minutos * 60_000:
            self.apply_recovery_interval()  # mudado nas Preferências de outra janela
        if not minutos or not self._editor.history.is_dirty:
            return
        try:
            self.recovery.write(self._editor.document, self.path)
        except OSError as erro:
            if not self._recovery_failed:  # avisa uma vez só, na barra de status
                self._recovery_failed = True
                self.statusBar().showMessage(
                    _("Não foi possível gravar a cópia de recuperação: {erro}").format(
                        erro=erro.strerror or erro
                    ),
                    8000,
                )
            return
        self._recovery_failed = False

    def save(self) -> bool:
        """Grava no arquivo atual (ou pergunta onde). Devolve `False` se não gravou."""
        if self.path is None:
            return self.save_as()
        return self._write(self.path)

    def save_as(self) -> bool:
        inicial = str(self.path) if self.path else f"{_(UNTITLED)}.xml"
        nome, _filtro = QFileDialog.getSaveFileName(
            self, _("Salvar modelo"), inicial, _("Modelos do TerraER (*.xml)")
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
                _("Não foi possível salvar o arquivo"),
                f"{caminho.name}\n\n{save_error_text(erro)}",
            )
            return False
        self.path = caminho.resolve()
        self.recent.add(self.path)
        self._editor.history.mark_clean()
        self.statusBar().showMessage(_("Salvo em {caminho}").format(caminho=caminho), 4000)
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
            vazio = self.recent_menu.addAction(_("Nenhum arquivo recente"))
            vazio.setEnabled(False)
            return
        self.recent_menu.addSeparator()
        self.recent_menu.addAction(_("&Limpar lista"), self.recent.clear)

    def open_recent(self, caminho: Path) -> None:
        if not caminho.is_file():
            self.recent.remove(caminho)
            QMessageBox.critical(
                self,
                _("Não foi possível abrir o arquivo"),
                f"{caminho}\n\n" + _("O arquivo não existe mais."),
            )
            return
        self.open_path_requested.emit(caminho)

    def export(self) -> bool:
        """Pergunta onde e grava o desenho como imagem, SVG ou PDF (RF-11)."""
        filtros = ";;".join(
            f"{_(nome)} (*.{ext}{' *.jpeg' if ext == 'jpg' else ''})"
            for ext, nome in EXPORT_FORMATS
        )
        base = self.path.with_suffix(".png") if self.path else Path(f"{_(UNTITLED)}.png")
        nome, filtro = QFileDialog.getSaveFileName(self, _("Exportar desenho"), str(base), filtros)
        if not nome:
            return False
        caminho = Path(nome)
        extensoes = {f".{ext}" for ext, _ in EXPORT_FORMATS} | {".jpeg"}
        if caminho.suffix.lower() not in extensoes:
            escolhida = next(
                (ext for ext, rotulo in EXPORT_FORMATS if filtro.startswith(_(rotulo))), "png"
            )
            caminho = caminho.with_name(f"{caminho.name}.{escolhida}")
        try:
            export_diagram(
                self.diagram_scene, caminho, self.path.stem if self.path else _(UNTITLED)
            )
        except EmptyDiagramError:
            QMessageBox.information(self, _("Exportar desenho"), _("O desenho está vazio."))
            return False
        except OSError as erro:
            QMessageBox.critical(
                self,
                _("Não foi possível exportar o desenho"),
                f"{caminho.name}\n\n{save_error_text(erro)}",
            )
            return False
        self.statusBar().showMessage(_("Exportado para {caminho}").format(caminho=caminho), 4000)
        return True

    def copy_image(self) -> bool:
        try:
            imagem = render_image(self.diagram_scene)
        except EmptyDiagramError:
            self.statusBar().showMessage(_("O desenho está vazio."), 4000)
            return False
        QApplication.clipboard().setImage(imagem)
        self.statusBar().showMessage(_("Desenho copiado como imagem."), 4000)
        return True

    def _restore_layout(self) -> None:
        """Volta o tamanho da janela e a posição dos painéis da última sessão (RNF-09)."""
        geometria, estado = window_layout()
        if geometria is not None:
            self.restoreGeometry(geometria)
        if estado is not None:
            self.restoreState(estado)
        self.action_show_tools.setChecked(not self.tool_bar.isHidden())
        self.statusBar().setVisible(self.action_show_status.isChecked())

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
            self.statusBar().showMessage(_("Nada para copiar."), 3000)
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
            self.statusBar().showMessage(_("A área de transferência não tem um modelo."), 3000)
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
        self.action_undo.setText(f"{_('&Desfazer')} {_(historico.undo_label)}".rstrip())
        self.action_redo.setText(f"{_('&Refazer')} {_(historico.redo_label)}".rstrip())
        self._update_title()
        if not historico.is_dirty and self.recovery.exists:
            self.recovery.remove()  # salvo: a cópia não serve mais
        self._refresh_issues()
        self.inspector.refresh(self._editor.document)
        self._selection_changed()

    def _refresh_issues(self) -> None:
        """Refaz a verificação do modelo inteiro; os diagramas de ER são pequenos."""
        documento = self._editor.document
        ligada = self.action_validate.isChecked()
        problemas = validate(documento) if ligada else []
        com_avisos = ligada and self.action_structure.isChecked()
        avisos = check_structure(documento) if com_avisos else []
        self.diagram_scene.show_issues(problemas)
        self.diagram_scene.show_warnings(avisos)
        self.messages.show_messages(problemas, avisos, ligada)
        self._show_issue_counts(ligada, problemas, avisos)

    def _show_issue_counts(self, ligada: bool, problemas: list, avisos: list) -> None:
        botao = self.issues_button
        if not ligada:
            botao.setText(_("Verificação desligada"))
            botao.setToolTip(_(OFF_TEXT))
            cor = None
        else:
            erros = issue_count(len(problemas), N_("erro"), N_("erros"))
            alertas = issue_count(len(avisos), N_("aviso"), N_("avisos"))
            botao.setText(f"{erros}  {alertas}")
            botao.setToolTip(
                summary_text(problemas, avisos, display_name) or _("Nenhum problema no modelo.")
            )
            cor = INVALID_COLOR if problemas else WARNING_COLOR if avisos else None
        botao.setStyleSheet(f"color: {cor.name()};" if cor is not None else "")

    def show_messages(self) -> None:
        """Traz o painel Mensagens para a frente, mesmo atrás de outra aba ou fechado."""
        self.messages_dock.show()
        self.messages_dock.raise_()

    def _language_chosen(self, codigo: str) -> None:
        """Guarda o idioma para a próxima vez que o programa abrir (RNF-06) e avisa, já no
        idioma escolhido, que é preciso reabrir. As janelas abertas continuam como estão."""
        anterior = saved_language() or language()
        set_saved_language(codigo)
        for c, acao in self.language_actions.items():
            acao.setChecked(c == codigo)
        if codigo == anterior:
            return
        QMessageBox.information(
            self,
            translate(N_("Idioma"), codigo),
            translate(N_("O idioma muda quando o HaradaER for fechado e aberto de novo."), codigo),
        )

    def open_manual(self) -> ManualDialog | None:
        """Ajuda › Manual: o manual instalado, numa janela (KDE e Apple). Sem ele no pacote,
        abre o do repositório no navegador; sem navegador, mostra o endereço para copiar."""
        if manual_path(language()) is not None:
            if self._manual is None:
                self._manual = ManualDialog(self, language())
            self._manual.show()
            self._manual.raise_()
            self._manual.activateWindow()
            return self._manual
        url = f"{REPOSITORIO}/blob/main/{MANUALS[language()]}"
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.information(
                self,
                _("Abrir no navegador"),
                _("Não foi possível abrir o navegador. Copie este endereço:") + f"\n\n{url}",
            )
        return None

    def _open_issue(self, tipo: Tipo) -> None:
        """Abre no navegador a issue já preenchida (RF-21). Sem navegador, mostra o endereço."""
        url = issue_url(tipo, haradaer.__version__, system_description(), language())
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.information(
                self,
                _("Abrir no navegador"),
                _("Não foi possível abrir o navegador. Copie este endereço:") + f"\n\n{url}",
            )

    def show_shortcuts(self) -> ShortcutsDialog:
        dialogo = ShortcutsDialog(
            self,
            self.menuBar(),
            lambda t: self._tool_actions[t].statusTip(),
            self.extra_menus,
        )
        dialogo.show()
        return dialogo

    # --- Edição rápida ------------------------------------------------------------------------

    def _quick_edit_toggled(self, ligado: bool) -> None:
        set_quick_edit_enabled(ligado)  # lembrado para as próximas janelas e sessões
        self.view.quick_edit = ligado
        for tool, acao in self._tool_actions.items():
            tecla = key_of(tool)
            dica = acao.statusTip()
            acao.setToolTip(f"{dica} ({tecla})" if ligado and tecla else dica)

    def _shortcut_key(self, tecla: str, voltar: bool) -> None:
        """Uma letra da Edição rápida: escolhe a ferramenta, ou age sobre a seleção."""
        atual = self.view.tool
        figuras = self.diagram_scene.selected_figures()
        if atual == SELECT and len(figuras) == 1 and isinstance(figuras[0], NodeFigure):
            no = figuras[0]
            familia = node_type_family(no.tag)
            if len(familia) > 1 and key_of(Tool("create", no.tag)) == tecla.upper():
                passo = -1 if voltar else 1  # a letra da família troca o tipo do selecionado
                tag = familia[(familia.index(no.tag) + passo) % len(familia)]
                self.view.change_type(no, tag)
                if no.tag == tag:
                    indice = familia.index(tag) + 1
                    self.statusBar().showMessage(
                        f"{_(KINDS[tag].label)}  ({tecla.upper()}: {indice}/{len(familia)})", 4000
                    )
                return
        tool = next_tool(tecla, atual, voltar=voltar)
        if tool is None:
            return
        nova_familia = key_of(atual) != tecla.upper()
        par = self._selected_pair()
        if tool.kind == "connect" and nova_familia and par is not None:
            if tool.tag in self._valid_for(*par):
                self._tool_clicked(tool)  # liga os dois na hora
                return
            self.view.set_tool(tool)
            a, b = (name_of(f.tag) for f in par)
            self.statusBar().showMessage(
                _("{conexao} não liga {a} e {b}.").format(
                    conexao=self._tool_actions[tool].statusTip(), a=a, b=b
                ),
                5000,
            )
            return
        if (
            tecla.upper() == "A"
            and nova_familia
            and len(figuras) == 1
            and isinstance(figuras[0], NodeFigure)
            and not figuras[0].tag.startswith("atr")
            and is_valid_connection("lcaf", "atr", figuras[0].tag)
        ):
            self.view.create_attached("atr", figuras[0])
            return
        self.view.set_tool(tool)
        indice, total = position(tool)
        texto = self._tool_actions[tool].statusTip()
        if total > 1:
            texto += f"  ({tecla.upper()}: {indice}/{total})"
        self.statusBar().showMessage(texto, 4000)

    def _structure_toggled(self, ligado: bool) -> None:
        set_structure_warnings_enabled(ligado)  # lembrado para as próximas janelas e sessões
        self._refresh_issues()

    def _update_title(self) -> None:
        nome = self.path.name if self.path else _(UNTITLED)
        self.setWindowTitle(f"{nome}[*] - {TITLE}")
        self.setWindowModified(self._editor.history.is_dirty)

    def _show_zoom(self, zoom: float) -> None:
        if not self._zoom_field.hasFocus():
            self._zoom_field.setText(f"{round(zoom * 100)}%")

    def _zoom_typed(self) -> None:
        """Aplica a porcentagem digitada (137, 137% ou 137,5); um texto inválido volta ao atual."""
        texto = self._zoom_field.text().replace("%", "").replace(",", ".").strip()
        try:
            valor = float(texto)
        except ValueError:
            valor = None
        if valor is not None and valor > 0:
            self.view.set_zoom(valor / 100)
        self._zoom_field.clearFocus()
        self._show_zoom(self.view.zoom)
        self.view.setFocus()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._editor.history.is_dirty and not self._confirm_discard():
            event.ignore()
            return
        self._recovery_timer.stop()
        self.recovery.remove()  # salvo ou descartado: nada a recuperar
        save_window_layout(self.saveGeometry(), self.saveState())
        self.closed.emit(self)
        super().closeEvent(event)

    def _confirm_discard(self) -> bool:
        """Pergunta o que fazer com as alterações. `False` cancela o fechamento."""
        botoes = QMessageBox.StandardButton
        resposta = QMessageBox.question(
            self,
            TITLE,
            _("Salvar as alterações em {nome}?").format(
                nome=self.path.name if self.path else _(UNTITLED)
            ),
            botoes.Save | botoes.Discard | botoes.Cancel,
            botoes.Save,
        )
        if resposta == botoes.Save:
            return self.save()
        return resposta == botoes.Discard
