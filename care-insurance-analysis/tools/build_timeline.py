"""Build an offline timeline from retrieved conversation and pinned repository records."""
import argparse, csv, html, json, re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

def assemble(folder):
    folder=Path(folder)
    def load(name):return json.loads((folder/name).read_text())
    commits=load('sources/commits.json');snapshots=[]
    for path in sorted((folder/'sources/snapshots').glob('*.json')):
        short,name=path.name.split('-',1)
        sha=next(c['sha'] for c in commits if c['sha'].startswith(short))
        repository_path='care-insurance-analysis/'+('STATE.json' if name=='STATE.json' else 'reports/'+name)
        snapshots.append({'sha':sha,'path':repository_path,'content':json.loads(path.read_text())})
    return {'base_commit':load('timeline.json')['base_commit'],'retrieved_context':[load('sources/context_1.json'),load('sources/context_2.json')],'commit_details':commits,'snapshots':snapshots,'visible_users':load('sources/conversation_available_user_text.json'),'assistant_raw':load('sources/assistant_available_text.json')}

def build(source_path,out):
    data=source_path if isinstance(source_path,dict) else json.loads(Path(source_path).read_text());out=Path(out);out.mkdir(parents=True,exist_ok=True)
    records=[]
    def add(id,at,role,chat,kind,title,body,source,quality,order=None):
        if at:
            dt=datetime.fromisoformat(at.replace('Z','+00:00')).astimezone(ZoneInfo('Asia/Tokyo'))
            at=dt.isoformat(timespec='seconds');shown=dt.strftime('%Y-%m-%d %H:%M:%S JST')
        else: shown='送信日時不明'+(f' / 会話順 {order:g}' if order else '')
        records.append(dict(id=id,at=at,display_time=shown,role=role,chat=chat,kind=kind,title=title,body=body,source=source,quality=quality,conversation_order=order))
    for m in data['visible_users']['messages']:
        add('user-'+str(m['sequence']),m.get('timestamp'),'プロデューサー','計画','会話原文',m['content'].splitlines()[0][:90],m['content'],'logs/conversation_available_user_text.json','表示済み本文。時刻未取得分は日時不明。',m['sequence'])
    for m in data.get('assistant_raw',[]):
        add('assistant-'+str(m['sequence']),m.get('timestamp'),'計画AI','計画','会話原文','計画2.4の保存・引継ぎ回答',m['content'],'現在の計画チャット表示本文',m['scope'],m['sequence'])
    maps=[{'c0':'資料確認','c2':'資料確認','c3':'資料確認','c1':'計画','c4':'共通指示','c5':'10 作業'}, {'c0':'計画','c1':'20 評価','c3':'40 履歴','c4':'10 作業'}]
    excluded=[]
    for i,result in enumerate(data['retrieved_context']):
        for m in result.get('messages',[]):
            for n,line in enumerate(m['content'].splitlines()):
                match=re.match(r'^- \[([^]]+)\] (.*?) ([UA])@(\d{4}-\d\d-\d\dT[^, ]+).*?: (.*)$',line)
                if not match: continue
                typ,tags,author,at,body=match.groups();c=re.findall(r'\[(c\d+)\]',tags)
                if i==1 and 'c2' in c:
                    excluded.append({'line':line,'reason':'検索依頼に由来する可能性があり役割チャットとの対応未確定。確定会話イベントへ採用しない。'});continue
                chat=next((maps[i][key] for key in c if key in maps[i]),'チャット未特定')
                add(f'retrieved-{i}-{n}',at,'プロデューサー' if author=='U' else chat+' AI',chat,'会話要約',body[:90],body,f'sources/context_{i+1}.json','検索で取得した要約。付属送信日時は原メッセージ未照合。全文ではない。')
    commits={x['sha']:x for x in data['commit_details']}
    for c in data['commit_details']:
        paths=[x['path'] for x in c['files']]
        role='10 作業' if all('/src/' in x or '/tools/' in x for x in paths) else '記録保存'
        add('commit-'+c['sha'],c['commit_at'],role,'GitHub','保存履歴',c['message'],json.dumps({'changed_files':c['files'],'diff_available':c['full_diff_available'],'completion_policy':'コミット説明だけで解析完了を判定しない。'},ensure_ascii=False,indent=2),'https://github.com/myonmyon545-cell/-/commit/'+c['sha'],'GitHubコミットと変更ファイル一覧を確認。保存日時。')
    for snap in data['snapshots']:
        if 'retrieval_error' in snap:continue
        x=snap['content'];role=x.get('role','00');status=x.get('verdict') or x.get('status') or x.get('phase') or '記録更新'
        base=Path(snap['path']).name;title=('役割'+role+' 報告' if base!='STATE.json' else '進捗・計画記録')+' / '+status
        f='sources/snapshots/'+snap['sha'][:12]+'-'+base
        body={'plan_revision':x.get('plan_revision'),'reported_at':x.get('updated_at'),'status':x.get('status'),'phase':x.get('phase'),'verdict':x.get('verdict'),'candidate':x.get('candidate'),'next_action':x.get('next_action'),'scope':'原記録の作成日時と保存コミット日時は別。詳細原文は収録JSON参照。'}
        add('snapshot-'+snap['sha']+'-'+base,x.get('updated_at'),role,'役割'+role,'保存報告',title,json.dumps(body,ensure_ascii=False,indent=2),f,'同一コミットの実JSONを読取。全文スナップショット収録。')
        dump(out/f,x)
    known=sorted((x for x in records if x['at']),key=lambda x:(x['at'],x['id']))
    unknown=sorted((x for x in records if not x['at']),key=lambda x:x.get('conversation_order') or 1e9)
    records=known+unknown
    coverage={'raw_user_messages':len(data['visible_users']['messages']),'raw_assistant_messages':len(data.get('assistant_raw',[])),'retrieved_summaries':sum(x['kind']=='会話要約' for x in records),'saved_report_versions':len(data['snapshots']),'commit_records':len(data['commit_details']),'dated_records':len(known),'undated_records':len(unknown),'excluded_retrieval_records':len(excluded),'gaps':['過去チャット全体の原文は未取得。検索要約を全文と表示しない。','00/30の公開会話全文は未取得。保存済みJSON報告/STATEで補完。','40は一部要約のみ。全更新会話は未取得。','古い計画AI応答は全件未取得。今回取得した表示原文1件と検索要約を収録。','送信日時不明の原文は会話順を保持し、保存日時を送信日時へ転用しない。','GitHub大型JSONの差分は一部省略。必要な報告/STATEは実JSONを別取得。'],'not_claimed':'全チャット全文収録済み、他チャット実行状態の直接観測、候補完成/評価合格は主張しない。'}
    pack={'schema':'care_timeline/v1','as_of':datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(timespec='seconds'),'base_commit':data['base_commit'],'timezone':'Asia/Tokyo','coverage':coverage,'records':records}
    dump(out/'timeline.json',pack);dump(out/'sources/commits.json',data['commit_details'])
    dump(out/'sources/conversation_available_user_text.json',data['visible_users']);dump(out/'sources/assistant_available_text.json',data.get('assistant_raw',[]))
    for i,x in enumerate(data['retrieved_context']):dump(out/f'sources/context_{i+1}.json',x)
    dump(out/'sources/excluded_retrieval_records.json',excluded)
    with (out/'timeline.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','at','display_time','role','chat','kind','title','body','source','quality','conversation_order'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
    esc=html.escape
    def item(x):
        searchable=esc((x['title']+' '+x['body']+' '+x['role']+' '+x['chat']).lower(),quote=True)
        return '<article data-kind="'+esc(x['kind'])+'" data-chat="'+esc(x['chat'])+'" data-search="'+searchable+'"><div class="time">'+esc(x['display_time'])+'</div><div class="meta">'+esc(x['chat']+' · '+x['role']+' · '+x['kind'])+'</div><details><summary>'+esc(x['title'])+'</summary><p class="quality">'+esc(x['quality'])+'</p><pre>'+esc(x['body'])+'</pre><p class="source">根拠：'+esc(x['source'])+'</p></details></article>'
    kinds=sorted({x['kind'] for x in records});chats=sorted({x['chat'] for x in records})
    def options(xs):return '<option value="">すべて</option>'+''.join('<option>'+esc(x)+'</option>' for x in xs)
    css=''' :root{color-scheme:light dark;--bg:light-dark(#f8fafc,#111827);--fg:light-dark(#172033,#e5e7eb);--muted:light-dark(#475569,#b2becd);--card:light-dark(#fff,#192235);--line:light-dark(#cbd5e1,#475569);--accent:light-dark(#2759a5,#92b9f8)}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.65 system-ui,-apple-system,'Noto Sans JP',sans-serif}main{max-width:920px;margin:auto;padding:24px 18px}h1{font-size:26px;line-height:1.3;margin:0 0 12px}h2{font-size:20px;margin:26px 0 12px}.caption,.quality,.source,.meta{color:var(--muted);overflow-wrap:anywhere}.overview{padding:16px;background:var(--card);border-radius:12px;margin:18px 0}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}.controls label{display:flex;flex-direction:column;flex:1 1 180px}select,input{font:inherit;color:var(--fg);background:var(--card);padding:10px;border:1px solid var(--line);border-radius:8px;width:100%;min-height:44px}article{border-left:2px solid var(--line);padding:8px 0 20px 18px;margin-left:5px;position:relative;overflow-wrap:anywhere}article:before{content:'';position:absolute;width:10px;height:10px;background:var(--accent);border-radius:50%;left:-6px;top:17px}.time{font-weight:650;font-variant-numeric:tabular-nums}.meta{font-size:14px}summary{cursor:pointer;min-height:44px;padding:8px 0;font-weight:600}pre{white-space:pre-wrap;font:inherit;overflow-wrap:anywhere;background:var(--card);padding:14px;border-radius:8px}p{margin:10px 0}a{color:var(--accent)}[hidden]{display:none!important}#count{font-variant-numeric:tabular-nums}footer{margin-top:28px;color:var(--muted)}@media(max-width:420px){main{padding:18px 12px}h1{font-size:22px}.controls{gap:8px}article{padding-left:13px}}@media print{body{background:white;color:black}.controls{display:none}details>pre,details>p{display:block}article{break-inside:avoid}summary{list-style:none}}'''
    script='''const root=document.getElementById('care-timeline');const items=[...root.querySelectorAll('article')];function update(){const q=root.querySelector('#q').value.toLowerCase();const kind=root.querySelector('#kind').value;const chat=root.querySelector('#chat').value;let n=0;for(const x of items){const show=(!q||x.dataset.search.includes(q))&&(!kind||x.dataset.kind===kind)&&(!chat||x.dataset.chat===chat);x.hidden=!show;if(show)n++;}root.querySelector('#count').textContent=n+'件表示 / '+items.length+'件収録';for(const section of root.querySelectorAll('.events-section'))section.hidden=![...section.querySelectorAll('article')].some(x=>!x.hidden);}for(const el of root.querySelectorAll('input,select'))el.addEventListener('input',update);update();'''
    doc='<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>介護保険解析 会話と作業のタイムライン</title><style>'+css+'</style></head><body><main id="care-timeline"><h1>会話と作業のタイムライン</h1><p class="caption">介護保険データ解析 · 日本時間 · 取得時点 '+esc(pack['as_of'])+'</p><div class="overview"><strong>原文・要約・保存記録を分けて表示</strong><p>ユーザー原文 '+str(coverage['raw_user_messages'])+'件、AI応答原文 '+str(coverage['raw_assistant_messages'])+'件、会話要約 '+str(coverage['retrieved_summaries'])+'件、報告・進捗 '+str(coverage['saved_report_versions'])+'版、変更履歴 '+str(coverage['commit_records'])+'件。</p><p>全文未取得の会話は未収録。日時不明の発言は下段に会話順で掲載。各項目をタップすると本文と根拠を開けます。</p></div><div class="controls"><label>本文検索<input id="q" type="search" placeholder="例：C04、候補、未算出"></label><label>記録の種類<select id="kind">'+options(kinds)+'</select></label><label>チャット・役割<select id="chat">'+options(chats)+'</select></label></div><p id="count" aria-live="polite"></p><section class="events-section"><h2>日時がある記録</h2>'+''.join(item(x) for x in known)+'</section><section class="events-section"><h2>送信日時不明の会話（会話順）</h2>'+''.join(item(x) for x in unknown)+'</section><footer><details><summary>未収録と確認範囲</summary><ul>'+''.join('<li>'+esc(x)+'</li>' for x in coverage['gaps'])+'</ul></details><p>取得元コミット：'+esc(pack['base_commit'])+'。履歴上の古い指示は当時の記録です。現行指示は最新PLANを参照。</p></footer></main><script>'+script+'</script></body></html>'
    (out/'timeline.html').write_text(doc)
    lines=['# 介護保険データ解析 会話・作業タイムライン','',f'取得時点：{pack["as_of"]} / 日本時間。対象コミット：`{pack["base_commit"]}`。','',f'ユーザー原文{coverage["raw_user_messages"]}件、AI応答原文{coverage["raw_assistant_messages"]}件、会話要約{coverage["retrieved_summaries"]}件、報告・進捗{coverage["saved_report_versions"]}版、変更履歴{coverage["commit_records"]}件。','', '**全チャット全文の収録ではありません。原文・検索要約・実報告・保存日時を区別しています。**','', '## 日時がある記録','', '| 日本時間 | チャット・担当 | 種類 | 内容 | 根拠 |','|---|---|---|---|---|']
    for x in known:
        source=x['source'];link='[根拠]('+source+')' if source.startswith('https://') else '[根拠]('+source+')'
        lines.append('| '+x['display_time'].replace(' JST','')+' | '+x['chat']+' / '+x['role']+' | '+x['kind']+' | '+x['title'].replace('|','／').replace('\n',' ')+' | '+link+' |')
    lines+=['','## 送信日時不明の会話原文','', '順序だけを保持。保存時刻や他の会話の日時を転用しません。','']
    for x in unknown:
        lines+=['<details>',f'<summary>会話順{x["conversation_order"]:g} / {x["role"]} / {esc(x["title"])}</summary>','',x['body'],'','</details>','']
    lines+=['## 未収録','']+['- '+x for x in coverage['gaps']]
    (out/'TIMELINE.md').write_text('\n'.join(lines)+'\n')
    dump(out/'coverage.json',coverage)
    manifest=[]
    import hashlib
    for f in sorted(out.rglob('*')):
        if f.is_file():manifest.append({'path':f.relative_to(out).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size})
    dump(out/'manifest.json',{'base_commit':data['base_commit'],'files':manifest,'self_hash':'manifest itself excluded'})
    return pack

if __name__=='__main__':
    a=argparse.ArgumentParser();group=a.add_mutually_exclusive_group(required=True);group.add_argument('--source');group.add_argument('--source-dir');a.add_argument('--out',required=True);args=a.parse_args();pack=build(assemble(args.source_dir) if args.source_dir else args.source,args.out);print(json.dumps({'records':len(pack['records']),'coverage':pack['coverage']},ensure_ascii=False))
