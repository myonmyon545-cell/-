"""Metadata only: original bytes never enter the viewer or GitHub."""
from pathlib import PurePosixPath
def registered_files(source):
 root='care-insurance-analysis/登録ファイル'
 out=[{'path':root,'type':'tree','display_title':'Excel・PDF・文書の登録資料','origin':'metadata_catalog','summary':'保存台帳で確認した資料のメタデータ。原本をWebへ送らない。'}]
 seen=set()
 purposes={'S01':'主解析の対象Excel','S02':'前期比較の参考Excel','S03':'完成形の見本Excel','S04':'分析優先項目の指示書','S05':'合議体解析の手順PDF','S06':'合議体集計ツールExcel','S07':'プロジェクト共通指示','S08':'作業計画の基本指示','S09':'作業計画の詳細運用','S10':'追加された介護保険課の業務資料'}
 def add(x,title,kind,latest=''):
  ident=x.get('library_file_id') or x.get('id')
  if not ident or ident in seen or not str(ident).startswith('libfile_'):return
  seen.add(ident);name=x.get('name') or title
  ext=PurePosixPath(name).suffix.lower()
  if ext not in ['.xlsx','.xls','.pdf','.docx','.doc','.md','.zip']:ext={'S04':'.docx','S05':'.pdf','S02':'.xlsx'}.get(kind,'.md')
  out.append({'path':root+'/'+ident+ext,'type':'blob','origin':'library_metadata','display_title':title,'original_name':name,'library_file_id':ident,'version':x.get('library_version',x.get('version')),'sha256':x.get('sha256') or x.get('candidate',{}).get('sha256'),'size':x.get('size_bytes'),'document_kind':kind,'latest_label':latest,'summary':x.get('scope') or x.get('role') or title,'content_uploaded_to_site':False})
 inputs=source.get('state',{}).get('inputs',{})
 numbered=[sid for sid in inputs if sid.startswith('S') and sid[1:].isdigit()]
 newest=max(numbered,key=lambda sid:int(sid[1:])) if numbered else None
 for sid,x in inputs.items():
  add(x,purposes.get(sid,x.get('role') or '登録済み参照資料'),sid,'最新の追加資料' if sid==newest else '')
 for role,r in source.get('reports',{}).items():
  for x in r.get('outputs',[]):
   if not x.get('saved'):continue
   typ=x.get('type','')
   title='保存済み成果物'
   if 'candidate' in typ:title='解析Excelの最新保存候補'
   elif 'copy' in typ:title='原部品保持の試験用Excel'
   elif 'reproduction' in typ:title='再現コード・検査結果のZIP'
   add(x,title,typ,'最新保存候補・完成未承認' if 'candidate' in typ else '')
 return out
