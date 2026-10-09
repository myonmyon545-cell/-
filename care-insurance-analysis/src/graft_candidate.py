"""Attach Artifact Tool-authored analysis sheets to the verified C03 copy.

Every existing worksheet, chart, drawing, printer and formula part is copied
verbatim. Only workbook registration/style tables and four new sheets change.
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
from preserve_package import tag, xml, sheets_by_name

NEW_SHEETS = ['候補案内', '指標一覧', '比較一覧', '定義・保留']


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source-copy',type=Path,required=True)
    p.add_argument('--donor',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--checks',type=Path,required=True)
    a=p.parse_args()
    with zipfile.ZipFile(a.source_copy) as sz,zipfile.ZipFile(a.donor) as dz:
        parts={n:sz.read(n) for n in sz.namelist()}
        wb=E.fromstring(parts['xl/workbook.xml'])
        rels=E.fromstring(parts['xl/_rels/workbook.xml.rels'])
        donorwb=E.fromstring(dz.read('xl/workbook.xml'))
        donor_rels={r.get('Id'):r.get('Target') for r in E.fromstring(dz.read('xl/_rels/workbook.xml.rels'))}
        donor_sheets={s.get('name'):s for s in donorwb.find('m:sheets',NS)}
        if set(donor_sheets)!=set(NEW_SHEETS):
            raise ValueError('donor sheet list differs from candidate contract')
        shared=list(E.fromstring(dz.read('xl/sharedStrings.xml'))) if 'xl/sharedStrings.xml' in dz.namelist() else []
        st=E.fromstring(parts['xl/styles.xml'])
        ds=E.fromstring(dz.read('xl/styles.xml'))
        base={kind:len(st.find('m:'+kind,NS)) for kind in ['fonts','fills','borders','cellXfs']}
        for kind in ['fonts','fills','borders']:
            dest=st.find('m:'+kind,NS)
            for item in ds.find('m:'+kind,NS):dest.append(copy.deepcopy(item))
            dest.set('count',str(len(dest)))
        numfmts=st.find('m:numFmts',NS)
        dnumfmts=ds.find('m:numFmts',NS)
        fmtmap={}
        if dnumfmts is not None and len(dnumfmts):
            if numfmts is None:
                numfmts=E.Element(tag('numFmts'),{'count':'0'});st.insert(0,numfmts)
            codes={x.get('formatCode'):int(x.get('numFmtId')) for x in numfmts}
            nextid=max([163]+[int(x.get('numFmtId')) for x in numfmts])+1
            for x in dnumfmts:
                code=x.get('formatCode');old=int(x.get('numFmtId'))
                if code not in codes:
                    y=copy.deepcopy(x);y.set('numFmtId',str(nextid));numfmts.append(y)
                    codes[code]=nextid;nextid+=1
                fmtmap[old]=codes[code]
            numfmts.set('count',str(len(numfmts)))
        xfs=st.find('m:cellXfs',NS)
        for xf in ds.find('m:cellXfs',NS):
            y=copy.deepcopy(xf)
            for field,kind in [('fontId','fonts'),('fillId','fills'),('borderId','borders')]:
                y.set(field,str(int(y.get(field,'0'))+base[kind]))
            if int(y.get('numFmtId','0')) in fmtmap:
                y.set('numFmtId',str(fmtmap[int(y.get('numFmtId'))]))
            y.set('xfId','0');xfs.append(y)
        xfs.set('count',str(len(xfs)))
        sheets=wb.find('m:sheets',NS)
        sheetid=max(int(s.get('sheetId')) for s in sheets)
        partnum=max(int(re.search(r'sheet(\d+)',n).group(1)) for n in parts
                    if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n))
        ct=E.fromstring(parts['[Content_Types].xml'])
        ctns='http://schemas.openxmlformats.org/package/2006/content-types'
        relns='http://schemas.openxmlformats.org/package/2006/relationships'
        newparts={}
        for idx,name in enumerate(NEW_SHEETS):
            dsheet=donor_sheets[name]
            source=posixpath.normpath(posixpath.join('xl',donor_rels[dsheet.get('{'+R+'}id')])).lstrip('/')
            sh=E.fromstring(dz.read(source))
            if sh.find('m:drawing',NS) is not None:
                raise ValueError('donor drawing requires validation')
            for c in sh.findall('.//m:c',NS):
                if c.get('t')=='s':
                    v=c.find('m:v',NS);si=copy.deepcopy(shared[int(v.text)])
                    si.tag=tag('is');c.remove(v);c.append(si);c.set('t','inlineStr')
                c.set('s',str(int(c.get('s','0'))+base['cellXfs']))
            for c in sh.findall('m:cols/m:col',NS):
                if 'style' in c.attrib:c.set('style',str(int(c.get('style'))+base['cellXfs']))
            for row in sh.findall('m:sheetData/m:row',NS):
                if 's' in row.attrib:row.set('s',str(int(row.get('s'))+base['cellXfs']))
            part=f'xl/worksheets/sheet{partnum+idx+1}.xml'
            newparts[part]=xml(sh)
            rid=f'rIdCandidate{idx+1}'
            if rid in {x.get('Id') for x in rels}:raise ValueError('relationship collision')
            sheets.insert(idx,E.Element(tag('sheet'),{'name':name,'sheetId':str(sheetid+idx+1),'{'+R+'}id':rid}))
            rels.append(E.Element('{'+relns+'}Relationship',{'Id':rid,'Type':R+'/worksheet',
                                                             'Target':f'worksheets/sheet{partnum+idx+1}.xml'}))
            ct.append(E.Element('{'+ctns+'}Override',{'PartName':'/'+part,
              'ContentType':'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'}))
        for defined in wb.findall('m:definedNames/m:definedName',NS):
            if 'localSheetId' in defined.attrib:
                defined.set('localSheetId',str(int(defined.get('localSheetId'))+len(NEW_SHEETS)))
        cp=wb.find('m:calcPr',NS)
        if cp is not None:cp.set('fullCalcOnLoad','1')
        modified={'xl/workbook.xml':xml(wb),'xl/_rels/workbook.xml.rels':xml(rels),
                  'xl/styles.xml':xml(st),'[Content_Types].xml':xml(ct)}
        a.out.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(a.out,'w',compression=zipfile.ZIP_DEFLATED) as oz:
            for info in sz.infolist():oz.writestr(info,modified.get(info.filename,parts[info.filename]))
            for name,bytes_ in newparts.items():oz.writestr(name,bytes_)
    old,new=workbook_cells(a.source_copy),workbook_cells(a.out)
    if [x['name'] for x in new['sheets'][:4]]!=NEW_SHEETS or new['sheets'][4:]!=old['sheets']:
        raise ValueError('source worksheet contents/order changed')
    allowed={'xl/workbook.xml','xl/_rels/workbook.xml.rels','xl/styles.xml','[Content_Types].xml'}
    diff={p for p,h in old['part_hashes'].items() if new['part_hashes'].get(p)!=h}
    if diff!=allowed or old['chart_count']!=new['chart_count'] or old['chart_count']!=148:
        raise ValueError('candidate package changed an existing part')
    expected=set(newparts)
    if set(new['part_hashes'])-set(old['part_hashes'])!=expected:
        raise ValueError('unexpected extra package part')
    with zipfile.ZipFile(a.out) as z:
        for name in z.namelist():
            if name.endswith(('.xml','.rels')):E.fromstring(z.read(name))
    check={'status':'PASS','source_copy_sha256':sha(a.source_copy.read_bytes()),
           'candidate_sha256':sha(a.out.read_bytes()),'source_sheet_count':len(old['sheets']),
           'candidate_sheet_count':len(new['sheets']),'charts':148,'new_sheets':NEW_SHEETS,
           'existing_original_parts_identical_except_registration_and_appended_styles':True,
           'changed_existing_parts':sorted(diff),'new_parts':sorted(expected)}
    write_json(a.checks,check)
    print(json.dumps(check,ensure_ascii=False))


if __name__=='__main__':main()
