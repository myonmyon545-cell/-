"""Package an Artifact Tool-authored summary into an untouched source workbook.

Original sheet/chart/drawing/printer parts are copied verbatim. Only workbook
registration, appended style records and new summary worksheet are changed.
This is a preservation adapter, not a replacement spreadsheet authoring engine.
"""
import argparse
import copy
import json
import posixpath
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as E
from inspect_inputs import M, R, NS, sha, write_json, workbook_cells

def tag(local): return '{'+M+'}'+local
E.register_namespace('', M)
E.register_namespace('r', R)

def xml(root): return E.tostring(root,encoding='utf-8',xml_declaration=True)

def sheets_by_name(z, workbook):
    wb=E.fromstring(z.read(workbook))
    rels={r.get('Id'):posixpath.normpath(posixpath.join('xl',r.get('Target'))).lstrip('/')
          for r in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    return {s.get('name'):rels[s.get('{'+R+'}id')] for s in wb.find('m:sheets',NS)}

def graft(source, donor, output, name='分析要点', corrected_sheet='Ⅰ基礎情報', corrected_range=('G513','G521')):
    with zipfile.ZipFile(source) as sz, zipfile.ZipFile(donor) as dz:
        parts={n:sz.read(n) for n in sz.namelist()}
        wb=E.fromstring(parts['xl/workbook.xml'])
        rels=E.fromstring(parts['xl/_rels/workbook.xml.rels'])
        source_sheets=sheets_by_name(sz,'xl/workbook.xml')
        donor_sheets=sheets_by_name(dz,'xl/workbook.xml')
        donorwb=E.fromstring(dz.read('xl/workbook.xml'))
        donor_sheet=next(s for s in donorwb.find('m:sheets',NS) if s.get('name')==name)
        donor_rels={r.get('Id'):r.get('Target') for r in E.fromstring(dz.read('xl/_rels/workbook.xml.rels'))}
        donor_part=posixpath.normpath(posixpath.join('xl',donor_rels[donor_sheet.get('{'+R+'}id')])).lstrip('/')
        sheet=E.fromstring(dz.read(donor_part))
        if sheet.find('m:drawing',NS) is not None or sheet.find('m:legacyDrawing',NS) is not None:
            raise ValueError('summary drawing requires a separately validated adapter')
        strings=[]
        if 'xl/sharedStrings.xml' in dz.namelist():
            strings=list(E.fromstring(dz.read('xl/sharedStrings.xml')))
        for c in sheet.findall('.//m:c',NS):
            if c.get('t')=='s':
                v=c.find('m:v',NS)
                si=copy.deepcopy(strings[int(v.text)])
                si.tag=tag('is')
                c.remove(v)
                c.append(si)
                c.set('t','inlineStr')
        # The workbook edit itself is authored and recalculated with Artifact
        # Tool. Read only the authorized corrected cells from that donor and
        # apply those values to the untouched source package so charts,
        # formulas, print settings and every other original part stay byte exact.
        first,last=corrected_range
        donor_corrected=E.fromstring(dz.read(donor_sheets[corrected_sheet]))
        refs=[]
        start_col=re.fullmatch(r'([A-Z]+)(\d+)',first)
        end_col=re.fullmatch(r'([A-Z]+)(\d+)',last)
        if not start_col or not end_col or start_col.group(1)!=end_col.group(1):raise ValueError('only a single-column correction range is supported')
        col=start_col.group(1)
        for row in range(int(start_col.group(2)),int(end_col.group(2))+1):refs.append(f'{col}{row}')
        source_corrected=E.fromstring(parts[source_sheets[corrected_sheet]])
        donor_values={}
        for ref in refs:
            c=donor_corrected.find(f'.//m:sheetData/m:row/m:c[@r="{ref}"]',NS)
            v=c.find('m:v',NS) if c is not None else None
            f=c.find('m:f',NS) if c is not None else None
            if c is None or v is None or f is not None or c.get('t','n') not in ['n','t']:
                raise ValueError('donor correction missing or not a plain value: '+ref)
            raw=float(v.text);donor_values[ref]=int(raw) if raw.is_integer() else raw
            target=source_corrected.find(f'.//m:sheetData/m:row/m:c[@r="{ref}"]',NS)
            if target is None or target.find('m:f',NS) is not None:raise ValueError('source correction target missing/formula: '+ref)
            old=target.find('m:v',NS)
            if old is None:old=E.SubElement(target,tag('v'))
            old.text=str(donor_values[ref]);target.set('t','n')
        patch_bytes=xml(source_corrected)
        st=E.fromstring(parts['xl/styles.xml'])
        donorstyles=E.fromstring(dz.read('xl/styles.xml'))
        base_lengths={x:len(st.find('m:'+x,NS)) for x in ['fonts','fills','borders','cellXfs']}
        for kind in ['fonts','fills','borders']:
            dest=st.find('m:'+kind,NS)
            for x in donorstyles.find('m:'+kind,NS): dest.append(copy.deepcopy(x))
            dest.set('count',str(len(dest)))
        original_numfmts=st.find('m:numFmts',NS)
        donor_numfmts=donorstyles.find('m:numFmts',NS)
        fmt_map={}
        if donor_numfmts is not None and len(donor_numfmts):
            if original_numfmts is None:
                original_numfmts=E.Element(tag('numFmts'),{'count':'0'})
                st.insert(0,original_numfmts)
            fmt_codes={x.get('formatCode'):int(x.get('numFmtId')) for x in original_numfmts}
            nextfmt=max([163]+[int(x.get('numFmtId')) for x in original_numfmts])+1
            for x in donor_numfmts:
                old=int(x.get('numFmtId')); code=x.get('formatCode')
                if code not in fmt_codes:
                    y=copy.deepcopy(x); y.set('numFmtId',str(nextfmt)); original_numfmts.append(y)
                    fmt_codes[code]=nextfmt; nextfmt+=1
                fmt_map[old]=fmt_codes[code]
            original_numfmts.set('count',str(len(original_numfmts)))
        dest=st.find('m:cellXfs',NS)
        for xf in donorstyles.find('m:cellXfs',NS):
            y=copy.deepcopy(xf)
            for attr,kind in [('fontId','fonts'),('fillId','fills'),('borderId','borders')]:
                y.set(attr,str(int(y.get(attr,'0'))+base_lengths[kind]))
            if int(y.get('numFmtId','0')) in fmt_map: y.set('numFmtId',str(fmt_map[int(y.get('numFmtId'))]))
            y.set('xfId','0'); dest.append(y)
        dest.set('count',str(len(dest)))
        for c in sheet.findall('.//m:c',NS):
            c.set('s',str(int(c.get('s','0'))+base_lengths['cellXfs']))
        for c in sheet.findall('m:cols/m:col',NS):
            if 'style' in c.attrib: c.set('style',str(int(c.get('style'))+base_lengths['cellXfs']))
        for row in sheet.findall('m:sheetData/m:row',NS):
            if 's' in row.attrib: row.set('s',str(int(row.get('s'))+base_lengths['cellXfs']))
        # Keep the new Japanese summary sheet to a single review page when
        # native office software exports it. This does not touch source-sheet
        # print settings, which remain byte-identical.
        sheetpr=sheet.find('m:sheetPr',NS)
        if sheetpr is None:
            sheetpr=E.Element(tag('sheetPr'))
            sheet.insert(0,sheetpr)
        setup=sheetpr.find('m:pageSetUpPr',NS)
        if setup is None: setup=E.SubElement(sheetpr,tag('pageSetUpPr'))
        setup.set('fitToPage','1')
        margins=E.Element(tag('pageMargins'),{'left':'0.25','right':'0.25','top':'0.35','bottom':'0.35','header':'0.15','footer':'0.15'})
        pagesetup=E.Element(tag('pageSetup'),{'orientation':'landscape','fitToWidth':'1','fitToHeight':'1'})
        for item in [margins,pagesetup]:
            old=sheet.find('m:'+item.tag.split('}')[-1],NS)
            if old is not None: sheet.remove(old)
            sheet.append(item)
        sheet_number=max(int(re.search(r'sheet(\d+)',n).group(1)) for n in parts if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n))+1
        rid='rIdCareSummary'
        if rid in {r.get('Id') for r in rels}: raise ValueError('summary relationship already exists')
        new_part=f'xl/worksheets/sheet{sheet_number}.xml'
        sheet_ids=[int(s.get('sheetId')) for s in wb.find('m:sheets',NS)]
        wb.find('m:sheets',NS).insert(0,E.Element(tag('sheet'),{'name':name,'sheetId':str(max(sheet_ids)+1),'{'+R+'}id':rid}))
        for n in wb.findall('m:definedNames/m:definedName',NS):
            if 'localSheetId' in n.attrib: n.set('localSheetId',str(int(n.get('localSheetId'))+1))
        relns='http://schemas.openxmlformats.org/package/2006/relationships'
        rels.append(E.Element('{'+relns+'}Relationship',{'Id':rid,'Type':R+'/worksheet','Target':'worksheets/sheet'+str(sheet_number)+'.xml'}))
        ct=E.fromstring(parts['[Content_Types].xml'])
        ctns='http://schemas.openxmlformats.org/package/2006/content-types'
        ct.append(E.Element('{'+ctns+'}Override',{'PartName':'/'+new_part,'ContentType':'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'}))
        cp=wb.find('m:calcPr',NS)
        if cp is not None: cp.set('fullCalcOnLoad','1')
        modified={'xl/workbook.xml':xml(wb),'xl/_rels/workbook.xml.rels':xml(rels),
                  'xl/styles.xml':xml(st),'[Content_Types].xml':xml(ct)}
        modified[source_sheets[corrected_sheet]]=patch_bytes
        output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as oz:
            for info in sz.infolist(): oz.writestr(info,modified.get(info.filename,parts[info.filename]))
            oz.writestr(new_part,xml(sheet))
    expected=[66,255,198,432,259,190,230,157,1787]
    if list(donor_values.values())!=expected:raise ValueError('C03 donor values do not match ROLE=20 PASS')
    return verify(source,output,{corrected_sheet:dict(zip(refs,expected))},donor_values)

def verify(source, output, authorized_changes=None, donor_values=None):
    authorized_changes=authorized_changes or {}
    a,b=workbook_cells(source),workbook_cells(output)
    changed_sheet_parts={a_sheet['part'] for a_sheet in a['sheets'] if a_sheet['name'] in authorized_changes}
    allowed={'xl/workbook.xml','xl/_rels/workbook.xml.rels','xl/styles.xml','[Content_Types].xml'}|changed_sheet_parts
    differences=[p for p,h in a['part_hashes'].items() if b['part_hashes'].get(p)!=h]
    if set(differences)!=allowed: raise ValueError('unexpected source part change: '+repr(differences))
    if a['chart_count']!=148 or b['chart_count']!=148: raise ValueError('chart count mismatch')
    if [s['name'] for s in b['sheets'][1:]]!=[s['name'] for s in a['sheets']]: raise ValueError('sheet list/order mismatch')
    for old,new in zip(a['sheets'],b['sheets'][1:]):
        wanted=copy.deepcopy(old)
        for ref,value in authorized_changes.get(old['name'],{}).items():
            if wanted['cells'].get(ref,{}).get('value')==value:raise ValueError('authorized patch did not change '+ref)
            wanted['cells'][ref]['value']=value
        if wanted!=new: raise ValueError('unexpected original sheet change: '+old['name'])
    with zipfile.ZipFile(source) as az,zipfile.ZipFile(output) as bz:
        originalstyles=E.fromstring(az.read('xl/styles.xml'))
        newstyles=E.fromstring(bz.read('xl/styles.xml'))
        for kind in ['fonts','fills','borders','cellXfs','cellStyleXfs','cellStyles','dxfs']:
            x,y=originalstyles.find('m:'+kind,NS),newstyles.find('m:'+kind,NS)
            if x is None: continue
            if y is None or len(y)<len(x): raise ValueError('style container lost: '+kind)
            for left,right in zip(x,y):
                if E.tostring(left)!=E.tostring(right): raise ValueError('original style changed: '+kind)
        for n in bz.namelist():
            if n.endswith('.xml') or n.endswith('.rels'): E.fromstring(bz.read(n))
        before=E.fromstring(az.read('xl/workbook.xml'))
        after=E.fromstring(bz.read('xl/workbook.xml'))
        for left,right in zip(before.findall('m:definedNames/m:definedName',NS),after.findall('m:definedNames/m:definedName',NS)):
            expected=dict(left.attrib)
            if 'localSheetId' in expected: expected['localSheetId']=str(int(expected['localSheetId'])+1)
            if expected!=right.attrib or left.text!=right.text: raise ValueError('defined name changed incorrectly')
    formula_cells_preserved=True
    for old,new in zip(a['sheets'],b['sheets'][1:]):
        allowed_refs=set(authorized_changes.get(old['name'],{}))
        if {k:v for k,v in old['cells'].items() if v['formula'] is not None}!={k:v for k,v in new['cells'].items() if v['formula'] is not None}:
            formula_cells_preserved=False;break
        for ref,v in old['cells'].items():
            if ref not in allowed_refs and new['cells'].get(ref)!=v:formula_cells_preserved=False;break
    if not formula_cells_preserved:raise ValueError('unintended original formulas/caches/cells changed')
    return {'status':'PASS','source_sheet_count':14,'output_sheet_count':15,'chart_count':148,
            'original_sheet_parts_identical_except_authorized_C03_cells':True,'chart_xml_series_axes_layout_identical':True,
            'drawing_and_printer_parts_identical':True,'original_style_records_identical':True,
            'original_formula_and_cached_values_identical_except_authorized_C03_cells':True,'defined_name_sheet_indices_shifted':True,
            'authorized_cell_changes':{sheet:{ref:{'from':a_sheet['cells'][ref]['value'],'to':value} for ref,value in cells.items()} for sheet,cells in authorized_changes.items() for a_sheet in a['sheets'] if a_sheet['name']==sheet},
            'changed_original_parts':differences,'new_parts':sorted(set(b['part_hashes'])-set(a['part_hashes'])),
            'source_sha256':sha(Path(source).read_bytes()),'output_sha256':sha(Path(output).read_bytes()),
            'scope':'OOXML structural preservation with exactly the independently approved C03 changes; visual and application checks are separate'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--donor',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--checks',type=Path,required=True);a=p.parse_args()
    result=graft(a.source,a.donor,a.out);write_json(a.checks,result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
