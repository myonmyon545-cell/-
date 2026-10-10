"""Isolate existing affected page blocks for native print QA only.

Paths are caller-supplied; --check-paths-only does not open an Excel package.
"""
import argparse
import json
import zipfile
from pathlib import Path
from lxml import etree as E

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
AREAS = {
    'Ⅳ事務データ': '$A$181:$AC$238',
    'Ⅱ調査項目データ（第５群）': '$A$63:$AD$121',
    'Ⅲ審査判定データ（変更率）': '$A$61:$AD$120,$A$361:$AD$543',
}

def resolve_paths(base, out):
    """Resolve CLI paths once and reject source overwrite or output reuse."""
    base = base.expanduser().resolve(strict=True)
    out = out.expanduser().resolve()
    if not base.is_file():
        raise ValueError('base must be an existing file')
    if base == out:
        raise ValueError('output must not overwrite the input')
    if out.exists():
        raise ValueError('output already exists; choose a new output path')
    return base, out

def create_probe(base, out):
    # Original page-selection logic is retained. Native rendering/recalculation
    # is not performed by this entry point.
    with zipfile.ZipFile(base) as src:
        root = E.fromstring(src.read('xl/workbook.xml'))
        node = root.find('m:sheets', NS)
        old = list(node)
        kept = [s for s in old if s.get('name') in AREAS]
        old_to_new = {old.index(s): i for i, s in enumerate(kept)}
        node[:] = kept
        for s in kept:
            s.set('state', 'visible')
        names = root.find('m:definedNames', NS)
        for n in list(names):
            idx = int(n.get('localSheetId', '-1'))
            if idx not in old_to_new:
                names.remove(n)
                continue
            n.set('localSheetId', str(old_to_new[idx]))
            if n.get('name') == '_xlnm.Print_Area':
                n.text = ','.join("'" + old[idx].get('name') + "'!" + r
                                  for r in AREAS[old[idx].get('name')].split(','))
        view = root.find('m:bookViews/m:workbookView', NS)
        view.set('activeTab', '0')
        view.set('firstSheet', '0')
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, 'x', zipfile.ZIP_DEFLATED) as dest:
            for n in src.namelist():
                data = (E.tostring(root, encoding='UTF-8', xml_declaration=True)
                        if n == 'xl/workbook.xml' else src.read(n))
                dest.writestr(n, data)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True,
                        help='Existing read-only workbook; relative paths use the caller cwd')
    parser.add_argument('--out', type=Path, required=True,
                        help='New probe path; never the base or an existing file')
    parser.add_argument('--check-paths-only', action='store_true',
                        help='Validate paths only; no Excel read, write, rendering or recalculation')
    args = parser.parse_args()
    try:
        base, out = resolve_paths(args.base, args.out)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if not args.check_paths_only:
        create_probe(base, out)
    print(json.dumps({'base': str(base), 'out': str(out),
                      'mode': 'paths_only' if args.check_paths_only else 'probe_created'},
                     ensure_ascii=False))

if __name__ == '__main__':
    main()
