import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lunuz import gui
from gi.repository import Gtk, GLib

recorded = []
errors = []

# ---- patches: nao executar de verdade, so gravar ----
gui.LunuzWindow.run_argv = lambda self, argv, pretty=None: recorded.append(list(argv))
gui.LunuzWindow.confirm = lambda self, item: True
gui.LunuzWindow.confirm_batch = lambda self, cat, items: True
Gtk.Dialog.run = lambda self: Gtk.ResponseType.OK
Gtk.FileChooserDialog.run = lambda self: Gtk.ResponseType.OK
Gtk.FileChooserDialog.get_filename = lambda self: "/tmp/arquivo_teste.py"

app = gui.LunuzApp()
win = gui.LunuzWindow(app)
win.show_all()
win.back_btn.set_visible(False)


def test_all():
    try:
        # 1. Todos os tiles abrem a pagina certa (categoria ou terminal)
        for cat in gui.CATEGORIES:
            win.on_tile_clicked(None, cat)
            esperado = "terminal" if cat["id"] == "terminal" else "category"
            assert win.stack.get_visible_child_name() == esperado, \
                f"tile {cat['id']} abriu {win.stack.get_visible_child_name()}"
            assert win.back_btn.get_visible(), "back nao apareceu"
            if cat["id"] != "terminal":
                assert len(win.cat_box.get_children()) >= len(cat["items"]) + 1, "itens faltando"
            # volta para a home para o proximo tile
            win.back_btn.emit("clicked")
            assert win.stack.get_visible_child_name() == "home", "voltar falhou"
            assert not win.back_btn.get_visible(), "back continuou visivel"
        print(f"OK 1: {len(gui.CATEGORIES)} tiles abriram (categorias + aba terminal)")

        # 2. BOTAO VOLTAR (bug reportado)
        win.open_category(gui.CATEGORIES[0])
        assert win.stack.get_visible_child_name() == "category"
        win.back_btn.emit("clicked")   # <- clicou de verdade
        assert win.stack.get_visible_child_name() == "home", "voltar nao foi para home"
        assert not win.back_btn.get_visible(), "back continuou visivel na home"
        print("OK 2: botao voltar leva para home e se esconde")

        # 3. Busca partindo de categoria -> limpar restaura categoria
        # (search-chilled tem delay de 150ms no GTK; invocamos o handler direto)
        win.open_category(gui.CATEGORIES[0])
        win.search.set_text("kernel")
        win.on_search(win.search)
        assert win.stack.get_visible_child_name() == "search", "busca nao foi para search"
        assert win.back_btn.get_visible()
        win.search.set_text("")
        win.on_search(win.search)
        assert win.stack.get_visible_child_name() == "category", "limpar busca nao restaurou categoria"
        print("OK 3: limpar busca restaura a categoria anterior")

        # 4. Busca -> botao voltar -> pagina anterior -> home
        win.search.set_text("nvidia")
        win.on_search(win.search)
        assert win.stack.get_visible_child_name() == "search"
        win.back_btn.emit("clicked")   # 1o voltar: volta p/ categoria de origem
        assert win.stack.get_visible_child_name() == "category", "voltar da busca nao foi para a categoria"
        assert win.search.get_text() == "", "voltar nao limpou a busca"
        assert win.back_btn.get_visible(), "back sumiu na categoria"
        win.back_btn.emit("clicked")   # 2o voltar: home
        assert win.stack.get_visible_child_name() == "home", "2o voltar nao foi para home"
        assert not win.back_btn.get_visible(), "back continuou visivel na home"
        print("OK 4: busca -> voltar -> categoria -> voltar -> home")

        # 5. Busca sem resultados
        win.search.set_text("zzzznaoexiste999")
        win.on_search(win.search)
        assert win.stack.get_visible_child_name() == "search"
        kids = [c for c in win.search_box.get_children()]
        assert kids, "sem nada na pagina de resultados"
        win.search.set_text("")
        win.on_search(win.search)
        assert win.stack.get_visible_child_name() == "home"
        print("OK 5: busca sem resultados ok")

        # 6. Toggles grade/lista (comportamento radio)
        assert win.btn_grid.get_active() and not win.btn_list.get_active()
        win.btn_list.emit("toggled") if False else win.btn_list.set_active(True)
        assert not win.btn_grid.get_active() and win.btn_list.get_active(), "list nao ativou"
        # desmarcar o ativo deve ser impedido
        win.btn_list.set_active(False)
        assert win.btn_list.get_active(), "permitiu ficar sem nenhum modo ativo"
        # voltar para grade
        win.btn_grid.set_active(True)
        assert win.btn_grid.get_active() and not win.btn_list.get_active()
        print("OK 6: toggles grade/lista com radio garantido")

        # 7. Executar TODOS os itens: os disponíveis executam, os de outra
        #    distro são bloqueados (diálogo) e NÃO geram execução
        n_items = sum(len(c["items"]) for c in gui.CATEGORIES)
        bloqueados = []
        for cat in gui.CATEGORIES:
            win.open_category(cat)
            for item in cat["items"]:
                antes7 = len(recorded)
                win.on_item_clicked(None, cat, item)
                if gui.item_available(item):
                    assert len(recorded) == antes7 + 1, \
                        f"{item['id']} deveria executar"
                else:
                    assert len(recorded) == antes7, \
                        f"{item['id']} indisponivel executou mesmo assim"
                    bloqueados.append(item["id"])
        n_disp = n_items - len(bloqueados)
        assert len(recorded) == n_disp, \
            f"esperava {n_disp} execucoes, gravou {len(recorded)}"
        print(f"OK 7: {n_disp}/{n_items} itens executaram; "
              f"bloqueados nesta distro: {bloqueados or 'nenhum'}")

        # 7b. Identificador de distro: chip na home com contagem certa
        win.show_page("home")
        assert win.distro_chip.get_visible(), "chip da distro nao visivel"

        def _texts(w):
            out = []
            if isinstance(w, Gtk.Label):
                out.append(w.get_text())
            for ch in (w.get_children() if isinstance(w, Gtk.Container) else []):
                out += _texts(ch)
            return out

        chip_txt = " | ".join(_texts(win.distro_chip))
        total7 = sum(len(c["items"]) for c in gui.CATEGORIES)
        ok7 = sum(1 for c in gui.CATEGORIES for it in c["items"]
                  if gui.item_available(it))
        assert f"{ok7} de {total7} ações disponíveis" in chip_txt, chip_txt
        assert gui.FAMILY_NAMES.get(gui.detect_distro()["family"], "") in chip_txt
        print(f"OK 7b: chip mostra '{ok7} de {total7} ações disponíveis'")

        # 7c. Linha indisponível: badge "só em ..." + classe unavail + clique
        #     abre diálogo em vez de executar
        ker = next(c for c in gui.CATEGORIES
                   if any(it["id"] == "k-zen" for it in c["items"]))
        win.open_category(ker)
        rows = [ch for ch in win.cat_box.get_children()
                if isinstance(ch, Gtk.Button)
                and ch.get_style_context().has_class("itemrow")]
        assert len(rows) == len(ker["items"]), "linhas nao batem com itens"
        kzen = next(it for it in ker["items"] if it["id"] == "k-zen")
        zrow = rows[ker["items"].index(kzen)]
        if gui.item_available(kzen):
            assert not zrow.get_style_context().has_class("unavail")
            print("OK 7c: k-zen disponivel nesta distro (sem badge)")
        else:
            assert zrow.get_style_context().has_class("unavail"), \
                "linha indisponivel sem classe unavail"
            ztxt = " ".join(_texts(zrow))
            assert "só em" in ztxt, f"badge ausente: {ztxt}"
            antes7c = len(recorded)
            win.on_item_clicked(None, ker, kzen)
            assert len(recorded) == antes7c, "indisponivel executou!"
            print("OK 7c: k-zen bloqueado com badge 'só em ...' e diálogo")

        # 8. find tem -name
        find_argv = [a for a in recorded if "-name" in a]
        assert find_argv, "find gerado sem -name (bug do formulario)"
        assert find_argv[0][find_argv[0].index("-name") + 1], "padrao vazio"
        print(f"OK 8: find usa -name -> {' '.join(find_argv[0][2:])}")

        # 9. scripts root usam pkexec, info nao
        root_runs = [a for a in recorded if a and a[0] == "pkexec"]
        plain_bash = [a for a in recorded if a and a[0] == "/bin/bash"]
        assert root_runs and plain_bash, f"root={len(root_runs)} plain={len(plain_bash)}"
        print(f"OK 9: {len(root_runs)} acoes root via pkexec, {len(plain_bash)} sem root")

        # 10. checagem extra: nenhum argv vazio
        for a in recorded:
            assert a and all(isinstance(p, str) and p for p in a), f"argv invalido: {a}"

        # 11. Aba Terminal: o widget se move para a pagina dedicada e volta
        win.show_page("terminal")
        assert win.stack.get_visible_child_name() == "terminal"
        assert win.terminal.get_parent() is win.term_host, "terminal nao foi para a aba"
        assert win.bot_hint.get_visible(), "aviso do painel inferior nao apareceu"
        win.show_page("home")
        assert win.terminal.get_parent() is win.term_box, "terminal nao voltou ao painel"
        assert not win.bot_hint.get_visible(), "aviso continuou visivel"
        print("OK 11: aba Terminal recebe/devolve o terminal")

        # 12. Selecao multipla
        sys_cat = next(c for c in gui.CATEGORIES if c["id"] == "system")
        win.open_category(sys_cat)
        win.multi_toggle.set_active(True)          # ativa o modo (re-renderiza)
        assert win.multi_mode and win.sel_bar.get_visible(), "barra de acao nao apareceu"
        assert not win.btn_run_sel.get_sensitive(), "botao deveria iniciar inativo"
        antes = len(recorded)
        shell_items = [i for i in sys_cat["items"] if i.get("kind") in ("shell", "info")]
        assert len(shell_items) >= 2, "categoria system sem itens suficientes"
        # item de formulario no modo multi nao executa
        form_cat = next(c for c in gui.CATEGORIES if c["id"] == "utils")
        win.open_category(form_cat)
        form_item = next(i for i in form_cat["items"] if i.get("kind") == "form")
        win.on_item_clicked(None, form_cat, form_item)
        assert len(recorded) == antes, "form executou no modo multi!"
        assert "manual" in win.status_lbl.get_text(), "aviso de manual ausente"
        # volta para system e seleciona 2
        win.open_category(sys_cat)
        win.multi_toggle.set_active(True)
        for it in shell_items[:2]:
            win.on_item_clicked(None, sys_cat, it)
        assert len(win.selected_ids) == 2, f"selecao: {win.selected_ids}"
        assert win.sel_count_lbl.get_text() == "2 selecionado(s)", win.sel_count_lbl.get_text()
        assert win.btn_run_sel.get_sensitive(), "botao executar continua inativo"
        # executa a leva (confirm_batch e confirm sao patches -> True)
        win.on_run_selected()
        assert len(recorded) == antes + 2, f"esperava +2, total {len(recorded)}"
        assert len(win.selected_ids) == 0, "selecao nao foi limpa apos executar"
        assert win.batch is None or win.batch["total"] == 2, "lote nao registrado"
        # desliga o modo
        win.multi_toggle.set_active(False)
        assert not win.multi_mode and not win.sel_bar.get_visible(), "modo nao desligou"
        print("OK 12: selecao multipla seleciona, executa em lote e limpa")

    except Exception:
        import traceback
        errors.append(traceback.format_exc())
    finally:
        if errors:
            print("FALHAS:")
            print(errors[0])
        else:
            print("\n=== TODOS OS TESTES PASSARAM ===")
        app.quit()


GLib.timeout_add(400, test_all)
sys.exit(app.run(None))
