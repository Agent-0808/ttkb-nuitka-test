"""ttkbootstrap 2.2.7 × Nuitka compatibility demo window.

Covers the capabilities most likely to break under Nuitka freezing:
- Theme switching (``theme_use`` / ``toggle_theme``)
- Widget styling with various bootstyle options
- Built-in Bootstrap Icons (depends on the ``bootstrap.ttf`` glyph font)
- Style queries (``lookup`` / ``theme_settings``)
- Reading the app's own bundled assets
"""

from __future__ import annotations

import json
import sys
from importlib import resources
from importlib.resources.abc import Traversable
from tkinter import PhotoImage
from typing import Any

import ttkbootstrap as ttk

APP_TITLE = "ttkbootstrap × Nuitka Compatibility Demo"
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_BODY = ("Segoe UI", 9)

#: Glyph names used to verify the icon font is available (all exist in the bootstrap-icons glyph table)
ICON_GLYPHS = (
    "gear-fill",
    "heart-fill",
    "house-door-fill",
    "arrow-clockwise",
    "moon-stars-fill",
    "sun-fill",
    "palette-fill",
    "check-circle-fill",
    "x-circle-fill",
    "info-circle-fill",
    "folder-fill",
    "search",
    "bell-fill",
    "person-fill",
    "terminal-fill",
    "cpu-fill",
    "bug-fill",
    "box-seam-fill",
)


def _asset(name: str) -> Traversable:
    """Locate the app's own assets.

    Uses importlib.resources instead of joining paths onto ``__file__``: under
    Nuitka onefile the source directory does not exist, and only the resource
    API can reach the unpacked data files.
    """
    return resources.files("ttkb_demo") / "assets" / name


def _read_info() -> dict[str, Any]:
    return json.loads(_asset("demo_info.json").read_text(encoding="utf-8"))


class DemoApp(ttk.App):
    """Demo main window."""

    def __init__(self) -> None:
        super().__init__(
            title=APP_TITLE,
            theme="bootstrap-dark",
            size=(1020, 700),
            minsize=(940, 640),
        )
        self.info = _read_info()
        self.logo = self._load_logo()
        self.theme_var = ttk.StringVar(value=self.style.theme_use())
        self.status_var = ttk.StringVar(value="Ready")
        self.use_nuitka = ttk.BooleanVar(value=True)
        self.progress_var = ttk.IntVar(value=0)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_header()
        self._build_body()
        self._build_footer()
        self.refresh_diagnostics()

    # ---------- UI construction ----------

    def _load_logo(self) -> PhotoImage:
        # as_file unpacks bundled resources to a real path; PhotoImage reads it
        # once, after which the temp file can be safely released
        with resources.as_file(_asset("logo.png")) as path:
            return PhotoImage(file=str(path))

    def _build_header(self) -> None:
        header = ttk.Frame(self, bootstyle="primary", padding=(16, 12))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, image=self.logo, bootstyle="inverse-primary").grid(
            row=0, column=0, rowspan=2, padx=(0, 14)
        )
        ttk.Label(
            header,
            text=str(self.info["name"]),
            font=FONT_TITLE,
            bootstyle="inverse-primary",
        ).grid(row=0, column=1, sticky="w")
        ttk.Label(
            header,
            text=str(self.info["purpose"]),
            font=FONT_BODY,
            bootstyle="inverse-primary",
        ).grid(row=1, column=1, sticky="w", pady=(2, 0))

        theme_box = ttk.Frame(header, bootstyle="primary")
        theme_box.grid(row=0, column=2, rowspan=2, sticky="e")
        ttk.Label(theme_box, text="Theme", bootstyle="inverse-primary").grid(
            row=0, column=0, padx=(0, 6)
        )
        self.theme_combo = ttk.Combobox(
            theme_box,
            textvariable=self.theme_var,
            values=list(self.style.theme_names()),
            state="readonly",
            width=22,
            bootstyle="primary",
        )
        self.theme_combo.grid(row=0, column=1)
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_selected)
        ttk.Button(
            theme_box,
            text="Light/Dark",
            image=ttk.Icon("moon-stars-fill", size=16, color="light"),
            compound="left",
            command=self._toggle_theme,
            bootstyle="secondary-outline",
        ).grid(row=0, column=2, padx=(8, 0))

    def _build_body(self) -> None:
        body = ttk.Frame(self, padding=(16, 12))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3, uniform="col")
        body.columnconfigure(1, weight=4, uniform="col")
        body.rowconfigure(0, weight=1)

        self._build_controls(body)
        self._build_notebook(body)

    def _build_controls(self, parent: ttk.Frame) -> None:
        box = ttk.Labelframe(parent, text="bootstyle widgets", bootstyle="info", padding=12)
        box.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="Plain entry", bootstyle="info").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(box, bootstyle="primary").grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(box, text="Read-only combobox", bootstyle="info").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(
            box,
            values=["Nuitka", "PyInstaller", "Source run"],
            state="readonly",
            bootstyle="info",
        ).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(box, text="Spinbox", bootstyle="info").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Spinbox(box, from_=1, to=999, bootstyle="primary").grid(
            row=2, column=1, sticky="ew", pady=4
        )

        ttk.Checkbutton(
            box,
            text="Enable round-toggle switch",
            variable=self.use_nuitka,
            bootstyle="round-toggle",
            command=lambda: self._set_status(f"Toggle state: {self.use_nuitka.get()}"),
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=6)

        radio_row = ttk.Frame(box)
        radio_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)
        radio_var = ttk.StringVar(value="onefile")
        for index, (text, value) in enumerate((("onefile", "onefile"), ("standalone", "standalone"))):
            ttk.Radiobutton(
                radio_row,
                text=text,
                value=value,
                variable=radio_var,
                bootstyle="primary",
            ).grid(row=0, column=index, padx=(0, 16))

        ttk.Label(box, text="Progress bar", bootstyle="info").grid(row=5, column=0, sticky="w", pady=4)
        ttk.Progressbar(
            box,
            variable=self.progress_var,
            maximum=100,
            bootstyle="success-striped",
        ).grid(row=5, column=1, sticky="ew", pady=4)

        ttk.Label(box, text="Scale", bootstyle="info").grid(row=6, column=0, sticky="w", pady=4)
        scale = ttk.Scale(box, from_=0, to=100, value=35, bootstyle="warning")
        scale.grid(row=6, column=1, sticky="ew", pady=4)
        self.scale_label = ttk.Label(box, text="35", bootstyle="warning")
        self.scale_label.grid(row=6, column=2, padx=(8, 0))
        scale.configure(command=lambda value: self.scale_label.configure(text=f"{float(value):.0f}"))

        button_row = ttk.Frame(box)
        button_row.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Button(
            button_row,
            text="Run progress animation",
            image=ttk.Icon("arrow-clockwise", size=16),
            compound="left",
            command=self._run_progress,
            bootstyle="success",
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(
            button_row,
            text="Danger action",
            image=ttk.Icon("x-circle-fill", size=16),
            compound="left",
            command=lambda: self._set_status("This is a danger-style button (no-op)"),
            bootstyle="danger-outline",
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(
            button_row,
            text="Refresh diagnostics",
            image=ttk.Icon("arrow-clockwise", size=16),
            compound="left",
            command=self.refresh_diagnostics,
            bootstyle="secondary-outline",
        ).grid(row=0, column=2)

        ttk.Separator(box).grid(row=8, column=0, columnspan=3, sticky="ew", pady=(14, 10))

        ttk.Label(
            box,
            text="Note: every widget above uses bootstyle instead of native ttk style names.\n"
            "If bootstyle breaks after Nuitka packaging, widgets fall back to the default gray look.",
            font=FONT_BODY,
            bootstyle="secondary",
            justify="left",
        ).grid(row=9, column=0, columnspan=3, sticky="w")

    def _build_notebook(self, parent: ttk.Frame) -> None:
        self.notebook = ttk.Notebook(parent, bootstyle="primary")
        self.notebook.grid(row=0, column=1, sticky="nsew")

        tree_tab = ttk.Frame(self.notebook, padding=10)
        tree_tab.columnconfigure(0, weight=1)
        tree_tab.rowconfigure(0, weight=1)
        self.notebook.add(tree_tab, text="Treeview", image=ttk.Icon("folder-fill", size=14))

        columns = ("name", "kind", "note")
        self.tree = ttk.Treeview(
            tree_tab,
            columns=columns,
            show="headings",
            height=8,
            bootstyle="primary",
        )
        for column, title, width in (
            ("name", "Name", 140),
            ("kind", "Kind", 110),
            ("note", "Notes", 260),
        ):
            self.tree.heading(column, text=title)
            self.tree.column(column, width=width, anchor="w")
        for row in (
            ("themes/builtin.py", "Python module", "2.x themes ship as modules with the package"),
            ("assets/icons/bootstrap.ttf", "Font resource", "Actual carrier of the icon glyphs"),
            ("assets/icons/glyphmap.json", "JSON resource", "Glyph name to codepoint mapping"),
            ("assets/elements/*.png", "Image resource", "Element assets such as checkboxes/scales"),
        ):
            self.tree.insert("", "end", values=row)
        self.tree.grid(row=0, column=0, sticky="nsew")

        icons_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(icons_tab, text="Built-in icons", image=ttk.Icon("heart-fill", size=14))
        self.icon_grid = ttk.Frame(icons_tab)
        self.icon_grid.grid(row=0, column=0, sticky="nw")
        self._populate_icons()

        style_tab = ttk.Frame(self.notebook, padding=10)
        style_tab.columnconfigure(0, weight=1)
        style_tab.rowconfigure(0, weight=1)
        self.notebook.add(style_tab, text="Style queries", image=ttk.Icon("palette-fill", size=14))
        self.diagnostics = ttk.Treeview(
            style_tab,
            columns=("key", "value"),
            show="headings",
            bootstyle="info",
        )
        self.diagnostics.heading("key", text="Item")
        self.diagnostics.heading("value", text="Value")
        self.diagnostics.column("key", width=180, anchor="w")
        self.diagnostics.column("value", width=360, anchor="w")
        self.diagnostics.grid(row=0, column=0, sticky="nsew")

    def _build_footer(self) -> None:
        footer = ttk.Frame(self, padding=(16, 8))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, bootstyle="secondary").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            footer,
            text=f"ttkbootstrap {ttk.__version__} · Python {sys.version.split()[0]}",
            bootstyle="secondary",
        ).grid(row=0, column=1, sticky="e")

    def _populate_icons(self) -> None:
        for child in self.icon_grid.winfo_children():
            child.destroy()
        for index, glyph in enumerate(ICON_GLYPHS):
            cell = ttk.Frame(self.icon_grid, padding=6)
            cell.grid(row=index // 6, column=index % 6, sticky="n")
            ttk.Label(cell, image=ttk.Icon(glyph, size=26, color="primary")).grid(row=0, column=0)
            ttk.Label(cell, text=glyph, font=FONT_BODY, bootstyle="secondary").grid(row=1, column=0)

    # ---------- Interaction ----------

    def _on_theme_selected(self, _event: object | None = None) -> None:
        name = self.theme_var.get()
        self.style.theme_use(name)
        self._after_theme_change(f"Theme switched to: {name}")

    def _toggle_theme(self) -> None:
        self.style.toggle_theme()
        self.theme_var.set(self.style.theme_use())
        self._after_theme_change(f"Light/dark mode toggled: {self.style.theme_use()}")

    def _after_theme_change(self, message: str) -> None:
        self.style.clear_image_cache()
        self._populate_icons()
        self.refresh_diagnostics()
        self._set_status(message)

    def _run_progress(self) -> None:
        value = self.progress_var.get()
        value = 0 if value >= 100 else value + 4
        self.progress_var.set(value)
        if value < 100:
            self.after(40, self._run_progress)
        else:
            self._set_status("Progress animation complete (after event loop works)")

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    # ---------- Diagnostics ----------

    def refresh_diagnostics(self) -> None:
        style = self.style
        rows = (
            ("Run mode", "Nuitka compiled" if "__compiled__" in globals() else "CPython interpreter"),
            ("Python", sys.version.split()[0]),
            ("ttkbootstrap", ttk.__version__),
            ("Current theme", style.theme_use()),
            ("Theme mode", str(style.theme_mode)),
            ("Available themes", str(len(style.theme_names()))),
            ("TButton.background", str(style.lookup("TButton", "background"))),
            ("TButton.foreground", str(style.lookup("TButton", "foreground"))),
            ("TLabel.foreground", str(style.lookup("TLabel", "foreground"))),
            ("TEntry.fieldbackground", str(style.lookup("TEntry", "fieldbackground"))),
            ("TNotebook.background", str(style.lookup("TNotebook", "background"))),
            ("Icon font resource", self._icon_font_status()),
            ("App resources", f"logo.png {len(_asset('logo.png').read_bytes())} B · demo_info.json loaded"),
        )
        self.diagnostics.delete(*self.diagnostics.get_children())
        for key, value in rows:
            self.diagnostics.insert("", "end", values=(key, value))

    @staticmethod
    def _icon_font_status() -> str:
        icon_dir = resources.files("ttkbootstrap") / "assets" / "icons"
        font = icon_dir / "bootstrap.ttf"
        glyphmap = icon_dir / "glyphmap.json"
        if not font.is_file():
            return "Missing: bootstrap.ttf not included in the build"
        glyph_count = len(json.loads(glyphmap.read_text(encoding="utf-8"))) if glyphmap.is_file() else 0
        return f"OK: {len(font.read_bytes()) // 1024} KiB, {glyph_count} glyphs"


def main() -> None:
    DemoApp().mainloop()


if __name__ == "__main__":
    main()
