# Alessandro Fiordelmondo CV generator — reconstructed

This project is a first working reconstruction of the CV generator inferred from the supplied `cv.json` and signed PDF.

## Pipeline

```text
cv.json
  ↓
main.py / Jinja2
  ↓
output/main.tex
  ↓
XeLaTeX
  ↓
output/main.pdf
```

## Run

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

The generated PDF is written to `output/main.pdf`.

## Reconstructed rules

- A4 format with 10 mm left/right margins.
- Arial is the font family used by the supplied PDF. The current reconstruction uses **Arimo** because Arial is not installed in the build environment; change `\\setmainfont{Arimo}` to `\\setmainfont{Arial}` on a system where Arial is available.
- Body text is approximately 8.5 pt with 11.9 pt leading.
- The main two-column entries use a 42 mm date/location column and a flexible content column.
- Publications use a full-width layout; URLs use a monospaced style, matching the embedded `LMMono8-Regular` font observed in the source PDF.
- Section order follows the source PDF: about me → education & research experience → publications → teaching → exhibitions → invited talks, seminars & workshops → other work experience → GDPR statement.
- Chronological sections are sorted newest-first to match the PDF.
- Dates are formatted as `Mon YYYY`, with `Present` for ongoing entries.
- The website URL is taken from the PDF because it is not present in `cv.json`.
- Image fields in the JSON are retained but are not rendered because the supplied signed PDF is text-only.

## Known reconstruction limits

This is not yet a byte-for-byte reproduction of the original source. The main remaining differences are exact font metrics, fine spacing, some entry-specific rendering rules (`exhibition.style`), and the precise page-break algorithm.
