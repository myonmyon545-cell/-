"""Prepare Artifact Tool sheet values from the verified aggregate analysis."""
import argparse
import json
from pathlib import Path
from inspect_inputs import write_json


def ref(row):
    r = row['source_ref']
    return r['input'] + ' ' + r['sheet'] + '!' + r['cell']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--definitions', type=Path, required=True)
    p.add_argument('--extraction', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    defs = json.loads(a.definitions.read_text())
    result = json.loads(a.extraction.read_text())
    metrics = result['records']
    comparisons = result['comparisons']
    if len(metrics) != 6316 or len(comparisons) != 1478:
        raise ValueError('candidate source coverage mismatch')
    held = sum(r['status'] != 'valid' for r in metrics)
    valid_c = sum(c['status'] == 'valid' for c in comparisons)
    guide = [
        ['介護保険データ解析 候補 v1（独立評価待ち）', '', '', ''],
        ['項目', '値・状態', '根拠', '評価範囲'],
        ['元表', 'S01 作業コピー', '原本のSHA256は変更なし', '原14シート・148グラフ'],
        ['C03', '修正済み', 'Ⅰ!G513:G521 9セル / ROLE20 PASS', '作業コピーのみ'],
        ['処理対象', len(metrics), 'S01/S02 各3158掲載値', '全章の元セル付き'],
        ['保留・欠損', held, '入力別状態を採用', '値と比較は抑止'],
        ['比較', len(comparisons), '市・県・全国・提供期間', f'有効 {valid_c} / 保留 {len(comparisons)-valid_c}'],
        ['E20-01', '定義適用', '36表648指標＋認定率12指標', '20の再評価待ち'],
        ['C10', '保留', '薬の内服 H/J/L/N/P/R71:73・P70', '地域見出し・数値の正式資料待ち'],
        ['C11', '保留', '不一致27＋ゼロ分子3', '正式分母待ち'],
        ['C04', '保留', '調査依頼日・実施日', '元集計または個票日付待ち'],
        ['C09', '未算出', '軽度変更構成比の分母0', '原数式エラーは保持'],
        ['表示', '未確認', '実行環境に日本語フォントなし', '20が日本語表示を要確認'],
        ['利用上の注意', '候補・評価待ち', '保留値の結論を出さない', '完成/暫定提出ではない'],
    ]
    metric_rows = [[
        '入力', '指標ID', '項目名', '対象区分', '統計種類', '選択肢/行',
        '地域', '補正', '状態', '採用値', '元掲載値', '単位',
        '元セル', '理由', '期間',
    ]]
    for r in metrics:
        metric_rows.append([
            r['input_id'], r['id'], r.get('item_name') or r.get('certification_kind') or r['table_id'],
            r.get('population_scope') or r['population'], r.get('statistic_kind') or r.get('definition') or r['kind'],
            r['row_label'], r['region'], r['adjustment'], r['status'],
            r['value'] if r['status'] == 'valid' else None, r['source_value']
                if isinstance(r['source_value'], (int, float, str)) else None,
            r['unit'], ref(r), r['reason'] or '', r['period'],
        ])
    comparison_rows = [[
        '比較ID', '市指標', '参照指標', '参照入力', '比較', '状態',
        '差', '単位', '対象区分', '補正', '理由',
    ]]
    for c in comparisons:
        comparison_rows.append([
            c['id'], c['city_id'], c['reference_id'], c['reference_input'],
            c['label'], c['status'], c['value'] if c['status'] == 'valid' else None,
            c['unit'], c['population'], c['adjustment'], c.get('reason') or '',
        ])
    definition_rows = [['種別', '項目ID', '項目名/率種', '対象区分・定義', '見出し元セル', '統計・分母']]
    for t in defs['table_inventory']:
        if t['id'].startswith('II.focus.'):
            definition_rows.append(['5項目', t['id'], t['item_name'], t['population_scope'],
                                    t['sheet'] + '!' + (t['population_heading_cell'] or t['item_title_cell']),
                                    t['statistic_rule']])
    cert = defs['table_inventory']
    cert = next(t for t in cert if t['id'] == 'I.certification.summary')
    for row, x in sorted(cert['row_semantics'].items(), key=lambda kv: int(kv[0])):
        definition_rows.append(['認定率', 'I.certification.summary:' + str(row), x['name'], x['definition'],
                                x['heading'], x['numerator_ref'] + '/' + x['denominator_ref']])
    definition_rows += [
        ['保留', 'C10:P70', '地域見出し異常', 'S01=644821 / S02=618046', 'Ⅱ調査項目データ（第５群）!P70', '地域名を推定しない'],
        ['保留', 'C11', '申請区分別変更率', '比率30入力別レコード', 'Ⅲ審査判定データ（変更率）', '正式対象/除外ケース分母待ち'],
        ['保留', 'C04', '調査日数', 'S01/S02', 'Ⅳ事務データ!J208', '日付・元集計待ち'],
        ['未算出', 'C09', '軽度変更構成比', '分母0', 'Ⅲ審査判定データ（変更率）!N110:N116', '数式エラーは0にしない'],
        ['表示', 'E01', '日本語字形', '実行環境にフォントなし', '候補全体', '20が別環境で確認'],
        ['条件', 'C37:C38', '二次判定例外', '非該当/非該当以外で補正条件が異なる',
         'Ⅱ（３）５項目!C37:C38', '個票補正の実施と同一視しない'],
    ]
    payload = {'schema': 'care_candidate_tables/v1', 'candidate_id': 'care-S01-20261009-v1',
               'guide': guide, 'metrics': metric_rows, 'comparisons': comparison_rows,
               'definitions': definition_rows,
               'checks': {'metrics': len(metric_rows)-1, 'held_or_missing': held,
                          'comparisons': len(comparison_rows)-1,
                          'valid_comparisons': valid_c, 'focus_definitions': 36,
                          'certification_definitions': 3}}
    write_json(a.out, payload)
    print(json.dumps(payload['checks'], ensure_ascii=False))


if __name__ == '__main__':
    main()
