# STARz Booklet Maker

A desktop application for converting PDF documents into print-ready booklet PDFs.

## Features

- Import PDF documents.
- Browse pages in a scrollable thumbnail grid.
- Select which pages to include in the booklet.
- Select all pages, clear the selection, or select odd/even pages.
- Select pages using page ranges or specific page numbers.
- Adjust thumbnail preview quality from 10% to 100%.
- Choose Light, Dark, or System Default appearance.
- Customize the accent color.
- Generate an A4 landscape PDF with two page areas side by side.
- Automatically add blank pages when needed for booklet imposition.

**Note:** The thumbnail quality setting affects only on-screen previews. It does not reduce the quality of the generated PDF.

## Booklet page order

The app arranges selected pages so the printed sheets can be folded into a booklet. For example, an eight-page booklet is arranged as follows:

| Output side | Left page | Right page |
|---|---:|---:|
| Sheet 1 — Front | 8 | 1 |
| Sheet 1 — Back | 2 | 7 |
| Sheet 2 — Front | 6 | 3 |
| Sheet 2 — Back | 4 | 5 |

If the number of selected pages is not divisible by four, blank pages are added automatically.

## Download

For a ready-to-use Windows version, visit the repository's **Releases** page and download the executable attached to the release you want.

Each release is versioned separately, so you can choose a previous release if you need an older version. GitHub also provides source-code archives for tagged releases.

## Run from source

### Requirements

- Python 3.10 or newer
- PySide6
- PyMuPDF

### Setup

1. Download or clone this repository.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment (recommended):

   **Windows Command Prompt:**
   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   ```

4. Install the dependencies:
   ```bat
   python -m pip install PySide6 PyMuPDF
   ```

5. Run the application:
   ```bat
   python main.py
   ```

Keep `main.py` and `booklet_engine.py` in the same folder.

## Build a Windows executable

To create a Windows executable yourself, install PyInstaller:

```bat
python -m pip install pyinstaller
```

Then run:

```bat
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "STARz Booklet Maker" main.py
```

The executable should be created in the `dist` folder. Test the executable before distributing it.

## Project files

- `main.py` — application interface and workflow.
- `booklet_engine.py` — booklet page-imposition logic.
- `README.md` — project documentation.

## Releases and version history

The latest source code is maintained in the repository. Published releases contain the downloadable Windows executable for that version. To access an earlier version's source code, open the corresponding tagged release and use GitHub's source-code archive.

## License

No license has been specified yet. Unless a license is added to this repository, the default copyright rules apply and others do not automatically receive permission to redistribute or modify the code.
