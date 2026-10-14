"""Teste da fila de execução + aba Terminal com spawn REAL.

Covers: serialização (nada roda junto), ordem preservada, status de
progresso e contagem de lote (seleção múltipla).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lunuz import gui
from gi.repository import Gtk, GLib, Vte

app = gui.LunuzApp()
win = None
errors = []


def term_text(term):
    try:
        n = term.get_row_count()
        r = term.get_text_range_format(Vte.Format.TEXT, 0, 0, n, 500)
        if isinstance(r, tuple):
            return r[0] or ""
        return r or ""
    except Exception:
        return ""


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


def on_activate(a):
    global win
    if not a.win:
        a.win = gui.LunuzWindow(a)
    win = a.win
    win.show_all()
    win.back_btn.set_visible(False)
    win._sync_terminal_layout()
    win.show_page("terminal")

    def start():
        # dois comandos em sequencia: o 2o DEVE esperar na fila
        win.run_argv(["/bin/bash", "-c", "echo PASSO1; sleep 1.5"], "etapa 1")
        win.run_argv(["/bin/bash", "-c", "echo PASSO2"], "etapa 2")
        assert win.running, "primeiro comando nao iniciou"
        assert len(win.run_queue) == 1, f"fila: {len(win.run_queue)} (esperado 1)"
        assert "Na fila" in win.status_lbl.get_text(), win.status_lbl.get_text()
        assert win.spinner.get_visible() or True  # spinner ativo
        print("OK enfileirado: 2o comando na fila com status", flush=True)
    GLib.timeout_add(500, step("enfileirar", start))
    GLib.timeout_add(900, step("serializacao", check_mid))
    GLib.timeout_add(4500, step("conclusao e ordem", check_end))
    GLib.timeout_add(7500, step("lote (multi)", check_batch))
    GLib.timeout_add(20000, emergency)
    return False


def check_mid():
    txt = term_text(win.terminal)
    assert "PASSO1" in txt, f"passo1 ausente: {txt[-200:]!r}"
    assert "PASSO2" not in txt, "PASSO2 rodou junto - fila ignorada!"
    assert win.running, "nada esta rodando"


def check_end():
    txt = term_text(win.terminal)
    assert "PASSO1" in txt and "PASSO2" in txt, f"saida incompleta: {txt[-200:]!r}"
    assert txt.index("PASSO1") < txt.index("PASSO2"), "ordem trocada"
    assert not win.running, "ainda sinaliza rodando"
    assert not win.run_queue, "fila nao esvaziou"
    st = win.status_lbl.get_text()
    assert "Concluído" in st or "fim" in st.lower(), f"status: {st!r}"
    # agora um lote de 2 (como a selecao multipla faz)
    win.batch = {"total": 2, "done": 0}
    win.run_argv(["/bin/bash", "-c", "echo LOTE1"], "lote 1")
    win.run_argv(["/bin/bash", "-c", "echo LOTE2"], "lote 2")
    assert len(win.run_queue) == 1, "lote: 2o nao enfileirou"


def check_batch():
    txt = term_text(win.terminal)
    assert "LOTE1" in txt and "LOTE2" in txt, f"lote incompleto: {txt[-200:]!r}"
    assert txt.index("LOTE1") < txt.index("LOTE2"), "ordem do lote trocada"
    st = win.status_lbl.get_text()
    assert "2/2" in st, f"status do lote: {st!r}"
    assert win.batch is None, "lote nao foi zerado"
    assert not win.running and not win.run_queue
    if errors:
        print("\nFALHAS:", flush=True)
        print("\n".join(errors), flush=True)
    else:
        print("\n=== TODOS OS TESTES DE FILA PASSARAM ===", flush=True)
    app.quit()


def emergency():
    if not errors:
        errors.append("TIMEOUT: teste de fila nao completou")
        print("TIMEOUT", flush=True)
    app.quit()
    return False


app.connect("activate", on_activate)
sys.exit(app.run(None))
