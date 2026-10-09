"""Read-only input inventory and OOXML cell extraction for plan 2.2."""
import argparse
import hashlib
import json
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'m': M}
SOURCES = {
    'S01': ('01-UTF-8-Q-E7-AC-AC-EF-BC-92-E5-9B-9E-2Exlsx-1', 'libfile_2f275b2a53d481919fb7d942fbecc486'),
    'S02': ('04-UTF-8-Q-E7-AC-AC-EF-BC-91-E5-9B-9E-2Exlsx-1', 'libfile_0d9cfee943ec819188518e4922ce620e'),
    'S03': ('03-R5-1-.xlsx', 'libfile_1a33a04a77e4819197bfdf49e7cd8099'),
    'S04': ('07-file-7', 'libfile_348a1421657c8191938bc42e4a79b9ea'),
    'S05': ('06-manual-1-.pdf', 'libfile_f40c9f4e1d0081919fb497f31e737856'),
    'S06': ('02-Tool_v1.3-1-1-.xls', 'libfile_b7623c4ffd6881919e938f89942286f3'),
    'S04_alias': ('05-R5-1', 'libfile_d66db96b3c5881919cf10890068434de'),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def workbook_cells(path):
    with zipfile.ZipFile(path) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(n.itertext()) if False else ''.join(t.text or '' for t in n.iter('{'+M+'}t'))
                       for n in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rels = {r.attrib['Id']: posixpath.normpath(posixpath.join('xl', r.attrib['Target'])).lstrip('/')
                for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        sheets = []
        for sheet in wb.find('m:sheets', NS):
            part = rels[sheet.attrib['{'+R+'}id']]
            root = ET.fromstring(z.read(part))
            cells = {}
            for c in root.findall('.//m:sheetData/m:row/m:c', NS):
                v, f = c.find('m:v', NS), c.find('m:f', NS)
                raw = v.text if v is not None else None
                typ = c.get('t', 'n')
                val = raw
                if typ == 's' and raw is not None:
                    val = strings[int(raw)]
                elif typ == 'inlineStr':
                    val = ''.join(t.text or '' for t in c.iter('{'+M+'}t'))
                elif typ == 'n' and raw is not None:
                    val = float(raw)
                    if val == int(val): val = int(val)
                if val is not None or f is not None:
                    cells[c.get('r')] = {'value': val, 'type': typ, 'style': c.get('s'),
                                         'formula': f.text if f is not None else None,
                                         'formula_attributes': dict(f.attrib) if f is not None else None}
            sheets.append({'name': sheet.get('name'), 'part': part, 'state': sheet.get('state','visible'),
                           'dimension': (root.find('m:dimension', NS).get('ref') if root.find('m:dimension',NS) is not None else None),
                           'cells': cells,
                           'merges': [m.get('ref') for m in root.findall('m:mergeCells/m:mergeCell', NS)],
                           'print_xml': {tag: ET.tostring(root.find('m:'+tag,NS),encoding='unicode')
                                         for tag in ['pageMargins','pageSetup','printOptions','rowBreaks','colBreaks'] if root.find('m:'+tag,NS) is not None},
                           'hidden_rows': [r.get('r') for r in root.findall('m:sheetData/m:row',NS) if r.get('hidden')=='1'],
                           'hidden_cols': [dict(c.attrib) for c in root.findall('m:cols/m:col',NS) if c.get('hidden')=='1']})
        charts = [p for p in z.namelist() if re.fullmatch(r'xl/charts/chart\d+\.xml',p)]
        return {'sheets': sheets, 'chart_count': len(charts),
                'part_hashes': {p:sha(z.read(p)) for p in z.namelist()},
                'defined_names': [{'attrs':dict(n.attrib),'text':n.text} for n in wb.findall('m:definedNames/m:definedName',NS)]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--sources',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    manifest={}
    for sid,(filename,library_id) in SOURCES.items():
        path=args.sources/filename
        data=path.read_bytes()
        entry={'library_file_id':library_id,'workspace_path':str(path.resolve()),'sha256':sha(data),'size_bytes':len(data)}
        if sid in {'S01','S02','S03'}:
            wb=workbook_cells(path)
            write_json(args.out/(sid+'_cells.json'), wb)
            entry.update({'sheet_count':len(wb['sheets']),'chart_count':wb['chart_count'],
                          'sheets':[{'name':s['name'],'dimension':s['dimension'],'state':s['state'],
                                     'populated_cells':len(s['cells']),'formula_cells':sum(c['formula_attributes'] is not None for c in s['cells'].values())} for s in wb['sheets']]})
            lines=[]
            for s in wb['sheets']:
                lines.append('\n### '+s['name'])
                rows={}
                for cell,c in s['cells'].items():
                    rows.setdefault(int(re.search(r'\d+',cell).group()),[]).append(cell+'='+str(c['value']).replace('\n',' / '))
                for row,values in sorted(rows.items()):
                    lines.append(' ; '.join(values))
            (args.out/(sid+'_rows.txt')).write_text('\n'.join(lines),encoding='utf-8')
        elif sid in {'S04','S04_alias'}:
            with zipfile.ZipFile(path) as z:
                root=ET.fromstring(z.read('word/document.xml'))
                wn={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                text='\n'.join(''.join(t.text or '' for t in x.findall('.//w:t',wn)) for x in root.findall('.//w:p',wn))
                (args.out/(sid+'_text.txt')).write_text(text,encoding='utf-8')
        manifest[sid]=entry
    manifest['environment']={'python':sys.version,'extraction':'standard library OOXML; original bytes are never rewritten'}
    write_json(args.out/'input_manifest.json',manifest)
    print(json.dumps({k:{x:v[x] for x in ('sha256','sheet_count','chart_count') if x in v} for k,v in manifest.items() if k!='environment'},ensure_ascii=False))

if __name__=='__main__': main()
