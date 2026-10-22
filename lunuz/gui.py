#!/usr/bin/env python3
"""lunuz tools - interface gráfica inspirada na LinuxToys.

Layout: header com busca + título central + modos de visualização,
grade de categorias com ícones quadrados coloridos, lista de itens
por categoria, terminal VTE embutido e rodapé com links.
"""

import sys
import os
import tempfile

try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Vte", "2.91")
    from gi.repository import Gtk, Gdk, GLib, Vte, Gio, Pango, GdkPixbuf
except Exception as e:  # pragma: no cover
    print(f"lunuz gui: GTK3/VTE nao disponivel: {e}", file=sys.stderr)
    print("Instale: sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91", file=sys.stderr)
    sys.exit(1)

from .actions import (CATEGORIES, all_items, detect_distro, item_icon,
                       item_available, available_families, FAMILY_NAMES)


def _which(name):
    """Procura um executavel no PATH."""
    import shutil
    return shutil.which(name)


# ------------------------------------------------------------------
# Ícones coloridos das seções (estilo LinuxToys) - scripts/icons/*.svg
# ------------------------------------------------------------------
ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")


def section_icon(cat, size=54):
    """Ícone colorido da seção (PNG). Retorna Gtk.Image ou None se ausente."""
    path = os.path.join(ICONS_DIR, f"sec-{cat.get('id', '')}.png")
    if not os.path.exists(path):
        return None
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)
        img = Gtk.Image.new_from_pixbuf(pb)
        img.set_valign(Gtk.Align.CENTER)
        return img
    except Exception:
        return None


def item_icon_image(item, size=36):
    """Ícone colorido do item (PNG de marca ou genérico, estilo LinuxToys)."""
    path = os.path.join(ICONS_DIR, f"item-{item.get('id', '')}.png")
    if not os.path.exists(path):
        return None
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)
        img = Gtk.Image.new_from_pixbuf(pb)
        img.set_valign(Gtk.Align.CENTER)
        return img
    except Exception:
        return None


def distro_icon(info, size=30):
    """Logo da distro (PNG estilizado): tenta o ID, depois a família, depois '?'."""
    for key in (info.get("id", ""), info.get("family", ""), "unknown"):
        path = os.path.join(ICONS_DIR, f"distro-{key}.png")
        if os.path.exists(path):
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)
                img = Gtk.Image.new_from_pixbuf(pb)
                img.set_valign(Gtk.Align.CENTER)
                return img
            except Exception:
                pass
    return None


# ------------------------------------------------------------------
# CSS global (tiles estilo LinuxToys)
# ------------------------------------------------------------------
def _build_css():
    css = """
tile {
    background-color: #26262e;
    border: 1px solid #3a3a44;
    border-radius: 14px;
    padding: 8px;
    min-height: 56px;
}
tile:hover { background-color: #31313c; }
tile:focus { outline-color: rgba(0,0,0,0); }

sq {
    border-radius: 12px;
    min-width: 52px;
    min-height: 52px;
}
sq-sm {
    border-radius: 9px;
    min-width: 36px;
    min-height: 36px;
}
.itemrow {
    background-color: #26262e;
    border: 1px solid #33333d;
    border-radius: 10px;
    padding: 6px;
}
.itemrow:hover { background-color: #31313c; }
.itemrow.sel { background-color: #17331f; border: 1px solid #3db96e; }
.itemrow.man { opacity: 0.72; }
.itemrow.unavail { opacity: 0.55; }
.badgelbl { color: #e5a535; font-size: 0.9em; }
.chip {
    background-color: #26262e;
    border: 1px solid #3a3a44;
    border-radius: 12px;
    padding: 8px 14px;
}
.termbox { background-color: #14141a; }
.footer { color: #9a9aa8; }
.white { color: #ffffff; }
"""
    for cat in CATEGORIES:
        css += f"""
.sq-{cat['id']} {{ background-color: {cat['color']}; }}
"""
    return css


# ------------------------------------------------------------------
# Janela principal
# ------------------------------------------------------------------
class LunuzWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="lunuz tools")
        self.set_default_size(1000, 700)
        self.set_position(Gtk.WindowPosition.CENTER)

        # ---------- CSS ----------
        provider = Gtk.CssProvider()
        provider.load_from_data(_build_css().encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # ícone da janela (Tux colorido)
        _win_icon = os.path.join(ICONS_DIR, "sec-system.png")
        if os.path.exists(_win_icon):
            try:
                Gtk.Window.set_default_icon_from_file(_win_icon)
            except Exception:
                pass

        # ---------- Header bar ----------
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title("lunuz tools")

        self.back_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        self.back_btn.set_tooltip_text("Voltar para a pagina inicial")
        self.back_btn.connect("clicked", self.on_back)
        self.back_btn.set_visible(False)
        header.pack_start(self.back_btn)

        # logo do app (Tux colorido) à esquerda da busca
        logo_path = os.path.join(ICONS_DIR, "sec-system.png")
        if os.path.exists(logo_path):
            try:
                logo_pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 26, 26, True)
                logo = Gtk.Image.new_from_pixbuf(logo_pb)
                logo.set_margin_end(4)
                header.pack_start(logo)
            except Exception:
                pass

        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Pesquisar recursos...")
        self.search.set_width_chars(24)
        self.search.connect("search-changed", self.on_search)
        header.pack_start(self.search)

        title = Gtk.Label()
        title.set_markup("<b>lunuz tools</b>")
        header.set_custom_title(title)

        # view mode toggles (grid / list)
        theme = Gtk.IconTheme.get_default()
        self.btn_grid = Gtk.ToggleButton()
        if theme.has_icon("view-grid-symbolic"):
            self.btn_grid.add(Gtk.Image.new_from_icon_name("view-grid-symbolic", Gtk.IconSize.BUTTON))
        else:
            self.btn_grid.set_label("Grade")
        self.btn_grid.set_active(True)
        self.btn_grid.set_tooltip_text("Visualização em grade")
        self.btn_grid.connect("toggled", self.on_view_toggle)

        self.btn_list = Gtk.ToggleButton()
        if theme.has_icon("view-list-symbolic"):
            self.btn_list.add(Gtk.Image.new_from_icon_name("view-list-symbolic", Gtk.IconSize.BUTTON))
        else:
            self.btn_list.set_label("Lista")
        self.btn_list.set_tooltip_text("Visualização em lista")
        self.btn_list.connect("toggled", self.on_view_toggle)

        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        view_box.get_style_context().add_class("linked")
        view_box.pack_start(self.btn_grid, False, False, 0)
        view_box.pack_start(self.btn_list, False, False, 0)
        header.pack_end(view_box)

        self.set_titlebar(header)

        # ---------- Stack: home / categoria / busca ----------
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(150)

        # home (grade de categorias)
        self.home_scroll = Gtk.ScrolledWindow()
        self.home_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.home_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.home_box.set_border_width(18)

        # chip identificador da distro (logo + ações disponíveis aqui)
        info = detect_distro()
        self.distro_chip = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        chip = self.distro_chip
        chip.get_style_context().add_class("chip")
        chip.set_margin_bottom(14)
        dimg = distro_icon(info, 30)
        if dimg is not None:
            chip.pack_start(dimg, False, False, 0)
        dv = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        t1 = Gtk.Label()
        t1.set_xalign(0)
        name_esc = GLib.markup_escape_text(info["name"])
        ver = info.get("version", "")
        t1.set_markup(
            f"<b>{name_esc}</b>"
            + (f" <small>({GLib.markup_escape_text(ver)})</small>" if ver else "")
        )
        t2 = Gtk.Label()
        t2.set_xalign(0)
        t2.get_style_context().add_class("dim-label")
        total = sum(len(c["items"]) for c in CATEGORIES)
        n_ok = sum(1 for c in CATEGORIES for it in c["items"]
                   if item_available(it, info["family"]))
        fam = FAMILY_NAMES.get(info["family"], info["family"])
        t2.set_text(f"Família {fam} • {n_ok} de {total} ações disponíveis nesta distro")
        dv.pack_start(t1, False, False, 0)
        dv.pack_start(t2, False, False, 0)
        chip.pack_start(dv, True, True, 0)
        self.home_box.pack_start(chip, False, False, 0)

        self.home_grid = Gtk.Grid()
        self.home_grid.set_row_spacing(14)
        self.home_grid.set_column_spacing(14)
        self.home_grid.set_column_homogeneous(True)
        self.home_box.pack_start(self.home_grid, False, False, 0)
        self.home_scroll.add(self.home_box)
        self.stack.add_named(self.home_scroll, "home")

        # categoria
        self.cat_scroll = Gtk.ScrolledWindow()
        self.cat_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.cat_box.set_border_width(18)
        self.cat_scroll.add(self.cat_box)
        self.stack.add_named(self.cat_scroll, "category")

        # busca
        self.search_scroll = Gtk.ScrolledWindow()
        self.search_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.search_box.set_border_width(18)
        self.search_scroll.add(self.search_box)
        self.stack.add_named(self.search_scroll, "search")

        # terminal - aba dedicada para acompanhar o progresso das instalacoes
        self.term_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        tpage_head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        tpage_head.set_border_width(6)
        tlbl = Gtk.Label()
        tlbl.set_xalign(0)
        tlbl.set_markup("<b>Terminal</b> — progresso da instalação")
        tpage_head.pack_start(tlbl, False, False, 0)
        self.spinner = Gtk.Spinner()
        tpage_head.pack_start(self.spinner, False, False, 0)
        self.status_lbl = Gtk.Label()
        self.status_lbl.set_xalign(0)
        self.status_lbl.set_max_width_chars(60)
        self.status_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        tpage_head.pack_start(self.status_lbl, True, True, 0)
        tclear = Gtk.Button.new_from_icon_name("edit-clear-symbolic", Gtk.IconSize.BUTTON)
        tclear.set_tooltip_text("Limpar terminal")
        tclear.connect("clicked", lambda *_: self.terminal.reset(True, True))
        tpage_head.pack_end(tclear, False, False, 0)
        self.term_page.pack_start(tpage_head, False, False, 0)
        self.term_host = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.term_page.pack_start(self.term_host, True, True, 0)
        self.stack.add_named(self.term_page, "terminal")

        self.build_home()
        self.stack.set_visible_child_name("home")

        # ---------- Terminal ----------
        self.term_box = term_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        term_box.get_style_context().add_class("termbox")

        term_head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        term_head.set_border_width(6)
        lbl = Gtk.Label()
        lbl.set_xalign(0)
        lbl.set_markup("<b>Terminal</b>")
        term_head.pack_start(lbl, True, True, 0)
        clear_btn = Gtk.Button.new_from_icon_name("edit-clear-symbolic", Gtk.IconSize.BUTTON)
        clear_btn.set_tooltip_text("Limpar terminal")
        clear_btn.connect("clicked", lambda *_: self.terminal.reset(True, True))
        term_head.pack_end(clear_btn, False, False, 0)
        term_box.pack_start(term_head, False, False, 0)

        self.terminal = Vte.Terminal()
        self.terminal.set_scrollback_lines(20000)
        self.terminal.connect("child-exited", self.on_child_exited)
        try:
            self.terminal.set_font(Pango.FontDescription("Monospace 10.5"))
        except Exception:
            pass
        try:
            self.terminal.set_colors(
                Gdk.RGBA(red=0.87, green=0.87, blue=0.9),
                Gdk.RGBA(red=0.07, green=0.07, blue=0.1),
                [],
            )
        except Exception:
            pass
        term_box.pack_start(self.terminal, True, True, 0)

        # aviso mostrado no painel inferior quando o terminal esta na aba dedicada
        self.bot_hint = Gtk.Label()
        self.bot_hint.set_xalign(0.5)
        self.bot_hint.set_halign(Gtk.Align.CENTER)
        self.bot_hint.set_margin_top(14)
        self.bot_hint.set_margin_bottom(14)
        self.bot_hint.set_markup(
            '<span foreground="#8a8a98">Acompanhe o progresso na aba <b>Terminal</b>.</span>'
        )
        self.bot_hint.set_no_show_all(True)
        self.bot_hint.set_visible(False)
        term_box.pack_start(self.bot_hint, False, False, 0)

        # ---------- Rodapé com links ----------
        footer = Gtk.Label()
        footer.set_use_markup(True)
        footer.set_xalign(0.5)
        footer.set_margin_top(6)
        footer.set_margin_bottom(6)
        footer.get_style_context().add_class("footer")
        readme = _readme_uri()
        footer.set_markup(
            '<span size="small">   <a href="%s">Wiki</a>'
            "   |   <a href=\"https://github.com/DAVIB3BR/Linuz-Tools/issues\">Reportar Bug</a>"
            "   |   <a href=\"https://github.com/DAVIB3BR/Linuz-Tools\">Portal do Desenvolvedor</a>"
            "   |   <a href=\"https://github.com/DAVIB3BR/Linuz-Tools\">Apoie este projeto</a>   </span>"
            % readme
        )
        footer.connect("activate-link", self.on_link)

        # ---------- Composição ----------
        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        paned.set_position(420)
        paned.pack1(self.stack, True, True)
        paned.pack2(term_box, True, True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.pack_start(paned, True, True, 0)
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        vbox.pack_start(footer, False, False, 0)
        self.add(vbox)

        self.current_cat = None
        self.prev_page = "home"
        # fila de execucao (evita saidas misturadas no terminal)
        self.run_queue = []
        self.running = False
        self.batch = None
        # selecao multipla
        self.multi_mode = False
        self.selected_ids = set()
        self.row_by_id = {}
        self.ind_by_id = {}
        self.connect("key-press-event", self.on_key_press)
        self.terminal.feed(
            b"lunuz tools - selecione uma secao na grade acima e clique em uma acao.\r\n"
            b"Acoes de administracao pedem autenticacao (pkexec).\r\n\r\n"
        )

    # ------------------------------------------------------------------
    # Navegação (voltar / páginas / terminal)
    # ------------------------------------------------------------------
    def show_page(self, name):
        """Navega para uma página e atualiza o botão voltar + terminal."""
        prev = self.stack.get_visible_child_name()
        if name == "terminal" and prev != "terminal":
            self._move_terminal("page")
        elif prev == "terminal" and name != "terminal":
            self._move_terminal("bottom")
        self.stack.set_visible_child_name(name)
        self.back_btn.set_visible(name != "home")
        if name == "home":
            # limpa a busca ao voltar para a grade
            if self.search.get_text():
                self.search.set_text("")
            self.home_scroll.get_vadjustment().set_value(0)
        elif name == "category":
            self.cat_scroll.get_vadjustment().set_value(0)
        elif name == "search":
            self.search_scroll.get_vadjustment().set_value(0)

    def _move_terminal(self, dest):
        """Move o widget do terminal entre a aba dedicada e o painel inferior."""
        target = self.term_host if dest == "page" else self.term_box
        term = self.terminal
        if term.get_parent() is target:
            return
        parent = term.get_parent()
        if parent is not None:
            parent.remove(term)
        target.pack_start(term, True, True, 0)
        term.show()
        self.bot_hint.set_visible(dest == "page")
        if dest == "bottom":
            term.grab_focus()

    def _sync_terminal_layout(self):
        """Reaplica o layout do terminal (apos show_all do activate)."""
        on_page = self.stack.get_visible_child_name() == "terminal"
        self.bot_hint.set_visible(on_page)

    def set_status(self, text):
        self.status_lbl.set_text(text)

    def on_key_press(self, _widget, ev):
        ctrl = ev.state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and ev.keyval in (Gdk.KEY_f, Gdk.KEY_F):
            self.search.grab_focus()
            return True
        if ev.keyval == Gdk.KEY_Escape:
            if self.search.get_text():
                self.search.set_text("")
                return True
            if self.stack.get_visible_child_name() != "home":
                self.show_page("home")
                return True
        return False

    # ------------------------------------------------------------------
    # Home: grade de categorias
    # ------------------------------------------------------------------
    def build_home(self):
        for child in self.home_grid.get_children():
            self.home_grid.remove(child)
        cols = 2 if self.btn_grid.get_active() else 1
        for i, cat in enumerate(CATEGORIES):
            tile = self.make_tile(cat)
            self.home_grid.attach(tile, i % cols, i // cols, 1, 1)
        self.home_box.show_all()

    def make_tile(self, cat):
        btn = Gtk.Button()
        btn.get_style_context().add_class("tile")
        btn.set_relief(Gtk.ReliefStyle.NONE)
        btn.set_hexpand(True)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        box.set_border_width(4)

        # ícone colorido ilustrativo (estilo LinuxToys); fallback: quadrado
        color_icon = section_icon(cat, 54)
        if color_icon is not None:
            box.pack_start(color_icon, False, False, 0)
        else:
            sq = Gtk.Box()
            sq.set_valign(Gtk.Align.CENTER)
            sq.get_style_context().add_class("sq")
            sq.get_style_context().add_class(f"sq-{cat['id']}")
            icon = Gtk.Image.new_from_icon_name(cat["icon"], Gtk.IconSize.DIALOG)
            icon.set_halign(Gtk.Align.CENTER)
            icon.set_valign(Gtk.Align.CENTER)
            icon.get_style_context().add_class("white")
            sq.add(icon)
            box.pack_start(sq, False, False, 0)

        lbl = Gtk.Label()
        lbl.set_text(cat["name"])
        lbl.set_xalign(0.5)
        lbl.set_halign(Gtk.Align.CENTER)

        box.pack_start(lbl, True, True, 0)
        btn.add(box)
        btn.connect("clicked", self.on_tile_clicked, cat)
        return btn

    def on_tile_clicked(self, _btn, cat):
        if cat.get("id") == "terminal":
            self.show_page("terminal")
            return
        self.open_category(cat)

    # ------------------------------------------------------------------
    # Página de categoria (com seleção múltipla)
    # ------------------------------------------------------------------
    def open_category(self, cat, reset_scroll=True):
        if cat.get("id") == "terminal":
            self.show_page("terminal")
            return
        if self.current_cat is not cat:
            self.selected_ids.clear()
        self.current_cat = cat
        for child in self.cat_box.get_children():
            self.cat_box.remove(child)

        # cabeçalho com o ícone colorido da seção (estilo LinuxToys)
        hrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        hicon = section_icon(cat, 46)
        if hicon is None:
            hsq = Gtk.Box()
            hsq.set_valign(Gtk.Align.CENTER)
            hsq.get_style_context().add_class("sq")
            hsq.get_style_context().add_class(f"sq-{cat['id']}")
            himg = Gtk.Image.new_from_icon_name(cat["icon"], Gtk.IconSize.DIALOG)
            himg.set_halign(Gtk.Align.CENTER)
            himg.set_valign(Gtk.Align.CENTER)
            himg.set_pixel_size(30)
            hsq.add(himg)
            hrow.pack_start(hsq, False, False, 0)
        else:
            hrow.pack_start(hicon, False, False, 0)

        head = Gtk.Label()
        head.set_xalign(0)
        head.set_markup(f'<span size="xx-large" weight="bold">{cat["name"]}</span>')

        sub = Gtk.Label()
        sub.set_xalign(0)
        n = len(cat["items"])
        distro = detect_distro()["name"]
        n_ok = sum(1 for it in cat["items"] if item_available(it))
        txt = f"{n} recursos - detectado: {distro}"
        if n_ok < n:
            txt += f" - {n_ok}/{n} disponíveis"
        sub.set_text(txt)
        sub.get_style_context().add_class("dim-label")

        htexts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        htexts.pack_start(head, False, False, 0)
        htexts.pack_start(sub, False, False, 0)
        hrow.pack_start(htexts, True, True, 0)
        self.cat_box.pack_start(hrow, False, False, 0)

        # barra de seleção múltipla
        mrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.multi_toggle = Gtk.ToggleButton()
        mbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mbox.pack_start(Gtk.Image.new_from_icon_name("edit-select-all-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
        mbox.pack_start(Gtk.Label("Seleção múltipla"), False, False, 0)
        self.multi_toggle.add(mbox)
        self.multi_toggle.set_active(self.multi_mode)
        self.multi_toggle.connect("toggled", self.on_multi_toggle)
        self.sel_count_lbl = Gtk.Label()
        self.sel_count_lbl.set_xalign(0)
        mrow.pack_start(self.multi_toggle, False, False, 0)
        mrow.pack_start(self.sel_count_lbl, False, False, 0)
        self.cat_box.pack_start(mrow, False, False, 0)

        self.row_by_id = {}
        self.ind_by_id = {}
        for item in cat["items"]:
            row = self.make_item_row(cat, item)
            self.row_by_id[item["id"]] = row
            self.cat_box.pack_start(row, False, False, 0)

        # barra de ações da seleção (executar/limpar) — com ícones
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.set_margin_top(4)

        self.btn_run_sel = Gtk.Button()
        rbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        rbox.pack_start(Gtk.Image.new_from_icon_name("media-playback-start-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
        rbox.pack_start(Gtk.Label("Executar selecionados"), False, False, 0)
        self.btn_run_sel.add(rbox)
        self.btn_run_sel.get_style_context().add_class("suggested-action")
        self.btn_run_sel.connect("clicked", lambda *_: self.on_run_selected())

        btn_clr = Gtk.Button()
        cbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cbox.pack_start(Gtk.Image.new_from_icon_name("edit-clear-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
        cbox.pack_start(Gtk.Label("Limpar seleção"), False, False, 0)
        btn_clr.add(cbox)
        btn_clr.connect("clicked", lambda *_: self.clear_selection())
        bar.pack_start(self.btn_run_sel, False, False, 0)
        bar.pack_start(btn_clr, False, False, 0)
        self.cat_box.pack_start(bar, False, False, 0)
        self.sel_bar = bar

        self.cat_box.show_all()
        if reset_scroll:
            self.cat_scroll.get_vadjustment().set_value(0)
        self.show_page("category")
        self.update_sel_ui()

    def make_item_row(self, cat, item):
        row = Gtk.Button()
        row.get_style_context().add_class("itemrow")
        row.set_relief(Gtk.ReliefStyle.NONE)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_border_width(5)

        # ícone colorido do item (marca ou genérico); fallback: quadrado
        lead = item_icon_image(item, 36)
        if lead is None:
            sq = Gtk.Box()
            sq.set_valign(Gtk.Align.CENTER)
            sq.get_style_context().add_class("sq-sm")
            sq.get_style_context().add_class(f"sq-{cat['id']}")
            icon = Gtk.Image.new_from_icon_name(item_icon(item) or cat["icon"], Gtk.IconSize.BUTTON)
            icon.set_halign(Gtk.Align.CENTER)
            icon.set_valign(Gtk.Align.CENTER)
            sq.add(icon)
            lead = sq

        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name = Gtk.Label()
        name.set_xalign(0)
        title = item["name"]
        if item.get("danger"):
            title += "   [atenção]"
        name.set_markup(f"<b>{GLib.markup_escape_text(title)}</b>")
        desc = Gtk.Label()
        desc.set_xalign(0)
        desc.set_text(item["desc"])
        desc.get_style_context().add_class("dim-label")
        texts.pack_start(name, False, False, 0)
        texts.pack_start(desc, False, False, 0)

        kind = item.get("kind", "shell")
        avail = item_available(item)
        selectable = kind in ("shell", "info") and avail
        selected = item["id"] in self.selected_ids

        if not avail:
            # ação exclusiva de outra distro: esmaecida + badge; clique explica
            row.get_style_context().add_class("unavail")
            fams = ", ".join(FAMILY_NAMES.get(f, f)
                             for f in available_families(item))
            bad = Gtk.Label()
            bad.set_text(f"só em {fams}" if fams else "indisponível")
            bad.set_valign(Gtk.Align.CENTER)
            bad.get_style_context().add_class("badgelbl")
            box.pack_start(lead, False, False, 0)
            box.pack_start(texts, True, True, 0)
            box.pack_start(bad, False, False, 0)
        elif self.multi_mode and selectable:
            # no modo selecao: indicador no lugar da seta
            ind = Gtk.Image.new_from_icon_name(
                "checkbox-checked-symbolic" if selected else "object-select-symbolic",
                Gtk.IconSize.BUTTON,
            )
            ind.set_valign(Gtk.Align.CENTER)
            box.pack_start(lead, False, False, 0)
            box.pack_start(texts, True, True, 0)
            box.pack_start(ind, False, False, 0)
            self.ind_by_id[item["id"]] = ind
            if selected:
                row.get_style_context().add_class("sel")
        elif self.multi_mode:
            # form/file: exigem preenchimento manual - ficam destacados
            man = Gtk.Label()
            man.set_text("preenchimento manual")
            man.get_style_context().add_class("dim-label")
            box.pack_start(lead, False, False, 0)
            box.pack_start(texts, True, True, 0)
            box.pack_start(man, False, False, 0)
            row.get_style_context().add_class("man")
        else:
            go = Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.BUTTON)
            go.set_valign(Gtk.Align.CENTER)
            box.pack_start(lead, False, False, 0)
            box.pack_start(texts, True, True, 0)
            box.pack_start(go, False, False, 0)

        row.add(box)
        row.connect("clicked", self.on_item_clicked, cat, item)
        return row

    def on_back(self, *_btn):
        # Volta para a grade; se estiver na busca, volta para a pagina anterior a ela
        if self.stack.get_visible_child_name() == "search" and self.prev_page != "home":
            target = self.prev_page
            self.search.set_text("")  # limpa busca (nao mexe na pagina atual)
            self.show_page(target)
            return
        self.show_page("home")

    # ------------------------------------------------------------------
    # Busca
    # ------------------------------------------------------------------
    def on_search(self, entry):
        text = entry.get_text().strip()
        if not text:
            # Restaura a pagina de onde a busca partiu
            if self.stack.get_visible_child_name() == "search":
                self.show_page(self.prev_page)
            return

        # Grava a pagina atual antes de trocar para resultados
        current = self.stack.get_visible_child_name()
        if current != "search":
            self.prev_page = current

        for child in self.search_box.get_children():
            self.search_box.remove(child)

        hits = 0
        low = text.lower()
        for cat, item in all_items():
            hay = f"{cat['name']} {item['name']} {item['desc']}".lower()
            if low in hay:
                self.search_box.pack_start(self.make_item_row(cat, item), False, False, 0)
                hits += 1

        lbl = Gtk.Label()
        lbl.set_xalign(0)
        if hits:
            lbl.set_markup(
                f'<span weight="bold">{hits} resultado(s) para "{GLib.markup_escape_text(text)}"</span>'
            )
        else:
            lbl.set_text(f'Nenhum resultado para "{text}"')
        self.search_box.pack_start(lbl, False, False, 0)
        self.search_box.show_all()
        self.show_page("search")

    # ------------------------------------------------------------------
    # Visualização grade/lista
    # ------------------------------------------------------------------
    def on_view_toggle(self, btn):
        other = self.btn_list if btn is self.btn_grid else self.btn_grid
        if not btn.get_active():
            # Impede que os dois fiquem inativos (comportamento radio)
            if not other.get_active():
                btn.set_active(True)  # reentra com o botao ativo
            return
        if other.get_active():
            other.set_active(False)  # reentra no outro (inativo -> retorna)
        self.build_home()

    # ------------------------------------------------------------------
    # Execução de itens
    # ------------------------------------------------------------------
    def on_item_clicked(self, _btn, cat, item):
        if not item_available(item):
            self.show_unavailable(item)
            return
        kind = item.get("kind", "shell")
        # ---- modo seleção múltipla: clicar alterna a seleção ----
        if self.multi_mode:
            if kind in ("shell", "info"):
                self.toggle_select(item)
            else:
                msg = (f"«{item['name']}» exige preenchimento manual - "
                       "desative a seleção múltipla para executá-lo.")
                self.set_status(msg)
                self.terminal.feed(f"# {msg}\r\n".encode())
            return
        if kind == "info":
            script = item["script"]
            if callable(script):
                script = script()
            self.run_script(script, root=False, label=item["name"])
        elif kind == "shell":
            if item.get("danger") and not self.confirm(item):
                return
            script = item["script"]
            if callable(script):
                script = script()
            self.run_script(script, root=item.get("root", False), label=item["name"])
        elif kind == "file":
            self.run_file_chooser(item)
        elif kind == "form":
            self.run_form(item)

    # ------------------------------------------------------------------
    # Seleção múltipla
    # ------------------------------------------------------------------
    def on_multi_toggle(self, btn):
        self.multi_mode = btn.get_active()
        self.selected_ids.clear()
        if self.current_cat is not None:
            self.open_category(self.current_cat, reset_scroll=False)

    def toggle_select(self, item):
        iid = item["id"]
        if iid in self.selected_ids:
            self.selected_ids.discard(iid)
        else:
            self.selected_ids.add(iid)
        selected = iid in self.selected_ids
        row = self.row_by_id.get(iid)
        if row:
            if selected:
                row.get_style_context().add_class("sel")
            else:
                row.get_style_context().remove_class("sel")
        ind = self.ind_by_id.get(iid)
        if ind:
            ind.set_from_icon_name(
                "checkbox-checked-symbolic" if selected else "object-select-symbolic",
                Gtk.IconSize.BUTTON,
            )
        self.update_sel_ui()

    def update_sel_ui(self):
        n = len(self.selected_ids)
        if getattr(self, "sel_count_lbl", None):
            self.sel_count_lbl.set_text(
                f"{n} selecionado(s)" if self.multi_mode else "Seleção múltipla desativada"
            )
        if getattr(self, "sel_bar", None):
            self.sel_bar.set_visible(self.multi_mode)
        if getattr(self, "btn_run_sel", None):
            self.btn_run_sel.set_sensitive(n > 0)

    def clear_selection(self):
        self.selected_ids.clear()
        for iid, row in list(self.row_by_id.items()):
            row.get_style_context().remove_class("sel")
            ind = self.ind_by_id.get(iid)
            if ind:
                ind.set_from_icon_name("object-select-symbolic", Gtk.IconSize.BUTTON)
        self.update_sel_ui()

    def on_run_selected(self):
        cat = self.current_cat
        if not cat:
            return
        items = [i for i in cat["items"]
                 if i["id"] in self.selected_ids
                 and i.get("kind", "shell") in ("shell", "info")]
        if not items:
            return
        if not self.confirm_batch(cat, items):
            return
        self.batch = {"total": len(items), "done": 0}
        for item in items:
            script = item["script"]
            if callable(script):
                script = script()
            self.run_script(script, root=item.get("root", False), label=item["name"])
        n = len(items)
        self.terminal.feed(
            f"### Fila: {n} acao(oes) de «{cat['name']}» enfileirada(s).\r\n".encode()
        )
        self.set_status(f"{n} ações enfileiradas - veja a aba Terminal.")
        self.clear_selection()

    def confirm_batch(self, cat, items):
        names = "\n".join(f"• {it['name']}" for it in items[:8])
        if len(items) > 8:
            names += f"\n... e mais {len(items) - 8}"
        root_n = sum(1 for it in items if it.get("root"))
        extra = f"\n\n{root_n} pedirão autenticação (senha de administrador)." if root_n else ""
        dlg = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=f"Executar {len(items)} ação(oes) de «{cat['name']}»?",
        )
        dlg.format_secondary_text(names + extra)
        dlg.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dlg.add_button("Executar todas", Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.CANCEL)
        resp = dlg.run()
        dlg.destroy()
        return resp == Gtk.ResponseType.OK

    def show_unavailable(self, item):
        """Diálogo explicando por que a ação não roda nesta distro."""
        fams = ", ".join(FAMILY_NAMES.get(f, f)
                         for f in available_families(item))
        det = detect_distro()
        dlg = Gtk.MessageDialog(
            transient_for=self, flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=f"«{item['name']}» não está disponível nesta distro",
        )
        atual = f"{det['name']} {det.get('version', '')}".strip()
        dlg.format_secondary_text(
            f"Disponível em: {fams}\nDetectado: {atual}"
        )
        dlg.run()
        dlg.destroy()

    def confirm(self, item):
        dlg = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=f"Executar: {item['name']}?",
        )
        dlg.format_secondary_text(
            f"{item['desc']}\n\nEsta ação modifica o sistema"
            + (" e pode exigir reinicialização." if item.get("root") else ".")
        )
        # ícone colorido do item na confirmação (estilo LinuxToys)
        cimg = item_icon_image(item, 48)
        if cimg is not None:
            try:
                dlg.set_image(cimg)
                dlg.set_image_visible(True)
            except Exception:
                pass
        dlg.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dlg.add_button("Executar", Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.CANCEL)
        resp = dlg.run()
        dlg.destroy()
        return resp == Gtk.ResponseType.OK

    def run_script(self, script, root=False, label=None):
        # Remove scripts temporarios antigos (> 1h) para nao acumular em /tmp
        import glob
        import time
        now = time.time()
        for old in glob.glob("/tmp/lunuz_act_*.sh"):
            try:
                if now - os.path.getmtime(old) > 3600:
                    os.remove(old)
            except OSError:
                pass

        # grava em arquivo temporario (evita problemas de aspas)
        fd, path = tempfile.mkstemp(prefix="lunuz_act_", suffix=".sh")
        with os.fdopen(fd, "w") as fh:
            fh.write("#!/bin/bash\n")
            fh.write(script)
        os.chmod(path, 0o700)

        if root:
            if not _which("pkexec"):
                self.terminal.feed(
                    b"\r\nERRO: pkexec nao encontrado. Instale policykit-1/polkit.\r\n"
                )
                os.remove(path)
                return
            argv = ["pkexec", "/bin/bash", path]
            shown = f"pkexec bash <script>  # {label or ''}"
        else:
            argv = ["/bin/bash", path]
            shown = f"bash <script>  # {label or ''}"
        self.run_argv(argv, shown)

    def run_file_chooser(self, item):
        dlg = Gtk.FileChooserDialog(
            title=f"Selecionar arquivo - {item['name']}",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dlg.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dlg.add_button("Abrir", Gtk.ResponseType.OK)
        filt = Gtk.FileFilter()
        patt = item.get("filter", "*")
        for p in patt.split():
            filt.add_pattern(p)
        filt.set_name(patt)
        dlg.add_filter(filt)
        resp = dlg.run()
        path = dlg.get_filename()
        dlg.destroy()
        if resp != Gtk.ResponseType.OK or not path:
            return
        argv = [sys.executable, "-m", "lunuz", item["tool"], path]
        self.run_argv(argv, f"lunuz {item['tool']} {path}")

    def run_form(self, item):
        dlg = Gtk.Dialog(title=item["name"], transient_for=self, flags=0)
        dlg.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Executar", Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        grid = Gtk.Grid()
        grid.set_row_spacing(8)
        grid.set_column_spacing(10)
        grid.set_border_width(12)
        entries = []
        for i, (label, default) in enumerate(item.get("fields", [])):
            lbl = Gtk.Label(label=f"{label}:")
            lbl.set_xalign(1)
            ent = Gtk.Entry()
            ent.set_text(default)
            ent.set_width_chars(32)
            ent.set_activates_default(True)  # Enter dispara "Executar" em qualquer campo
            grid.attach(lbl, 0, i, 1, 1)
            grid.attach(ent, 1, i, 1, 1)
            entries.append(ent)
        box = dlg.get_content_area()
        box.add(grid)
        dlg.show_all()
        resp = dlg.run()
        values = [e.get_text().strip() for e in entries]
        dlg.destroy()
        if resp != Gtk.ResponseType.OK:
            return
        if item.get("danger") and not self.confirm(item):
            return
        # Template opcional de argv (ex.: find precisa de -name)
        tmpl = item.get("argv_tmpl")
        if tmpl:
            parts = [part.format(*values) for part in tmpl]
        else:
            parts = [item["tool"]] + values
        argv = [sys.executable, "-m", "lunuz"] + parts
        pretty = "lunuz " + " ".join(parts)
        self.run_argv(argv, pretty)

    def run_argv(self, argv, pretty=None):
        """Executa um comando; se outro estiver rodando, entra na fila."""
        cmd = pretty or " ".join(argv)
        if self.running:
            self.run_queue.append((argv, pretty))
            n = len(self.run_queue)
            self.set_status(f"Na fila ({n} pendente(s)): {cmd}")
            self.terminal.feed(f"... na fila ({n}): {cmd}\r\n".encode())
            return
        self._spawn(argv, pretty)

    def _spawn(self, argv, pretty):
        cmd = pretty or " ".join(argv)
        self.running = True
        self.terminal.feed(f"\r\n$ {cmd}\r\n".encode())
        if self.batch:
            step = self.batch["done"] + 1
            self.set_status(f"Executando {step}/{self.batch['total']}: {cmd}")
        else:
            self.set_status(f"Executando: {cmd}")
        self.spinner.start()
        # Garante que filhos "python3 -m lunuz" achem o pacote mesmo quando o
        # ambiente pai nao possui PYTHONPATH (execucao direta do gui.py)
        envv = None
        pkg_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        have = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
        if pkg_parent not in have:
            envv = [f"{k}={v}" for k, v in os.environ.items() if k != "PYTHONPATH"]
            envv.append("PYTHONPATH=" + os.pathsep.join([pkg_parent] + have))
        try:
            self.terminal.spawn_sync(
                Vte.PtyFlags.DEFAULT,
                None,
                argv,
                envv,
                GLib.SpawnFlags.DEFAULT,
                None,
                None,
                None,
            )
        except Exception as e:
            self.running = False
            self.spinner.stop()
            self.set_status(f"Erro ao iniciar: {e}")
            self.terminal.feed(f"erro ao executar: {e}\r\n".encode())

    def on_child_exited(self, _term, status):
        self.running = False
        self.spinner.stop()
        try:
            code = os.waitstatus_to_exitcode(status)
            if code < 0:
                code = 128 - code
        except Exception:
            code = status
        if self.batch:
            self.batch["done"] += 1
        if self.run_queue:
            nxt = self.run_queue.pop(0)
            if self.batch:
                self.set_status(
                    f"Etapa {self.batch['done']}/{self.batch['total']} ok (código {code}) - próxima..."
                )
            else:
                self.set_status(f"Anterior ok (código {code}) - próxima da fila...")
            self._spawn(*nxt)
            return
        if self.batch:
            info = self.batch
            self.batch = None
            self.set_status(
                f"Fila concluída: {info['done']}/{info['total']} ações (último código {code})."
            )
        elif code == 0:
            self.set_status("Concluído com sucesso.")
        else:
            self.set_status(f"Finalizado com código {code} - verifique o terminal.")
        self.terminal.feed(f"[fim, código {code}]\r\n".encode())

    # ------------------------------------------------------------------
    def on_link(self, _label, uri):
        try:
            Gtk.show_uri_on_window(self, uri, Gdk.CURRENT_TIME)
        except Exception:
            pass
        return True


def _readme_uri():
    for base in (
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        os.path.expanduser("~/lunuz_tools"),
    ):
        p = os.path.join(base, "README.md")
        if os.path.isfile(p):
            return "file://" + p
    return "https://github.com/DAVIB3BR/Linuz-Tools"


# ------------------------------------------------------------------
class LunuzApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.davi.lunuz-tools")
        self.win = None

    def do_activate(self):
        if not self.win:
            self.win = LunuzWindow(self)
        self.win.show_all()
        # show_all() reexibe tudo - volta a esconder o botao na home
        if self.win.stack.get_visible_child_name() == "home":
            self.win.back_btn.set_visible(False)
        self.win._sync_terminal_layout()
        self.win.update_sel_ui()
        self.win.present()


def main():
    app = LunuzApp()
    sys.exit(app.run(None))


if __name__ == "__main__":
    main()
