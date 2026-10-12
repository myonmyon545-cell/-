"""Preservation adapter: Artifact-authored summary/notes only; no raw-value edits."""
import argparse,copy,json,re,zipfile
from pathlib import Path
from xml.etree import ElementTree as E
from inspect_inputs import NS,sha,workbook_cells
from preserve_package import sheets_by_name,xml,tag
def main():
 p=argparse.ArgumentParser();p.add_argument('--source-copy',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--notes',type=Path,required=True);p.add_argument('--tables',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--checks',type=Path,required=True);a=p.parse_args()
 notes=json.loads(a.notes.read_text());table=json.loads(a.tables.read_text());old=workbook_cells(a.source_copy)
 if len(notes)!=21:raise ValueError(f'expected 6 preserved captions + 15 E20-03 captions; got {len(notes)}')
 if len({(n,r) for n,r,_ in notes})!=len(notes):raise ValueError('duplicate caption ranges')
 if len({t for _,_,t in notes})!=len(notes):raise ValueError('duplicate caption bodies')
 assert len(old['sheets'])==15 and old['sheets'][0]['name']=='分析要点' and old['chart_count']==148
 with zipfile.ZipFile(a.source_copy) as sz,zipfile.ZipFile(a.donor) as dz:
  parts={n:sz.read(n) for n in sz.namelist()};sm=sheets_by_name(sz,'xl/workbook.xml');dm=sheets_by_name(dz,'xl/workbook.xml');st=E.fromstring(parts['xl/styles.xml']);ds=E.fromstring(dz.read('xl/styles.xml'))
  base={k:len(st.find('m:'+k,NS)) for k in ['fonts','fills','borders','cellXfs']}
  for k in ['fonts','fills','borders']:
   node=st.find('m:'+k,NS)
   for item in ds.find('m:'+k,NS):node.append(copy.deepcopy(item))
   node.set('count',str(len(node)))
  nfs=st.find('m:numFmts',NS)
  if nfs is None:nfs=E.Element(tag('numFmts'));st.insert(0,nfs)
  fmtmap={};codes={n.get('formatCode'):int(n.get('numFmtId')) for n in nfs};nid=max([163]+list(codes.values()))+1
  for n in ds.findall('m:numFmts/m:numFmt',NS):
   code=n.get('formatCode')
   if code not in codes:q=copy.deepcopy(n);q.set('numFmtId',str(nid));nfs.append(q);codes[code]=nid;nid+=1
   fmtmap[int(n.get('numFmtId'))]=codes[code]
  nfs.set('count',str(len(nfs)));xfs=st.find('m:cellXfs',NS)
  for xf in ds.find('m:cellXfs',NS):
   q=copy.deepcopy(xf)
   for attr,k in [('fontId','fonts'),('fillId','fills'),('borderId','borders')]:q.set(attr,str(int(q.get(attr,'0'))+base[k]))
   if int(q.get('numFmtId','0')) in fmtmap:q.set('numFmtId',str(fmtmap[int(q.get('numFmtId'))]))
   q.set('xfId','0');xfs.append(q)
  xfs.set('count',str(len(xfs)));shared=list(E.fromstring(dz.read('xl/sharedStrings.xml'))) if 'xl/sharedStrings.xml' in dz.namelist() else []
  def convert(sh):
   for c in sh.findall('.//m:c',NS):
    if c.get('t')=='s':v=c.find('m:v',NS);q=copy.deepcopy(shared[int(v.text)]);q.tag=tag('is');c.remove(v);c.append(q);c.set('t','inlineStr')
    c.set('s',str(int(c.get('s','0'))+base['cellXfs']))
   for c in sh.findall('m:cols/m:col',NS):
    if 'style' in c.attrib:c.set('style',str(int(c.get('style'))+base['cellXfs']))
   for r in sh.findall('m:sheetData/m:row',NS):
    if 's' in r.attrib:r.set('s',str(int(r.get('s'))+base['cellXfs']))
   return sh
  summary=convert(E.fromstring(dz.read(dm['分析要点'])))
  for k in ['pageMargins','pageSetup','printOptions']:
   n=summary.find('m:'+k,NS)
   if n is not None:summary.remove(n)
  sp=summary.find('m:sheetPr',NS)
  if sp is None:sp=E.Element(tag('sheetPr'));summary.insert(0,sp)
  E.SubElement(sp,tag('pageSetUpPr'),{'fitToPage':'1'})
  E.SubElement(summary,tag('pageMargins'),{'left':'0.25','right':'0.25','top':'0.4','bottom':'0.4','header':'0.2','footer':'0.2'})
  E.SubElement(summary,tag('pageSetup'),{'paperSize':'8','orientation':'landscape','fitToWidth':'1','fitToHeight':'0'})
  parts[sm['分析要点']]=xml(summary)
  edited={}
  for name,rng,note in notes:
   dest=edited.setdefault(name,E.fromstring(parts[sm[name]]));donor=convert(E.fromstring(dz.read(dm[name])));addr=rng.split(':')[0]
   # Never overwrite a source value/formula; authorize only the blank local-caption row.
   for c in dest.findall('.//m:c',NS):
    if c.get('r')==addr:assert c.find('m:v',NS) is None and c.find('m:f',NS) is None and c.find('m:is',NS) is None,'caption target not blank'
   rnum=re.search(r'\d+',addr)[0];sd=dest.find('m:sheetData',NS);row=sd.find(f'm:row[@r="{rnum}"]',NS)
   if row is None:raise ValueError('caption row missing; preserve row layout')
   prev=row.find(f'm:c[@r="{addr}"]',NS)
   if prev is not None:row.remove(prev)
   q=copy.deepcopy(donor.find(f'.//m:c[@r="{addr}"]',NS));row.append(q);row[:]=sorted(row,key=lambda c:(len(re.match('[A-Z]+',c.get('r'))[0]),re.match('[A-Z]+',c.get('r'))[0]))
   merges=dest.find('m:mergeCells',NS)
   if merges is None:raise ValueError('merge registry missing')
   if any(m.get('ref')==rng for m in merges.findall('m:mergeCell',NS)):raise ValueError('duplicate merged caption range: '+rng)
   E.SubElement(merges,tag('mergeCell'),{'ref':rng});merges.set('count',str(len(merges)))
  for name,sh in edited.items():parts[sm[name]]=xml(sh)
  wb=E.fromstring(parts['xl/workbook.xml']);dn=wb.find('m:definedNames',NS)
  for name,value in [('_xlnm.Print_Area',f"'分析要点'!$A$1:$N${len(table['rows'])}"),('_xlnm.Print_Titles',f"'分析要点'!${table['header_row']}:${table['header_row']}")]:
   found=next((n for n in dn if n.get('name')==name and n.get('localSheetId')=='0'),None)
   if found is None:found=E.SubElement(dn,tag('definedName'),{'name':name,'localSheetId':'0'})
   found.text=value
  parts['xl/workbook.xml']=xml(wb);parts['xl/styles.xml']=xml(st)
  a.out.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(a.out,'w',zipfile.ZIP_DEFLATED) as z:
   for info in sz.infolist():z.writestr(info,parts[info.filename])
 new=workbook_cells(a.out);assert len(new['sheets'])==15 and new['chart_count']==148
 # Verify every caption has one exact merge and exact displayed body in the assembled OOXML.
 with zipfile.ZipFile(a.out) as verify_zip:
  out_sheets=sheets_by_name(verify_zip,'xl/workbook.xml')
  seen=set()
  for name,rng,note in notes:
   key=(name,rng)
   if key in seen:raise ValueError('duplicate caption in output: '+repr(key))
   seen.add(key)
   part=E.fromstring(verify_zip.read(out_sheets[name]))
   if not any(m.get('ref')==rng for m in part.findall('m:mergeCells/m:mergeCell',NS)):raise ValueError('caption merge missing: '+repr(key))
   addr=rng.split(':')[0];cell=part.find(f'.//m:sheetData/m:row/m:c[@r="{addr}"]',NS)
   value=cell.find('m:v',NS) if cell is not None else None
   text=value.text if value is not None else ''.join(t.text or '' for t in cell.findall('.//m:t',NS)) if cell is not None else ''
   if text!=note:raise ValueError('caption body mismatch: '+repr(key))
 if len(seen)!=21:raise ValueError('caption count mismatch')
 assert [s['name'] for s in old['sheets']]==[s['name'] for s in new['sheets']]
 allowed={sm['分析要点'],'xl/workbook.xml','xl/styles.xml'}|{sm[n] for n,_,_ in notes}
 diff={n for n,h in old['part_hashes'].items() if h!=new['part_hashes'][n]};assert diff==allowed,(diff,allowed)
 noteaddrs={(n,r.split(':')[0]) for n,r,_ in notes}
 for os,ns in zip(old['sheets'][1:],new['sheets'][1:]):
  for addr,c in os['cells'].items():
   if (os['name'],addr) not in noteaddrs:assert c==ns['cells'].get(addr),(os['name'],addr)
  assert os['print_xml']==ns['print_xml'] and os['hidden_rows']==ns['hidden_rows'] and os['hidden_cols']==ns['hidden_cols']
 result={'status':'PASS','candidate_sha256':sha(a.out.read_bytes()),'base_C03_copy_sha256':sha(a.source_copy.read_bytes()),'C03_reapplied':False,'sheets':15,'charts':148,'local_caption_cells':[list(x) for x in sorted(noteaddrs)],'changed_parts':sorted(diff),'all_original_values_formulas_unchanged':True,'all_chart_drawing_image_parts_byte_identical':True,'original_print_hidden_settings_unchanged':True,'summary_print':{'orientation':'landscape','paper':'A3','width_pages':1,'height_pages':'automatic','range':f'A1:N{len(table["rows"])}','repeat_row':table['header_row']},'visual_readability':'pending E01/native print review'}
 a.checks.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()

