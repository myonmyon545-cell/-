"""Verify extracted cached values with an independent, read-only XLSX parser."""
import argparse
import json
from pathlib import Path
import openpyxl
from inspect_inputs import SOURCES, write_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--sources',type=Path,required=True);p.add_argument('--calculation',type=Path,required=True);a=p.parse_args()
    data=json.loads((a.calculation/'extracted_values.json').read_text());lookup={};count=0;bad=[]
    for sid in ['S01','S02']:
        # Load bytes because the source attachment can have no .xlsx suffix.
        with open(a.sources/SOURCES[sid][0],'rb') as stream:
            wb=openpyxl.load_workbook(stream,read_only=True,data_only=True,keep_links=True)
            for sh in wb:
                lookup[(sid,sh.title)]={c.coordinate:c.value for row in sh.iter_rows() for c in row if c.value is not None}
            wb.close()
    for r in data['records']:
        value=lookup[(r['input_id'],r['source_ref']['sheet'])].get(r['source_ref']['cell']);observed=r['source_value']
        if value!=observed:bad.append({'input':r['input_id'],'id':r['id'],'source':value,'extracted':observed})
        count+=1
    for r in data['comparisons']:
        if r['status']=='held' and r['value'] is not None:bad.append({'id':r['id'],'reason':'held comparison has numeric output'})
    result={'verdict':'PASS' if not bad else 'FAIL','verified_source_values':count,'independent_parser':'openpyxl read-only data_only','differences':bad,'workbook_write_performed':False,'scope':'all extracted source values; not independent AI interpretation or layout evaluation'}
    write_json(a.calculation/'independent_extraction_check.json',result);print(json.dumps(result,ensure_ascii=False))
    if bad:raise SystemExit(1)

if __name__=='__main__':main()
