"""Portable full v2 assembly replay from validated aggregate inputs/C03 checkpoint."""
import argparse,json,os,subprocess,sys,tempfile,zipfile
from pathlib import Path
from xml.etree import ElementTree as E
from inspect_inputs import sha,workbook_cells
def main():
 p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--sources',type=Path,required=True);p.add_argument('--node',type=Path,required=True);p.add_argument('--node-modules',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();src=Path(__file__).resolve().parent;b=a.bundle.resolve();a.out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((b/'src/input_manifest.json').read_text());s10ref=json.loads((b/'references/S10_excerpts.json').read_text());expected={k:v['sha256'] for k,v in manifest.items() if k in ['S01','S02','S03','S04','S05','S06']};expected['S10']=s10ref['source']['sha256']
 files={sha(f.read_bytes()):f for f in a.sources.iterdir() if f.is_file()};assert all(h in files for h in expected.values()),'required source SHA256 missing'
 def run(script,args):subprocess.run([sys.executable,str(src/script),*map(str,args)],check=True)
 run('replay_pipeline.py',['--inspection',b/'inspection','--sources',a.sources,'--source-copy',b/'candidate/S01_C03_作業コピー_保持試験.xlsx','--proposal',b/'historical/role30_initial.json','--comparison',b/'baseline','--out',a.out/'numeric_replay.json'])
 run('integrate_s10.py',['--source',files[expected['S10']],'--excerpts',b/'references/S10_excerpts.json','--out',a.out/'S10_application.json'])
 run('summary_v2.py',['--extraction',b/'baseline/calculation/extracted_values.json','--supplement',a.out/'S10_application.json','--out',a.out/'summary_tables.json'])
 with tempfile.TemporaryDirectory(prefix='care_v2_author_') as tmp:
  author=Path(tmp);(author/'node_modules').symlink_to(a.node_modules.resolve(),target_is_directory=True);builder=author/'summary_v2.mjs';builder.write_bytes((src/'summary_v2.mjs').read_bytes())
  subprocess.run([str(a.node),str(builder),str((a.out/'summary_tables.json').resolve()),str((a.out/'author').resolve())],check=True)
 run('graft_v2.py',['--source-copy',b/'candidate/S01_C03_作業コピー_保持試験.xlsx','--donor',a.out/'author/summary_donor.xlsx','--notes',a.out/'author/local_notes.json','--tables',a.out/'summary_tables.json','--out',a.out/'candidate_v2.xlsx','--checks',a.out/'preservation.json'])
 original=b/'candidate/介護保険解析_候補_v2.xlsx';replay=a.out/'candidate_v2.xlsx';ow=workbook_cells(original);rw=workbook_cells(replay)
 assert ow['sheets']==rw['sheets'] and ow['chart_count']==rw['chart_count']==148
 def logical(f):
  with zipfile.ZipFile(f) as z:
   return {n:E.tostring(E.fromstring(z.read(n))) if n.endswith(('.xml','.rels')) else z.read(n) for n in z.namelist() if n not in ['docProps/core.xml']}
 left,right=logical(original),logical(replay);differences=[n for n in set(left)|set(right) if left.get(n)!=right.get(n)];assert not differences,differences
 s10a=json.loads((a.out/'S10_application.json').read_text());s10b=json.loads((b/'checks/S10_application.json').read_text());assert s10a==s10b
 report={'status':'PASS','scope':'fresh Artifact summary/local captions and complete native package assembly from SHA-verified retained C03 checkpoint; raw numerical pipeline 6 outputs replayed; original C03 checkpoint itself is validated, not reapplied','candidate_sha256':sha(original.read_bytes()),'replay_sha256':sha(replay.read_bytes()),'logical_part_differences':differences,'all_values_formulas_notes_print_and_chart_parts_equal':True,'S10_native_read_replayed':True,'zip_timestamps_not_compared':True}
 (a.out/'full_replay.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
