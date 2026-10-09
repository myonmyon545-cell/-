"""Freeze source-cell contracts and known issue evidence before extraction."""
import argparse
import json
import re
from pathlib import Path
from inspect_inputs import write_json, sha

def colnum(name):
    n=0
    for c in name: n=n*26+ord(c)-64
    return n

def main():
    p=argparse.ArgumentParser();p.add_argument('--inspection',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    data={k:json.loads((a.inspection/(k+'_cells.json')).read_text()) for k in ['S01','S02','S03']}
    target=data['S01']; sheets={s['name']:s for s in target['sheets']}
    tables=[]
    def add(tid,sh,ranges,req,pop,unit,adjustment='通常',rules=None):
        tables.append({'id':tid,'sheet':sh,'ranges':ranges,'requirements':req,'population':pop,
                       'units':unit,'adjustment':adjustment,'rules':rules or [],'input':'S01'})
    basic='Ⅰ基礎情報';period='2025-04-01～2025-09-30（申請日基準、2025-11-30格納締切）'
    add('I.population',basic,['G129:Q139','T129:Z139'],['R02'],'2025年1月基準の住民基本台帳人口',['人','比率'],rules=['G129総人口、G130 65歳以上、G131 75歳以上、G132 85歳以上','K/N/Qは65歳以上人口分母、T/W/Zは総人口分母'])
    add('I.certification',basic,['F260:AA270'],['R03'],'2025年1月基準の第1号被保険者認定者／65歳以上人口',['人','比率'],rules=['F260=65歳以上人口、F261=第1号認定者、F262=軽度、F263=中重度','I/O/R認定者構成、U/X/AA人口認定率、Lは年齢補正認定者構成'])
    add('I.certification.summary',basic,['D287:W287','D324:W324','D355:W355'],['R03'],'第1号被保険者／65歳以上人口',['比率'],'通常と年齢補正を別指標',rules=['D通常市、J市年齢補正、Q通常県、W通常全国','県の補正値は未掲載。比較先を創作しない'])
    add('I.dementia',basic,['G390:Z400'],['R04'],'認知症高齢者自立度の有効ケース',['件','比率'],rules=['G/N/U件数、K/R/Z構成比','II以上はIIa+IIb+IIIa+IIIb+IV+M、III以上はIIIa+IIIb+IV+M'])
    add('I.disability',basic,['G452:Z462'],['R04'],'障害高齢者自立度の有効ケース',['件','比率'],rules=['B以上はB1+B2+C1+C2、分母は当該表全体'])
    add('I.first_decision_duplicate',basic,['G513:Y521'],['R06'],'一次判定結果の有効ケース',['件','比率'],'通常／有効期間・年齢補正',rules=['G513:G521はC03で保留。IIIの正しい内訳を二重集計しない','K/N/QとU/Yは提供比率を別条件で保持'])
    selection_count=0
    for s in target['sheets'][3:9]:
        cells=s['cells']; first=s['name'].endswith('（第１群）'); other=s['name'].endswith('（その他）')
        if not other:
            row=188 if first else 8
            add('II.score.'+str(target['sheets'].index(s)-2),s['name'],[f'G{row}:W{row}'],['R05'],'集計対象ケースの提供中間評価項目得点',['点'],'通常／有効期間・年齢補正',rules=['G/K/O通常市県全国、S/W補正市全国','個票と公式採点規則なしに再採点しない'])
        headers=sorted(int(ref[1:]) for ref,c in cells.items() if re.fullmatch(r'H\d+',ref) and c['value']=='三島市' and cells.get('C'+ref[1:],{}).get('value')=='選択肢')
        for header in headers:
            rows=[]
            r=header+1
            while isinstance(cells.get('H'+str(r),{}).get('value'),(int,float)) and isinstance(cells.get('C'+str(r),{}).get('value'),str):
                rows.append(r);r+=1
            if not rows: raise ValueError('selection table has no rows: '+s['name']+str(header))
            label=cells.get('C'+str(header-2),{}).get('value')
            tid=f'II.selection.{target["sheets"].index(s):02}.{header}'
            add(tid,s['name'],[f'H{rows[0]}:R{rows[-1]}'],['R05'],'当該調査項目の有効ケース',['件','比率'],rules=['H/L/P選択件数、J/N/R選択率','当該表から有効件数を確認。複数選択を100%に強制しない'])
            tables[-1].update({'label':label,'header_row':header,'data_rows':rows,'count_columns':['H','L','P'],'ratio_columns':['J','N','R'],'choice_column':'C'})
            selection_count+=1
    focus=target['sheets'][9]
    headers=sorted(int(re.search(r'\d+',r).group()) for r,c in focus['cells'].items() if c['value']=='選択' and r.startswith('P'))
    for r in headers:
        data_rows=[];i=r+1
        while isinstance(focus['cells'].get('P'+str(i),{}).get('value'),str) and any(isinstance(focus['cells'].get(col+str(i),{}).get('value'),(int,float)) for col in ['R','S']):
            data_rows.append(i);i+=1
        if data_rows:
            add(f'II.focus.{r}',focus['name'],[f'P{data_rows[0]}:AD{data_rows[-1]}'],['R05'],'一次判定区分を限定した当該調査項目の有効ケース',['比率'],'有効期間・年齢補正',rules=['提供選択率と自治体分布統計。個票なし再算出を称しない','左下肢・右下肢は原定義の1-1麻痺に属する。5項目を6項目と数えない'])
            tables[-1]['data_rows']=data_rows
    decision=target['sheets'][10]['name']
    add('III.first_decision',decision,['G128:Y136'],['R06'],'一次判定の有効ケース',['件','比率'],'通常／有効期間・年齢補正',rules=['G件数、K/N/Q通常比率、U/Y補正比率'])
    add('III.second_decision',decision,['G191:Y199'],['R06'],'二次判定の有効ケース',['件','比率'],'通常／有効期間・年齢補正',rules=['周辺集計から移行表や変更件数を復元しない'])
    change=target['sheets'][11]['name']
    specs=[('all',67,69),('severity_composition',101,108),('mild_composition',109,116),('severe_within',129,136),('mild_within',249,256),('new_application',369,371),('renewal',430,432),('category_change',491,493),('previous_to_current',552,555),('previous_milder',615,617),('previous_same',676,678),('previous_severer',737,739)]
    for tid,start,end in specs:
        add('III.change.'+tid,change,[f'H{start}:AA{end}'],['R06'],'同表の対象ケース。構成比と区分内変更率を区別',['件','比率'],rules=['要支援2と要介護1の相互変更は変化なし','分母0の構成比は未算出。C09 N110:N116を0%にしない'])
    validity=target['sheets'][12]['name']
    for tid,start,end in [('all',67,72),('support1',87,92),('support2',106,111),('care1',132,137),('care2',150,155),('care3',168,173),('care4',195,200),('care5',214,219)]:
        add('III.validity.'+tid,validity,[f'H{start}:Z{end}'],['R06'],'当該二次判定区分の認定有効期間有効ケース',['件','比率'],rules=['区分1-6、7-12、13-24、25-36、37-48か月','開始日が1日以外は翌月を起点。48月超等を最終区分へ押し込まない'])
    office=target['sheets'][13]['name']
    add('IV.insured',office,['J129:Z132'],['R07'],'期間中の集計対象申請ケース',['件','比率'])
    add('IV.application',office,['J150:Z153'],['R07'],'期間中の集計対象申請ケース',['件','比率'])
    for tid,n,r in [('opinion',189,190),('survey',207,208),('recognition',225,226)]:
        add('IV.days.'+tid,office,[f'J{n}:Z{r}'],['R07'],'当該日数指標の地域別有効ケース',['件','日'],rules=['日数は提供平均の転記と整合確認のみ。個票なし再計算しない','判定日を越す日付の除外。申請日前の依頼・同日を一律除外しない'])
    definitions={'schema':'care_definitions/v1','plan_revision':'2.2','period':period,
                 'stock_basis':'2025年1月。S01/S02で同じストックを合算しない',
                 'table_inventory':tables,'selection_tables':selection_count,
                 'required_metric_id_rule':'table_id:cell。セル列は地域と補正区分を一意に表し、これらは各レコードの明示フィールドにも保持。台帳の実掲載値を列挙。未掲載の県補正値を創作せず、補助領域と重複を除く',
                 'source_auxiliary_rule':'AR以降のグラフ補助は別領域。印刷範囲を超える補助値を二重集計しない。元分布統計はprovided',
                 'differences':'比率差=100*(市-比較先) pp、日数差=市-比較先。通常と補正を混ぜない',
                 'known_issue_policy':{'C03':'10照合済み、20独立照合前は原セルを修正しない','C04':'市調査期間の比較と原因説明を保留','C09':'軽度変更数0の構成比は未算出。原数式エラーを既存不整合として区別','C10':'第5群の薬の内服表は件数と掲載割合が不一致。件数・割合の比較を保留し元集計の確認を要する','C11':'申請区分別変更率の掲載比率と同表対象件数分母が不一致のセルを保留。除外ケースや別分母を推測しない'},
                 'national_scope':'期間中500件以上送信自治体の対象全ケース。自治体比率の単純平均ではない'}
    write_json(a.out/'definitions.json',definitions)
    get=lambda sheet,ref:sheets[sheet]['cells'][ref]['value']
    old=[get(basic,'G'+str(r)) for r in range(513,522)]
    new=[get(decision,'G'+str(r)) for r in range(128,137)]
    labels_ok=all(get(basic,'C'+str(i))==get(decision,'C'+str(j)) for i,j in zip(range(513,522),range(128,137)))
    ratio_ok=all(abs(new[i]/new[-1]-get(basic,'K'+str(513+i)))<1e-10 for i in range(8))
    errors=[{'sheet':s['name'],'cell':r,'value':c['value'],'formula':c['formula'],'formula_attributes':c['formula_attributes']} for s in target['sheets'] for r,c in s['cells'].items() if c['type']=='e']
    evidence={'schema':'care_startup_checks/v1','plan_revision':'2.2',
              'C03':{'status':'HELD','role10_label_match':labels_ok,'original_counts':old,'proposed_counts':new,'proposed_parts_sum':sum(new[:-1]),'total':new[-1],'I_ratio_matches_III':ratio_ok,'IV_total':get(office,'J132'),'applied':False,'needs':'ROLE=20による独立照合'},
              'C04':{'status':'HELD','city_current':get(office,'J208'),'city_prior':data['S02']['sheets'][13]['cells']['J208']['value'],'valid_n':get(office,'J207'),'needs':'元送信・集計結果または個票の調査依頼日・実施日'},
              'C09':{'status':'HELD','source_errors':errors,'denominator':get(change,'J109'),'needs':'候補では未算出と明記。原表修正する場合は明示した根拠と独立評価'},
              'R5_template':{'sheet_names_same':[s['name'] for s in target['sheets']]==[s['name'] for s in data['S03']['sheets']], 'chart_counts':[target['chart_count'],data['S03']['chart_count']],'cover_text':data['S03']['sheets'][0]['cells']['C51']['value']},
              'manual':{'M01':'本文・Toolセル読取り確認済み。CSV・列定義・認定ソフト・VBA実行環境なし','M02_M04':'入力環境待ち','main_path_dependency':False},
              'table_counts':{'all':len(tables),'survey_selection':selection_count,'focus':sum(t['id'].startswith('II.focus.') for t in tables)},
              'source_numeric_errors_count':len(errors)}
    if not labels_ok or not ratio_ok or sum(new[:-1])!=new[-1] or new[-1]!=get(office,'J132'): raise ValueError('C03 repair evidence does not agree')
    write_json(a.out/'startup_checks.json',evidence)
    print(json.dumps({'tables':len(tables),'selection_tables':selection_count,'C03':'role10 proof agrees; correction not applied','C04':'HELD','C09_errors':len(errors)},ensure_ascii=False))

if __name__=='__main__': main()
