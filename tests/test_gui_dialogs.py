"""Teste real dos diálogos do lunuz GUI sem usar o mouse.

- Formulario (ls): preenche entry real, clica Executar, roda DE VERDADE no terminal
- Seletor de arquivo (cat): seleciona arquivo real, roda DE VERDADE
- Confirmacao de perigo (chmod): OK executa (gravado), CANCEL nao executa
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("LUNUZ_LANG", "pt_BR")  # testes deterministicos: textos em pt_BR
os.chdir(os.path.expanduser("~"))

# fixture dos testes: dir com arquivo (conteudo "alvo-x") + subpasta
os.makedirs("/tmp/gtest/sub", exist_ok=True)
with open("/tmp/gtest/a.txt", "w") as _f:
    _f.write("alvo-x\nlinha 2\n")

from lunuz import gui
from gi.repository import Gtk, GLib, Gdk, Vte

recorded = []
errors = []
allow_real = {"on": False}
_real_run_argv = gui.LunuzWindow.run_argv


def rec(self, argv, pretty=None):
    recorded.append(list(argv))
    if allow_real["on"]:
        _real_run_argv(self, argv, pretty)


gui.LunuzWindow.run_argv = rec

app = gui.LunuzApp()
win = None  # preenchido no activate (janelas so podem ser criadas apos startup)


def on_activate(a):
    """Cria a janela apos o startup do GApplication e inicia os testes."""
    global win
    if not a.win:
        a.win = gui.LunuzWindow(a)
    win = a.win
    win.connect("destroy", _on_destroy)
    win.show_all()
    if win.stack.get_visible_child_name() == "home":
        win.back_btn.set_visible(False)
    schedule(400, "abrir formulario ls", s1_abrir_ls)


def _on_destroy(*_a):
    import traceback
    print("AVISO: janela principal destruida! stack:", flush=True)
    print("".join(traceback.format_stack()), flush=True)


# ---------- helpers ----------
def find_form(title_part):
    for w in Gtk.Window.list_toplevels():
        if (isinstance(w, Gtk.Dialog) and not isinstance(w, Gtk.MessageDialog)
                and title_part in (w.get_title() or "")):
            return w
    return None


def find_filechooser(title_part):
    for w in Gtk.Window.list_toplevels():
        if isinstance(w, Gtk.FileChooserDialog) and title_part in (w.get_title() or ""):
            return w
    return None


def find_msgdialog():
    for w in Gtk.Window.list_toplevels():
        if isinstance(w, Gtk.MessageDialog):
            return w
    return None


def term_text(term):
    try:
        n = term.get_row_count()
        r = term.get_text_range_format(Vte.Format.TEXT, 0, 0, n, 500)
        if isinstance(r, tuple):
            return r[0] or ""
        return r or ""
    except Exception:
        return ""


def all_entries(widget):
    out = []
    if isinstance(widget, Gtk.Entry):
        out.append(widget)
    if isinstance(widget, Gtk.Container):
        for c in widget.get_children():
            out += all_entries(c)
    return out


def items_of(cat_id):
    for c in gui.CATEGORIES:
        if c["id"] == cat_id:
            return c, {i["id"]: i for i in c["items"]}
    raise KeyError(cat_id)


def step(name, fn):
    def _run():
        try:
            fn()
            print(f"OK {name}", flush=True)
        except Exception:
            import traceback
            tb = traceback.format_exc()
            errors.append(f"[{name}]\n" + tb)
            print(f"FALHOU {name}\n{tb}", flush=True)
        return False
    return _run


def schedule(ms, name, fn, *args):
    GLib.timeout_add(ms, step(name, lambda: fn(*args)))


# ---------- passos ----------
def s1_abrir_ls():
    cat, its = items_of("utils")
    win.open_category(cat)
    assert win.stack.get_visible_child_name() == "category"
    schedule(600, "form ls aberto", s2_form_ls)
    win.on_item_clicked(None, cat, its["u-ls"])  # bloqueia em dlg.run() (loop aninhado)


def s2_form_ls():
    dlg = find_form("Listar diret")
    assert dlg is not None, "dialogo do formulario nao abriu"
    entries = all_entries(dlg)
    assert len(entries) == 1, f"esperava 1 entry, achou {len(entries)}"
    entries[0].set_text("/tmp/gtest")
    allow_real["on"] = True   # esta execucao roda de verdade
    dlg.response(Gtk.ResponseType.OK)
    schedule(1600, "saida do ls no terminal", s3_ls_output)


def s3_ls_output():
    allow_real["on"] = False
    expect = [sys.executable, "-m", "lunuz", "ls", "/tmp/gtest"]
    assert recorded and recorded[0] == expect, f"argv errado: {recorded[:1]}"
    txt = term_text(win.terminal)
    assert "a.txt" in txt and "sub" in txt, f"terminal sem saida do ls: {txt[-300:]!r}"
    print("   -> terminal mostra a.txt e sub (execucao real confirmada)")
    schedule(400, "seletor de arquivo", s4_start_cat)


def s4_start_cat():
    cat, its = items_of("utils")
    schedule(600, "seletor preenchido", s5_filechooser)
    win.on_item_clicked(None, cat, its["u-cat"])  # abre FileChooserDialog


def s5_filechooser():
    dlg = find_filechooser("Selecionar arquivo")
    assert dlg is not None, "seletor de arquivo nao abriu"
    # a pasta carrega de forma assincrona: seleciona e espera "grudar"
    dlg.select_filename("/tmp/gtest/a.txt")
    schedule(300, "selecao do seletor", s5b_respond, dlg)


def s5b_respond(dlg):
    if dlg.get_filename() is None:
        dlg.select_filename("/tmp/gtest/a.txt")
        schedule(300, "selecao do seletor (retry)", s5b_respond, dlg)
        return
    assert dlg.get_filename() == "/tmp/gtest/a.txt", f"path: {dlg.get_filename()!r}"
    allow_real["on"] = True
    dlg.response(Gtk.ResponseType.OK)
    schedule(1600, "saida do cat no terminal", s6_cat_output)


def s6_cat_output():
    allow_real["on"] = False
    expect = [sys.executable, "-m", "lunuz", "cat", "/tmp/gtest/a.txt"]
    assert recorded[1] == expect, f"argv cat errado: {recorded[1:2]}"
    txt = term_text(win.terminal)
    assert "alvo-x" in txt, f"terminal sem saida do cat: {txt[-300:]!r}"
    print("   -> terminal mostra conteudo do arquivo (cat real)")
    schedule(400, "chmod perigo (OK)", s7_start_chmod_ok)


def s7_start_chmod_ok():
    cat, its = items_of("utils")
    schedule(600, "confirmacao de perigo respondida", s8_confirm_ok)
    win.on_item_clicked(None, cat, its["u-chmod"])  # formulario + confirmacao


def s8_confirm_ok():
    # s8 e disparado ENQUANTO o formulario roda; responde o form e deixa a
    # confirmacao abrir dentro deste mesmo callback (loop aninhado seguinte)
    form = find_form("Permiss")
    assert form is not None, "formulario chmod nao abriu"
    schedule(500, "confirm OK", s9_do_confirm_ok)
    form.response(Gtk.ResponseType.OK)  # -> abre MessageDialog (loop aninhado)


def s9_do_confirm_ok():
    md = find_msgdialog()
    assert md is not None, "dialogo de confirmacao nao abriu"
    md.response(Gtk.ResponseType.OK)
    # apos responder, o fluxo continua e grava o argv; agenda o proximo cenario
    schedule(700, "chmod via formulario (cancel)", s10_chmod_cancel)


def s10_chmod_cancel():
    expect = [sys.executable, "-m", "lunuz", "chmod", "755", "script.sh"]
    assert recorded[2] == expect, f"argv chmod errado: {recorded[2:3]}"
    print("   -> confirmacao OK gerou o comando chmod")
    cat, its = items_of("utils")
    schedule(600, "confirm CANCEL", s11_do_confirm_cancel)
    win.on_item_clicked(None, cat, its["u-chmod"])


def s11_do_confirm_cancel():
    form = find_form("Permiss")
    assert form is not None, "segundo formulario chmod nao abriu"
    schedule(500, "confirm CANCEL responde", s12_respond_cancel)
    form.response(Gtk.ResponseType.OK)


def s12_respond_cancel():
    md = find_msgdialog()
    assert md is not None, "confirmacao (cancel) nao abriu"
    md.response(Gtk.ResponseType.CANCEL)
    schedule(800, "final", s13_final)


done = {"v": False}


def s13_final():
    if done["v"]:
        return False
    done["v"] = True
    # cancel NAO deve ter gerado execucao extra
    assert len(recorded) == 3, f"esperava 3 execucoes (cancel nao conta), gravou {len(recorded)}: {recorded}"
    print("   -> confirmacao CANCEL nao executou nada")
    # screenshot final
    try:
        gw = win.get_window()
        wpx = win.get_allocated_width()
        hpx = win.get_allocated_height()
        pb = Gdk.pixbuf_get_from_window(gw, 0, 0, wpx, hpx)
        pb.savev("/tmp/dlg_result.png", "png", [], [])
        print("   -> screenshot salvo")
    except Exception as e:
        print(f"   (screenshot falhou: {e})")
    if errors:
        print("\nFALHAS:")
        print("\n".join(errors))
    else:
        print("\n=== TODOS OS TESTES DE DIALOGO PASSARAM ===")
    app.quit()


def s_timeout():
    if not done["v"]:
        done["v"] = True
        print("TIMEOUT - passo nao completou")
        if errors:
            print("\n".join(errors))
        app.quit()
    return False


app.connect("activate", on_activate)
GLib.timeout_add(25000, s_timeout)  # rede de seguranca
sys.exit(app.run(None))
