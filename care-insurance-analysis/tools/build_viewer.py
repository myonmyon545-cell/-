"""Offline, dependency-light atlas from fixed GitHub input and archived timeline."""
import argparse, json, hashlib, re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml

def build(source, timeline, template, out):
 source=json.loads(Path(source).read_text()); timeline=json.loads(Path(timeline).read_text()); out=Path(out);out.mkdir(parents=True,exist_ok=True)
 y=yaml.safe_load(source['plan'].split('```yaml')[1].split('```')[0])
 roles={'10.json':'ROLE10の実作業報告。候補・入力・検査・再開情報。','20.json':'ROLE20の独立評価。FAIL/HELD/PASSは固定候補に対する判定。','30.json':'ROLE30の修正提案。適用済みの証明ではない。','PLAN.md':'現行解析・評価契約と運用仕様。','STATE.json':'ROLE00が更新する保存済み進捗。別チャットの実行状態そのものではない。','timeline.html':'検索・展開可能な会話/作業タイムライン。','candidate.json':'固定候補の数値・根拠・状態を機械検査するパッケージ。','S10_excerpts.json':'追加資料の出所・年度・根拠ブロック。主解析とは別の提供値。','build_timeline.py':'収録元からタイムラインを再生成するコード。'}
 files=[]
 for f in source['tree']:
  name=f['path'].split('/')[-1]
  summary=roles.get(name)
  if not summary:
   if f['type']=='tree':summary='入れ子構造のフォルダ。下位項目を選択して概要を表示。'
   elif '/src/' in f['path']:summary='解析・候補生成・再現のコード。存在確認のみで実行済みとは扱わない。'
   elif '/logs/' in f['path']:summary='取得可能な作業/会話/検証の履歴。原文と要約、失敗と成功を区別。'
   elif '/checks/' in f['path']:summary='保存済み検査記録。対象候補・計画版・実行範囲の確認が必要。'
   elif '/references/' in f['path']:summary='参照資料・簡易確認・出所情報。完成版の実績と区別。'
   elif '/roles/' in f['path']:summary='担当チャットの役割・開始・受渡し指示。'
   else:summary='固定コミットで存在を確認した管理ファイル。概要はファイル用途の説明。'
  files.append(dict(f,summary=summary))
 actual=[]
 for role,r in source['reports'].items():
  actual.append({'title':'ROLE'+role+' 保存済み報告','at':r.get('updated_at'),'status':r.get('verdict',r.get('status')),'plan_revision':r.get('plan_revision'),'candidate':r.get('candidate'),'next_action':r.get('next_action'),'source':'reports/'+role+'.json','scope':'保存済み報告に基づく履歴。現行契約への適用完了は別途必要。'})
 tasks=[dict(x,id=k,record_status='現行計画。新版候補への完了報告未確認') for k,x in y['execution'].items() if isinstance(x,dict) and re.fullmatch(r'T\d+',k)]
 tasks.sort(key=lambda x:int(x['id'][1:]))
 data={'schema':'care_process_atlas/v1','as_of':source.get('as_of') or datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(timespec='seconds'),'base_commit':source['base_commit'],'plan_revision':y['meta']['revision'],'candidate_binding':None,'release_status':'NOT_FINAL','timeline':timeline,'actual':actual,'tasks':tasks,'files':files,'state_record_at':source['state'].get('updated_at'),'missing':['過去の全チャット原文は未取得','現行2.4新候補の実処理完了は未確認','非公開原本/候補のファイルツリーはROLE10の実manifest待ち','実ブラウザ操作・3D視覚検証は未実施']}
 text=Path(template).read_text().replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c'))
 (out/'index.html').write_text(text)
 (out/'process_atlas.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 manifest={'schema':'care_atlas_manifest/v1','base_commit':data['base_commit'],'candidate_binding':None,'release_status':'NOT_FINAL','files':[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in [out/'index.html',out/'process_atlas.json']],'self_hash':'manifest excluded'}
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'files':len(files),'tasks':len(tasks),'records':len(timeline['records']),'status':'NOT_FINAL'},ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--timeline',required=True);p.add_argument('--template',required=True);p.add_argument('--out',required=True);a=p.parse_args();build(a.input,a.timeline,a.template,a.out)
