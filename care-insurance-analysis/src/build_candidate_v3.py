"""Freeze the 2.4 candidate package after the C04 display-only substitution."""
import argparse, hashlib, json, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

def main():
    p=argparse.ArgumentParser()
    for name in ('bundle','candidate_pre_c04','candidate','source_copy','previous_package','supplement','out','result'):
        p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    p.add_argument('--code-commit',required=True)
    a=p.parse_args(); b=a.bundle.resolve();
    sys.path.insert(0,str(b/'src'));sys.path.insert(0,str(b/'tools'))
    from preserve_package import sheets_by_name,xml
    from inspect_inputs import NS,sha
    from verify_handoff import check_package
    with zipfile.ZipFile(a.candidate_pre_c04) as z:
        parts={n:z.read(n) for n in z.namelist()}
        target=sheets_by_name(z,'xl/workbook.xml')['Ⅳ事務データ']; root=ET.fromstring(parts[target])
        cell=root.find('.//m:c[@r="J208"]',NS); assert cell is not None and cell.find('m:f',NS) is None
        value=cell.find('m:v',NS); old=float(value.text); assert abs(old-0.023503077783995522)<1e-15
        value.text='25.6';parts[target]=xml(root)
    with zipfile.ZipFile(a.candidate,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in parts.items():z.writestr(n,data)
    pkg=json.loads(a.previous_package.read_text());supp=json.loads(a.supplement.read_text())
    pkg.update(plan_revision='2.4',candidate={'id':'care-S01-20261010-v3','version':3,'sha256':sha(a.candidate.read_bytes())},
               code_commit=a.code_commit,source_copy_sha256=sha(a.source_copy.read_bytes()),
               S10_application_sha256=sha(a.supplement.read_bytes()),supplemental_metrics=supp['supplemental_metrics'],
               required_supplemental_metrics=[m['id'] for m in supp['supplemental_metrics']],
               template_source='S01原14シート＋先頭分析要点1枚。C03確認済み作業コピーを再利用し重複適用なし。C04は明示承認のS10表示置換。',
               scope='2.4候補。C04置換適用。C10/C11/C09は保留表示。20の初回全範囲独立評価待ち。E01の日本語表示は未合格。完成・暫定提出ではない。')
    pkg['input_hashes']['S10']=supp['source']['sha256']
    pkg['hold_policy'].update(C04='S10 R7市独自集計25.6日を表示置換。S01 raw値は監査保存。S01期間の復元ではなく比較と原因結論を抑止。',
        C10='破損P70を含む両入力の対象値は採用null・比較抑止。正式元集計待ち。',
        C11='S01 14率/S02 16率とゼロ分子3率を保留。正式分母待ち。',E01='日本語字形の実描画合格なし。')
    key='S01::IV.days.survey:J208';row=next(r for r in pkg['metrics'] if r['id']==key)
    row.update(status='provided_substitute',value=25.6,reason='承認済表示置換：S10 R7年度市独自集計25.6日。S01第2回期間の復元ではなく比較不可。',
        substitution_source_ref={'input':'S10','table_index_0based':62,'year':'R7','region':'市','statistic':'認定調査日数','period':'令和7年度・市独自年度集計'},
        original_source_status='held',original_raw_source_value=old)
    row['evidence_sha256']=hashlib.sha256(json.dumps({k:v for k,v in row.items() if k!='evidence_sha256'},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    for c in pkg['comparisons']:
        if key in c.get('depends_on',[]):c.update(status='held',value=None,reason='C04：異なる年度・母集団の代替値のため比較抑止')
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(pkg,ensure_ascii=False,indent=2)+'\n')
    check=check_package(pkg,expected_revision='2.4',workbook=a.candidate)
    check.update(core_metrics=len(pkg['metrics']),core_comparisons=len(pkg['comparisons']),supplemental_metrics=len(pkg['supplemental_metrics']),
        core_values_and_states_exactly_retained_except_C04=True,supplemental_core_comparison_edges=0,
        independent_evaluation='pending_plan_2.4',release='not_released',display='held_E01',
        C04={'status':'provided_substitute','display_value':25.6,'original_value_audit':old,'comparisons_suppressed':True})
    a.result.write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'candidate':pkg['candidate'],'fingerprint':check['candidate_fingerprint'],
        'valid_metrics':check['valid_metrics'],'held_or_absent':check['held_or_absent'],'release':'not_released'}))
if __name__=='__main__':main()
