#!/usr/bin/env python3
"""lunuz tools - internacionalizacao (i18n).

- Detecta automaticamente o idioma do sistema (LANG/LC_ALL/LC_MESSAGES)
  e aplica o idioma correspondente na interface.
- O usuario pode trocar o idioma nas Configuracoes (engrenagem) da GUI;
  a escolha fica salva em ~/.config/lunuz/settings.json.
- Ingles (EUA) e o idioma padrao quando o sistema nao e reconhecido.

Idiomas suportados: en_US (padrao), en_GB, en_AU, pt_BR, pt_PT, ru,
ja, zh_CN, de, ko, vi.
"""

import json
import os

# ------------------------------------------------------------------
# Idiomas suportados (codigo, nome nativo, bandeira)
# ------------------------------------------------------------------
LANGUAGES = [
    ("en_US", "English (US)", "\U0001f1fa\U0001f1f8"),
    ("en_GB", "English (UK)", "\U0001f1ec\U0001f1e7"),
    ("en_AU", "English (Australia)", "\U0001f1e6\U0001f1fa"),
    ("pt_BR", "Português (Brasil)", "\U0001f1e7\U0001f1f7"),
    ("pt_PT", "Português (Portugal)", "\U0001f1f5\U0001f1f9"),
    ("ru",    "Русский", "\U0001f1f7\U0001f1fa"),
    ("ja",    "日本語", "\U0001f1ef\U0001f1f5"),
    ("zh_CN", "中文（简体）", "\U0001f1e8\U0001f1f3"),
    ("de",    "Deutsch", "\U0001f1e9\U0001f1ea"),
    ("ko",    "한국어", "\U0001f1f0\U0001f1f7"),
    ("vi",    "Tiếng Việt", "\U0001f1fb\U0001f1f3"),
]

DEFAULT_LANGUAGE = "en_US"

# ------------------------------------------------------------------
# Deteccao do idioma do sistema
# ------------------------------------------------------------------
def _normalize(code):
    """Normaliza 'pt_BR.utf8'/'en-GB' -> 'pt_br'/'en_gb'."""
    return (code or "").split(".")[0].split("@")[0].strip().replace("-", "_").lower()


def detect_system_language():
    """Detecta o idioma do sistema e devolve um codigo suportado.

    Ordem: variavel LUNUZ_LANG (override p/ testes/dev) > LC_ALL >
    LC_MESSAGES > LANG > locale padrao do Python. Cai para en_US se
    o idioma nao for suportado.
    """
    # override explicito (dev/testes) tem prioridade maxima
    override = os.environ.get("LUNUZ_LANG")
    if override:
        return map_to_supported(override)

    raw = ""
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val and val not in ("C", "POSIX"):
            raw = val
            break
    if not raw:
        try:
            import locale
            raw = locale.getdefaultlocale()[0] or ""
        except Exception:
            raw = ""
    return map_to_supported(raw)


def map_to_supported(raw):
    """Mapeia qualquer codigo BCP47/POSIX para um idioma suportado."""
    code = _normalize(raw)
    if not code:
        return DEFAULT_LANGUAGE
    # correspondencias exatas primeiro
    known = {c.lower(): c for c, _n, _f in LANGUAGES}
    if code in known:
        return known[code]
    lang = code.split("_")[0]
    region = code.split("_")[1] if "_" in code else ""
    if lang == "pt":
        return "pt_BR" if region != "pt" else "pt_PT"
    if lang == "en":
        if region == "gb":
            return "en_GB"
        if region == "au":
            return "en_AU"
        return "en_US"
    if lang == "zh":
        return "zh_CN"
    if lang in ("ru", "ja", "de", "ko", "vi"):
        return lang
    return DEFAULT_LANGUAGE


# ------------------------------------------------------------------
# Persistencia da escolha do usuario
# ------------------------------------------------------------------
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "lunuz")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")


def _load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                return data
    except (OSError, ValueError):
        pass
    return {}


def _save_config(data):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass


def get_language_setting():
    """'auto' ou codigo fixo escolhido nas Configuracoes."""
    return _load_config().get("language", "auto")


def set_language(setting):
    """Salva a escolha: 'auto' ou um codigo de LANGUAGES."""
    global _current
    valid = [c for c, _n, _f in LANGUAGES]
    if setting != "auto" and setting not in valid:
        setting = "auto"
    cfg = _load_config()
    cfg["language"] = setting
    _save_config(cfg)
    _current = None  # invalida cache


def get_language():
    """Codigo efetivo do idioma em uso (detectado ou escolhido)."""
    global _current
    if _current is not None:
        return _current
    setting = get_language_setting()
    lang = detect_system_language() if setting == "auto" else setting
    _current = lang
    return lang


_current = None  # cache do idioma efetivo (None = ainda nao calculado)


# ------------------------------------------------------------------
# Traducoes da interface (chrome)
# ------------------------------------------------------------------
from .ui_translations import UI, CATEGORY_NAMES, FIELD_LABELS


def t(key, **kwargs):
    """Traduz uma chave da interface no idioma atual (com formatacao)."""
    lang = get_language()
    table = UI.get(lang) or UI[DEFAULT_LANGUAGE]
    text = table.get(key) or UI[DEFAULT_LANGUAGE].get(key) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass
    return text


def tr_cat(cat):
    """Nome da categoria no idioma atual."""
    lang = get_language()
    names = CATEGORY_NAMES.get(cat.get("id", ""), {})
    return names.get(lang) or names.get("en_US") or cat.get("name", "")


def tr_item(item):
    """(nome, descricao) do item no idioma atual; cai para o padrao.

    O texto canonico em actions.py ja esta em pt_BR, entao esse idioma
    nao precisa de tabela em item_translations.ITEMS.
    """
    lang = get_language()
    if lang == "pt_BR":
        return item.get("name", ""), item.get("desc", "")
    from .item_translations import ITEMS
    table = ITEMS.get(lang) or ITEMS.get(DEFAULT_LANGUAGE) or {}
    pair = table.get(item.get("id", ""))
    if pair:
        return pair
    return item.get("name", ""), item.get("desc", "")


def tr_field(label):
    """Rotulo de campo de formulario no idioma atual."""
    lang = get_language()
    opts = FIELD_LABELS.get(label, {})
    return opts.get(lang) or opts.get("en_US") or label


def language_display_name(code):
    for c, name, flag in LANGUAGES:
        if c == code:
            return f"{flag} {name}"
    return code
