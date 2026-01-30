# git-local – Design Dokument

## Übersicht

Eine minimalistische Web-App zur Übersicht und Navigation lokaler Git-Repositories. Zeigt alle Projekte in `/Users/olivier/Versioncontrol/local` mit Status, Branch-Info und Schnellzugriff auf VS Code/Terminal.

## Anforderungen

- Alle Git-Repos in einem Verzeichnis scannen und auflisten
- Pro Repo: Name, Branch, Status (clean/dirty), letzter Commit, Anzahl Branches
- Schnellzugriff: VS Code öffnen, Terminal öffnen, Finder öffnen
- Remote-URL anzeigen (falls vorhanden)
- Standalone mit uv – kein Docker/DDEV nötig

## Design-Prinzipien

Orientiert am Look & Feel der Letter App:

- **Monochrom:** Schwarz, Weiß, Graustufen – keine Farben
- **Clean:** Viel Whitespace, klare Typografie, scharfe Kanten
- **Minimalistisch:** Nur das Nötigste, keine Ablenkung

---

## Tech-Stack

| Komponente | Technologie |
|------------|-------------|
| Backend | Python 3.11+ mit FastAPI |
| Frontend | HTMX + Jinja2 Templates |
| Styling | Custom CSS (Letter-Style) |
| Git-Operationen | GitPython |
| Package Manager | uv |

---

## Projektstruktur

```
git-local/
├── pyproject.toml
├── src/
│   └── git_local/
│       ├── __init__.py
│       ├── main.py          # FastAPI app, routes
│       ├── git_scanner.py   # Repository discovery & info
│       ├── templates/
│       │   ├── base.html
│       │   ├── index.html   # Projekt-Übersicht
│       │   └── components/
│       │       └── repo_list.html  # HTMX partial
│       └── static/
│           └── style.css
├── docs/
│   └── plans/
│       └── 2026-01-30-git-local-design.md
└── README.md
```

---

## API-Endpunkte

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/` | HTML-Seite mit Projekt-Übersicht |
| GET | `/api/repos` | JSON mit allen Repos |
| GET | `/partials/repos` | HTMX partial für Repo-Liste |
| POST | `/api/open/vscode/{name}` | VS Code öffnen |
| POST | `/api/open/terminal/{name}` | Terminal öffnen |
| POST | `/api/open/finder/{name}` | Finder öffnen |

---

## Datenmodell

### Repository Info

```python
@dataclass
class RepoInfo:
    name: str                    # Ordnername
    path: str                    # Absoluter Pfad
    branch: str                  # Aktueller Branch
    is_dirty: bool               # Hat uncommitted changes
    dirty_count: int             # Anzahl uncommitted files
    branch_count: int            # Anzahl lokaler Branches
    last_commit_message: str     # Letzte Commit-Message
    last_commit_date: datetime   # Letztes Commit-Datum
    last_commit_relative: str    # "vor 3 Tagen"
    remote_url: str | None       # Remote URL (falls vorhanden)
```

---

## Benutzeroberfläche

### Visuelles Konzept (Letter-Style)

**CSS-Variablen:**
```css
--black: #000;
--gray-900: #111;
--gray-700: #333;
--gray-600: #555;
--gray-500: #777;
--gray-400: #999;
--gray-200: #ddd;
--gray-100: #f5f5f5;
--white: #fff;
```

**Typografie:**
- System Font Stack
- Uppercase Labels mit Letter-Spacing
- Klare Hierarchie

**Elemente:**
- Keine abgerundeten Ecken
- 1px Borders
- Großzügige Abstände (8px-Raster)

### Hauptansicht

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  GIT LOCAL                               [↻] [⚙]       │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  24 Repositories                                        │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  claude-insights-agent                                  │
│  main · clean · 2 branches                             │
│  "Add webhook support" · vor 3 Tagen                   │
│                                        [📁] [VS]       │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  letter                                                 │
│  main · 2 uncommitted · 1 branch                       │
│  "Improve export modal" · vor 1 Tag                    │
│                                        [📁] [VS]       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Header-Aktionen

| Button | Funktion |
|--------|----------|
| [↻] | Refresh/Rescan aller Repos |
| [⚙] | Settings (Pfad konfigurieren) |

### Repo-Aktionen

| Button | Funktion |
|--------|----------|
| [📁] | Im Finder öffnen |
| [VS] | In VS Code öffnen |
| [>_] | Terminal öffnen (optional) |

### Status-Anzeige

- `clean` – Keine uncommitted changes (grau, unauffällig)
- `2 uncommitted` – Dirty state (dunkler, auffälliger)

---

## Dark Mode

Automatisch via `prefers-color-scheme: dark`:

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #0d0d0d;
    --color-fg: #f0f0f0;
    /* ... */
  }
}
```

---

## Starten der App

```bash
cd git-local
uv run fastapi dev src/git_local/main.py
```

Öffnet auf `http://localhost:8000`

---

## Spätere Erweiterungen (nicht in v1)

- Terminal-UI (TUI) als Alternative
- Commit-Historie anzeigen
- Branch-Diff-Ansicht
- Suche/Filter
- Mehrere Scan-Verzeichnisse

---

## Zusammenfassung

| Aspekt | Entscheidung |
|--------|--------------|
| Framework | FastAPI + HTMX |
| Styling | Monochrom (Letter-Style) |
| Git-Lib | GitPython |
| Package Manager | uv |
| Aktionen | VS Code, Terminal, Finder öffnen |
| Dark Mode | Ja, automatisch |
