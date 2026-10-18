"""Persistent game notes and reusable note templates."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from theme_manager import ThemeManager

BUILTIN_TEMPLATES = {
    "Walk Through": """Game:\nArea / chapter:\nCurrent objective:\n\nSteps\n1. \n2. \n3. \n\nImportant characters / items:\n\nBosses or challenges:\n\nNext steps:\n""",
    "Hidden Treasure Notes": """Game:\nRegion / level:\nTreasure name:\n\nClues found:\n- \n\nLocation / map reference:\n\nHow to reach it:\n1. \n2. \n\nRequirements (keys, skills, quests):\n\nCollected: No\n""",
    "Blank Template": "",
}


class GameNotesStore:
    """Read and safely save notes and user-editable templates."""

    def __init__(self, storage_path: Optional[Path] = None):
        appearance_path = ThemeManager._default_settings_path()
        self.storage_path = storage_path or appearance_path.with_name("game-notes.json")
        self.notes: List[Dict[str, str]] = []
        self.templates: Dict[str, str] = {}
        self._load()

    def template_names(self) -> List[str]:
        return list(BUILTIN_TEMPLATES) + sorted(self.templates, key=str.casefold)

    def load_template(self, name: str) -> str:
        if name in BUILTIN_TEMPLATES:
            return BUILTIN_TEMPLATES[name]
        if name in self.templates:
            return self.templates[name]
        raise KeyError(f"Template not found: {name}")

    def save_template(self, name: str, body: str) -> None:
        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Enter a name for the template")
        if cleaned_name in BUILTIN_TEMPLATES:
            raise ValueError("Built-in templates cannot be overwritten. Save it with a new name instead.")
        if len(cleaned_name) > 80:
            raise ValueError("Template names must be 80 characters or fewer")
        self.templates[cleaned_name] = body
        self._save()

    def delete_template(self, name: str) -> None:
        if name in BUILTIN_TEMPLATES:
            raise ValueError("Built-in templates cannot be deleted")
        if name not in self.templates:
            raise KeyError(f"Template not found: {name}")
        del self.templates[name]
        self._save()

    def save_note(self, title: str, body: str, note_id: Optional[str] = None) -> Dict[str, str]:
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError("Give the note a title before saving")
        if len(cleaned_title) > 120:
            raise ValueError("Note titles must be 120 characters or fewer")
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        note = {
            "id": note_id or uuid.uuid4().hex,
            "title": cleaned_title,
            "body": body,
            "updated": timestamp,
        }
        for index, saved_note in enumerate(self.notes):
            if saved_note["id"] == note["id"]:
                self.notes[index] = note
                self._save()
                return dict(note)
        self.notes.append(note)
        self._save()
        return dict(note)

    def get_note(self, note_id: str) -> Dict[str, str]:
        for note in self.notes:
            if note["id"] == note_id:
                return dict(note)
        raise KeyError(f"Note not found: {note_id}")

    def delete_note(self, note_id: str) -> None:
        remaining = [note for note in self.notes if note["id"] != note_id]
        if len(remaining) == len(self.notes):
            raise KeyError(f"Note not found: {note_id}")
        self.notes = remaining
        self._save()

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.storage_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps({"notes": self.notes, "templates": self.templates}, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary_path, self.storage_path)

    def _load(self) -> None:
        try:
            saved = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(saved, dict):
            return
        saved_notes = saved.get("notes", [])
        if isinstance(saved_notes, list):
            for note in saved_notes:
                if not isinstance(note, dict):
                    continue
                note_id = note.get("id")
                title = note.get("title")
                body = note.get("body")
                updated = note.get("updated", "")
                if all(isinstance(value, str) for value in (note_id, title, body, updated)):
                    self.notes.append({"id": note_id, "title": title, "body": body, "updated": updated})
        saved_templates = saved.get("templates", {})
        if isinstance(saved_templates, dict):
            self.templates = {
                name: body
                for name, body in saved_templates.items()
                if isinstance(name, str)
                and name.strip()
                and name not in BUILTIN_TEMPLATES
                and isinstance(body, str)
            }