"""One printable summary; full machine audit stays outside the workbook."""
import argparse
import json
from pathlib import Path

from replay_pipeline import STAGE_ID, verify_extraction_manifest


def comparison_trace(extraction):
    by={(r.get('input_id'),r.get('id')):r for r in extraction.get('records',[])}
    trace=[]
    for c in extraction.get('comparisons',[]):
        city=by.get(('S01',c.get('city_id')))
        ref=by.get((c.get('reference_input'),c.get('reference_id')))
        trace.append({
            'id':c.get('id') or '|'.join(str(c.get(k,'')) for k in ('city_id','label','reference_input','reference_id')),
            'city_id':c.get('city_id'),'label':c.get('label'),
            'reference_input':c.get('reference_input'),'reference_id':c.get('reference_id'),
            'value':c.get('value'),'status':c.get('status'),'reason':c.get('reason'),
            'dependent_status':c.get('dependent_status'),
            'city_source_ref':city.get('source_ref') if city else None,
            'reference_source_ref':ref.get('source_ref') if ref else None})
    return trace


def input_provenance(verified, run_id, stage_id):
    return {'run_id':run_id,'stage_id':stage_id,
        'extraction_sha256':verified['extraction_sha256'],
        'manifest_sha256':verified['manifest_sha256']}


def build_summary(x, s, verified, run_id, stage_id):
    rows,formats,header=build_rows(x,s)
    return {'schema':'care_summary_v2/v1','rows':rows,'row_formats':formats,'header_row':header,
        'core_rows':len(rows)-header,'supplemental_blocks':11,
        'input_provenance':input_provenance(verified,run_id,stage_id),
        'input_counts':verified['counts'],'comparison_trace':comparison_trace(x)}


def build_rows(x, s):
    by={(r['input_id'],r['id']):r for r in x['records']}
    cm={(c['city_id'],c['label']):c for c in x['comparisons']}
    rows=[];formats=[]
    def add(v,fmt=None):rows.append(v+['']*(14-len(v)));formats.append(fmt)
    add(['介護保険解析 候補 v3／PLAN 2.4／ROLE20 全件再評価待ち'])
    add(['完成・暫定提出ではありません。日本語表示は未合格。正式資料待ちの主解析値・比較は保留を維持します。'])
    add(['主解析：S01 2025/4/1～9/30・11/30締切／S02 2024/10/1～2025/3/31・6/30締切。人口は2025年1月、合算禁止。'])
    add(['優先結果 R02–R07：数値・元セル・通常/補正・母集団は下表で照合。差は有効入力同士のみ。'])
    for req in ['R02','R03','R04','R05','R06','R07']:
        rs=[r for r in x['records'] if r['input_id']=='S01' and req in r.get('requirements',[])];hc=sum(r['status']!='valid' for r in rs)
        add([req,'S01対象指標',len(rs),'うち保留/欠損',hc,'保留の比較・結論は除外。提供補正値の個票再算出は未実施。'])
        priority=[r for r in rs if r['region']=='市' and r['adjustment']=='通常'][:2]
        for r in priority:
            add([req+' 優先指標',r.get('item_name') or r['row_label'],r['population'],r['value'] if r['status']=='valid' else '保留',r['unit'],r['source_ref']['sheet']+'!'+r['source_ref']['cell']+' / '+r['status']], 'headline_ratio' if r['unit']=='比率' else 'headline_days' if r['unit']=='日' else 'headline_count')
    add(['C03：既存作業コピーの9セル修正を検証して再利用。原本・旧候補は変更せず、再適用なし。'])
    add(['C04：市の表示はS10 R7年度・市独自集計25.6日へ置換（S01第2回値の復元ではない）。元値は監査記録、県・全国/第1回比較と原因結論は対象外。'])
    add(['C10：第５群!P70破損見出しとH/J/L/N/P/R71:73。地域推定せず、依存グラフ・結論は未検証。'])
    add(['C11：S01比率14セル/S02比率16セル、ゼロ分子3セルを含め正式分母待ち。件数の有効値と区別。'])
    add(['C09：分母0により未算出（0%ではない）。原数式エラーを保持。新たな正式資料待ちではない。'])
    add(['S10 業務参考（年度・母集団・方法が主解析と異なる。参考値で主解析の保留を解除しない）'])
    add(['参考ID','内容','年度/範囲','掲載値','状態','資料位置/方法・利用制限'])
    for b in s['blocks']:
        ms=[m for m in s['supplemental_metrics'] if m['block_id']==b['id']]
        if not ms:add([b['id'],'運用背景','年度・予定は資料内文脈に従う','','','参考専用','','','','','','','S10本文2068/2199/2203/2541/2542','資料記載、主解析比較不可'])
        for m in ms:
            sr=m['source_ref'];locator='S10 XML表 '+str(sr.get('table_index_0based',sr['tables']))+' 行'+str(sr.get('row_index_0based','-'))+' セル'+str(sr.get('cell_index_0based','-'))
            add([m['id'],m['title'],'.'.join(sr['logical_path'])+(' 予定' if m['planned'] else ''),m['raw_source_value'] if m['raw_source_value'] is not None else '欠損',m['unit'] or '件',m['status'],'','','','','','',locator,m['method_caution'] or '業務参考・主解析比較不可'], 'supplement_days' if m['unit']=='日' else 'supplement_percent' if 'percent' in '.'.join(sr['logical_path']) or m['unit']=='percent_as_printed' else 'supplement_count')
    add(['C12：R7待ち理由 合算4417・再掲控除3993・掲載3393。差600は未解決、理由構成比を不採用。'])
    add(['C13：R7日数は市独自集計・厚労省公表後差替予定。比較改善・原因の結論に使わない。R7空欄は欠損。'])
    add(['C14：R8委託計画2920対2600+324=2924。差4は保留、実績と予定を混在させない。'])
    add(['S10-11：郵送・14日取寄せ・研修・6か月委員組替えは資料記載の運用背景。現行法独立確認ではない。'])
    add(['指標ID','区分','期間または基準日','通常または補正','単位','市','県','全国','第1回参考値','県差','全国差','提供期間差','元セル','判定']);header=len(rows)
    def v(r):return r['value'] if r and r['status']=='valid' else ('保留' if r else '対象外')
    for r in x['records']:
        if r['input_id']!='S01' or r['region']!='市':continue
        links={k:cm.get((r['id'],k)) for k in ['県差','全国差','提供期間差']}
        def other(k):
            c=links[k]
            if c:return by.get((c['reference_input'],c['reference_id']))
            if k=='提供期間差':return by.get(('S02',r['id']))
            region={'県差':'県','全国差':'全国'}[k]
            matches=[q for q in x['records'] if q['input_id']=='S01' and q['region']==region and all(q.get(f)==r.get(f) for f in ['table_id','row_label','unit','adjustment','population','kind'])]
            return matches[0] if len(matches)==1 else None
        c04=(r['id']=='IV.days.survey:J208')
        def diff(k):
            if c04:return '対象外'
            c=links[k];return c['value'] if c and c['status']=='valid' else ('保留' if c else '対象外')
        label=' / '.join(str(z) for z in [r.get('item_name') or r['table_id'],r.get('population_scope') or r['population'],r.get('statistic_kind') or r['kind'],r['row_label']])
        trace=[r]+[other(k) for k in ['県差','全国差','提供期間差']]
        source=' / '.join(q['source_ref']['input']+' '+q['source_ref']['sheet']+'!'+q['source_ref']['cell'] for q in trace if q)
        if c04:
            period='令和7年度・市独自年度集計（S10）';status='provided_substitute：S01第2回の復元ではない';value=25.6
            source='S10 表62 R7 市 調査日数（元S01値は監査ログ）'
        else:
            period=r['period'];status=r['status']+(' '+r['reason'] if r['reason'] else '');value=v(r)
        add([r['id'],label,period,r['adjustment'],'%' if r['unit']=='比率' else r['unit'],value,v(other('県差')) if not c04 else '対象外',v(other('全国差')) if not c04 else '対象外',v(other('提供期間差')) if not c04 else '対象外',diff('県差'),diff('全国差'),diff('提供期間差'),source,status], 'ratio' if r['unit']=='比率' else ('days' if r['unit']=='日' else 'count'))
    return rows,formats,header


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--extraction',type=Path,required=True)
    p.add_argument('--run-manifest',type=Path,required=True)
    p.add_argument('--expected-run-id',required=True)
    p.add_argument('--expected-stage-id',required=True)
    p.add_argument('--supplement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    verified=verify_extraction_manifest(a.extraction,a.run_manifest,a.expected_run_id,a.expected_stage_id)
    x=verified['extraction'];s=json.loads(a.supplement.read_text(encoding='utf-8'))
    result=build_summary(x,s,verified,a.expected_run_id,a.expected_stage_id)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    if a.out.exists():raise FileExistsError('summary output already exists: '+str(a.out))
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'rows':len(rows),'comparison_trace_count':len(result['comparison_trace']),
        'source_run_id':a.expected_run_id,'source_stage_id':a.expected_stage_id,
        'extraction_sha256':verified['extraction_sha256']},ensure_ascii=False))


if __name__=='__main__':main()
