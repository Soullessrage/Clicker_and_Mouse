"""Dedicated game-notes editor with reusable templates."""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Optional

from notes_manager import BUILTIN_TEMPLATES, GameNotesStore
from theme_manager import ThemeManager


class GameNotesWindow:
    """Edit walkthroughs and game notes in their own persistent window."""

    def __init__(self, master: tk.Tk, theme: ThemeManager):
        self.theme = theme
        self.store = GameNotesStore()
        self.window = tk.Toplevel(master)
        self.window.title("Game Notes")
        self.window.geometry("920x680")
        self.window.minsize(760, 540)
        self.window.transient(master)
        self.window.configure(background=self.theme.colors()["background"])
        self._note_id: Optional[str] = None
        self._build()
        self._refresh_notes()

    def _build(self) -> None:
        colors = self.theme.colors("canvas")
        style = ttk.Style(self.window)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "GameNotes.TCombobox",
            fieldbackground=colors["panel_highlight"],
            background=colors["panel"],
            foreground=colors["text"],
            arrowcolor=colors["accent"],
            padding=6,
        )

        outer = tk.Frame(self.window, background=colors["background"], padx=18, pady=16)
        outer.pack(fill=tk.BOTH, expand=True)
        heading = tk.Frame(outer, background=colors["background"])
        heading.pack(fill=tk.X, pady=(0, 12))
        tk.Label(
            heading,
            text="Game Notes",
            background=colors["background"],
            foreground=colors["text"],
            font=self._font(18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            heading,
            text="Save your discoveries, route plans, and walkthrough steps locally.",
            background=colors["background"],
            foreground=colors["muted"],
            font=self._font(10),
        ).pack(anchor="w", pady=(3, 0))

        body = tk.Frame(outer, background=colors["background"])
        body.pack(fill=tk.BOTH, expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        saved_panel = tk.Frame(
            body,
            background=colors["panel"],
            padx=10,
            pady=10,
            highlightthickness=1,
            highlightbackground=colors["accent"],
        )
        saved_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(
            saved_panel,
            text="SAVED NOTES",
            background=colors["panel"],
            foreground=colors["accent"],
            font=self._font(9, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.note_list = tk.Listbox(
            saved_panel,
            width=25,
            activestyle="none",
            background=colors["panel_highlight"],
            foreground=colors["text"],
            selectbackground=colors["accent"],
            selectforeground=colors["text"],
            relief=tk.FLAT,
            highlightthickness=0,
            font=self._font(10),
        )
        self.note_list.pack(fill=tk.BOTH, expand=True)
        self.note_list.bind("<<ListboxSelect>>", self._load_selected_note)
        self._action_button(saved_panel, "New Blank Note", self._new_note, colors).pack(fill=tk.X, pady=(8, 0))
        self._action_button(saved_panel, "Delete Note", self._delete_note, colors).pack(fill=tk.X, pady=(5, 0))

        editor = tk.Frame(
            body,
            background=colors["panel"],
            padx=14,
            pady=12,
            highlightthickness=1,
            highlightbackground=colors["accent"],
        )
        editor.grid(row=0, column=1, sticky="nsew")
        editor.columnconfigure(0, weight=1)
        editor.rowconfigure(3, weight=1)

        tk.Label(
            editor,
            text="NOTE TITLE",
            background=colors["panel"],
            foreground=colors["muted"],
            font=self._font(8, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self.title_entry = tk.Entry(
            editor,
            background=colors["panel_highlight"],
            foreground=colors["text"],
            insertbackground=colors["text"],
            relief=tk.FLAT,
            font=self._font(11),
        )
        self.title_entry.grid(row=1, column=0, sticky="ew", pady=(4, 12), ipady=7)

        template_row = tk.Frame(editor, background=colors["panel"])
        template_row.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        template_row.columnconfigure(0, weight=1)
        self.template_var = tk.StringVar(value="Walk Through")
        self.template_box = ttk.Combobox(
            template_row,
            textvariable=self.template_var,
            values=self.store.template_names(),
            state="readonly",
            style="GameNotes.TCombobox",
        )
        self.template_box.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._action_button(template_row, "Load Template", self._load_template, colors).grid(row=0, column=1)

        text_frame = tk.Frame(editor, background=colors["panel"])
        text_frame.grid(row=3, column=0, sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.body_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            undo=True,
            background=colors["panel_highlight"],
            foreground=colors["text"],
            insertbackground=colors["text"],
            selectbackground=colors["accent"],
            relief=tk.FLAT,
            padx=12,
            pady=10,
            font=self._font(10),
        )
        self.body_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.body_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.body_text.configure(yscrollcommand=scrollbar.set)

        template_actions = tk.Frame(editor, background=colors["panel"])
        template_actions.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self._action_button(template_actions, "Save as Template", self._save_template, colors).pack(side=tk.LEFT)
        self._action_button(template_actions, "Delete Custom Template", self._delete_template, colors).pack(
            side=tk.LEFT,
            padx=(6, 0),
        )

        footer = tk.Frame(outer, background=colors["background"])
        footer.pack(fill=tk.X, pady=(10, 0))
        self.status_label = tk.Label(
            footer,
            text="Notes are saved on this computer.",
            background=colors["background"],
            foreground=colors["muted"],
            anchor="w",
            font=self._font(9),
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._action_button(footer, "Save Note", self._save_note, colors, primary=True).pack(side=tk.RIGHT)

    def _font(self, size: int, weight: str = "normal"):
        family = self.theme.font_family
        if family == "System Default":
            from tkinter import font as tkfont

            family = tkfont.nametofont("TkDefaultFont").actual("family")
        return family, size, weight

    @staticmethod
    def _action_button(parent, text, command, colors, primary: bool = False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=7,
            background=colors["accent"] if primary else colors["panel_highlight"],
            foreground=colors["text"],
            activebackground=colors["accent_alt"],
            activeforeground=colors["text"],
            font=("TkDefaultFont", 9, "bold"),
            cursor="hand2",
        )

    def _refresh_notes(self, select_id: Optional[str] = None) -> None:
        self.note_list.delete(0, tk.END)
        self._visible_note_ids = []
        for note in sorted(self.store.notes, key=lambda item: item["updated"], reverse=True):
            self.note_list.insert(tk.END, note["title"])
            self._visible_note_ids.append(note["id"])
        self.template_box.configure(values=self.store.template_names())
        if select_id in self._visible_note_ids:
            index = self._visible_note_ids.index(select_id)
            self.note_list.selection_set(index)
            self.note_list.activate(index)

    def _load_selected_note(self, _event: tk.Event) -> None:
        selection = self.note_list.curselection()
        if not selection:
            return
        note = self.store.get_note(self._visible_note_ids[selection[0]])
        self._note_id = note["id"]
        self._set_editor(note["title"], note["body"])
        self._set_status(f"Loaded '{note['title']}'. Save edits to keep them.")

    def _set_editor(self, title: str, body: str) -> None:
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, title)
        self.body_text.delete("1.0", tk.END)
        self.body_text.insert("1.0", body)

    def _new_note(self) -> None:
        self._note_id = None
        self.note_list.selection_clear(0, tk.END)
        self._set_editor("", "")
        self._set_status("Blank note ready.")
        self.title_entry.focus_set()

    def _load_template(self) -> None:
        name = self.template_var.get()
        if not name:
            self._set_status("Choose a template first.")
            return
        self._note_id = None
        self.note_list.selection_clear(0, tk.END)
        self._set_editor(name if name != "Blank Template" else "", self.store.load_template(name))
        self._set_status(f"Loaded '{name}'. Edit it freely, then save as a note or template.")

    def _save_note(self) -> None:
        try:
            note = self.store.save_note(
                self.title_entry.get(),
                self.body_text.get("1.0", "end-1c"),
                self._note_id,
            )
        except ValueError as error:
            messagebox.showwarning("Save note", str(error), parent=self.window)
            return
        self._note_id = note["id"]
        self._refresh_notes(select_id=self._note_id)
        self._set_status(f"Saved '{note['title']}'.")

    def _delete_note(self) -> None:
        if not self._note_id:
            self._set_status("Select a saved note to delete.")
            return
        if not messagebox.askyesno("Delete note", "Delete this saved note?", parent=self.window):
            return
        self.store.delete_note(self._note_id)
        self._new_note()
        self._refresh_notes()
        self._set_status("Note deleted.")

    def _save_template(self) -> None:
        current_name = self.template_var.get()
        initial_name = "" if current_name in BUILTIN_TEMPLATES else current_name
        name = simpledialog.askstring(
            "Save template",
            "Template name:",
            initialvalue=initial_name,
            parent=self.window,
        )
        if name is None:
            return
        try:
            self.store.save_template(name, self.body_text.get("1.0", "end-1c"))
        except ValueError as error:
            messagebox.showwarning("Save template", str(error), parent=self.window)
            return
        self.template_var.set(name.strip())
        self._refresh_notes(select_id=self._note_id)
        self._set_status(f"Template '{name.strip()}' saved. You can edit and save it again anytime.")

    def _delete_template(self) -> None:
        name = self.template_var.get()
        if name in BUILTIN_TEMPLATES:
            self._set_status("Built-in templates cannot be deleted; save an edited copy under a new name.")
            return
        if not name:
            self._set_status("Choose a custom template to delete.")
            return
        if not messagebox.askyesno("Delete template", f"Delete the custom template '{name}'?", parent=self.window):
            return
        self.store.delete_template(name)
        self.template_var.set("Walk Through")
        self._refresh_notes(select_id=self._note_id)
        self._set_status("Custom template deleted.")

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)