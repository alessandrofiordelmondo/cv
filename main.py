#!/usr/bin/env python3
import json, subprocess, shutil
from pathlib import Path
from datetime import date
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output'
TEMPLATE = ROOT / 'template'
JSON_PATH = ROOT / 'cv.json'

MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']


def parse_date(value):
    if not value:
        return None
    return date.fromisoformat(str(value).strip())


def fmt_date(value, ongoing=False):
    d = parse_date(value)
    if not d:
        return 'ongoing' if ongoing else ''
    return f'{d.day:02d} {MONTHS[d.month-1]} {d.year}'


def fmt_range(start, end=None, ongoing=False):
    a = fmt_date(start)
    if ongoing:
        b = 'ongoing'
    elif end:
        b = fmt_date(end)
    else:
        b = ''
    if not a:
        return b
    if not b:
        return a
    return f'{a} – {b}'


def fmt_month_date(value):
    d = parse_date(value)
    if not d:
        return ''
    return f'{MONTHS[d.month-1]} {d.year}'


def fmt_month_range(start, end=None, ongoing=False):
    a = fmt_month_date(start)
    if ongoing:
        b = 'ongoing'
    elif end:
        b = fmt_month_date(end)
    else:
        b = ''
    if not a:
        return b
    if not b:
        return a
    return f'{a} – {b}'


def fmt_day(value):
    d = parse_date(value)
    if not d:
        return ''
    return f'{d.day:02d} {MONTHS[d.month-1]} {d.year}'


def latex_escape(s):
    if s is None:
        return ''
    s = str(s)
    replacements = {
        '\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
        '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
        '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
    }
    return ''.join(replacements.get(ch, ch) for ch in s)


def prepare(data):
    p = data['personal']
    p['birthDateFormatted'] = fmt_day(p.get('birthDate'))
    p['bioText'] = p.get('bio', {}).get('en', '')
    p['website'] = 'https://alessandrofiordelmondo.github.io'  # present in source PDF; absent from JSON

    data['educationResearch'].sort(key=lambda e: str(e.get('startDate') or '').strip(), reverse=True)
    for e in data['educationResearch']:
        e['dateFormatted'] = fmt_range(e.get('startDate'), e.get('endDate'), e.get('ongoing', False))
        e['fieldText'] = ', '.join(e.get('fielOfStudy', []))
        desc = e.get('description') or {}
        e['descriptionPrimary'] = desc.get('primary', []) if isinstance(desc, dict) else desc
        e['descriptionSecondary'] = desc.get('secondary', '') if isinstance(desc, dict) else ''

    data['otherWorkExperience'].sort(key=lambda e: str(e.get('startDate') or '').strip(), reverse=True)
    for e in data['otherWorkExperience']:
        e['dateFormatted'] = fmt_range(e.get('startDate'), e.get('endDate'), e.get('ongoing', False))

    data['teaching'].sort(key=lambda e: str(e.get('startDate') or '').strip(), reverse=True)
    for e in data['teaching']:
        e['dateFormatted'] = fmt_range(e.get('startDate'), e.get('endDate'), e.get('endDate') is None)
        e['academicYears'] = ' | '.join(e.get('academic_year', []))

    data['exhibition'].sort(key=lambda e: str(e.get('startDate') or '').strip(), reverse=True)
    for e in data['exhibition']:
        e['dateFormatted'] = fmt_range(e.get('startDate'), e.get('endDate'), e.get('ongoing', False))
        e.get('replicas', []).sort(
            key=lambda r: str((r.get('date') or [''])[0]).strip(),
            reverse=True,
        )
        for r in e.get('replicas', []):
            dates = r.get('date', [])
            r['dateFormatted'] = fmt_day(dates[0]) if dates else ''

    data['talks'].sort(key=lambda e: str(e.get('startDate') or '').strip(), reverse=True)
    for e in data['talks']:
        e['dateFormatted'] = fmt_range(e.get('startDate'), e.get('endDate'), e.get('ongoing', False))

    data['publication'].sort(
        key=lambda e: (int(e.get('year') or 0), int(e.get('month') or 0)),
        reverse=True,
    )
    for e in data['publication']:
        e['citationAuthors'] = ', '.join(e.get('author', []))
        bits = []
        if e.get('year'):
            bits.append(str(e['year']))
        title = e.get('title', '')
        container = ''
        if e.get('journal'):
            container = f"In {e['journal']}"
            if e.get('volume'):
                container += f" {e['volume']}"
            if e.get('number'):
                container += f"({e['number']})"
            if e.get('publisher'):
                container += f", {e['publisher']}"
        elif e.get('booktitle'):
            container = f"In {e['booktitle']}"
            if e.get('conference'):
                container += f", {e['conference']}"
        elif e.get('conference'):
            container = e['conference']
        e['citation'] = f"{e['citationAuthors']}. {e.get('year','')}. {title}." + (f" {container}" if container else '')

    data['creativeWork'].sort(key=lambda e: int(e.get('year') or 0), reverse=True)
    for e in data['creativeWork']:
        e['description'] = e.get('descritpion', '')

    data['archive'].sort(
        key=lambda e: str(e.get('startDate') or e.get('updateDate') or '').strip(),
        reverse=True,
    )
    for e in data['archive']:
        e['dateFormatted'] = fmt_range(e.get('startDate'), e.get('updateDate')) if e.get('startDate') else ''

    return data


def main():
    OUT.mkdir(exist_ok=True)
    data = prepare(json.loads(JSON_PATH.read_text(encoding='utf-8')))
    env = Environment(loader=FileSystemLoader(str(TEMPLATE)), autoescape=False, keep_trailing_newline=True, variable_start_string='[[', variable_end_string=']]', comment_start_string='<#', comment_end_string='#>')
    env.filters['latex'] = latex_escape
    env.filters['month_range'] = fmt_month_range
    tex = env.get_template('cv.tex.j2').render(cv=data)
    tex_path = OUT / 'main.tex'
    tex_path.write_text(tex, encoding='utf-8')

    if not shutil.which('xelatex'):
        raise SystemExit('xelatex not found')

    cmd = ['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', 'main.tex']
    for _ in range(2):
        result = subprocess.run(cmd, cwd=OUT, text=True, capture_output=True)
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            raise SystemExit(result.returncode)

    print(OUT / 'main.pdf')


if __name__ == '__main__':
    main()
