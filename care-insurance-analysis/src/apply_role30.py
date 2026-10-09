"""Apply source-verified ROLE=30 semantic and hold corrections to T02/T05.

No source workbook is edited. The candidate builder consumes the resulting
input-specific records and must never infer validity from the inventory's
shared top-level status.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

from inspect_inputs import sha, write_json

SOURCE_HASHES = {
    'S01': '5721ee2b38cb8f55f973f149fe32f67dcfe5453645fcfdccdb934b169bcd2a2d',
    'S02': '9b29b315bf310770295e8fe60ba2953362f3cff21b3d78adfe255c42f2c26304',
}
STATS = {
    'R': '最小値', 'S': '最小値',
    'T': '第1四分位点', 'U': '第1四分位点',
    'V': '中央値', 'W': '中央値',
    'X': '第3四分位点', 'Y': '第3四分位点',
    'Z': '最大値', 'AA': '最大値',
    'AB': '三島市の提供選択率', 'AC': '三島市の提供選択率',
}
RATIO_IDS = {'III.change.new_application:N371', 'III.change.renewal:N432'}
COLS_C10 = ('H', 'J', 'L', 'N', 'P', 'R')


def normal(s):
    return ''.join(str(s or '').split())


def metric_evidence(row):
    payload = {
        'input_hash': row['input_hash'],
        'source': {k: row['source_ref'][k] for k in ('sheet', 'cell')},
        'period': row['period'], 'population': row['population'],
        'adjustment': row['adjustment'], 'source_value': row['source_value'],
    }
    return sha(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                          separators=(',', ':'), allow_nan=False).encode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--proposal', type=Path, required=True)
    ap.add_argument('--inspection', type=Path, required=True)
    ap.add_argument('--contract', type=Path, required=True)
    ap.add_argument('--calculation', type=Path, required=True)
    ap.add_argument('--checks', type=Path, required=True)
    args = ap.parse_args()
    proposal = json.loads(args.proposal.read_text())
    issues = {x['id']: x for x in proposal['issues']}
    for issue in ['E20-01', 'C11', 'C10', 'STATUS-PROPAGATION']:
        if issue not in issues:
            raise ValueError('ROLE=30 proposal missing ' + issue)
    books = {}
    manifest = json.loads((args.inspection / 'input_manifest.json').read_text())
    for sid in SOURCE_HASHES:
        if manifest[sid]['sha256'] != SOURCE_HASHES[sid]:
            raise ValueError(sid + ' input hash differs from independent evidence')
        books[sid] = {s['name']: s['cells'] for s in
                      json.loads((args.inspection / (sid + '_cells.json')).read_text())['sheets']}
    definitions_path = args.contract / 'definitions.json'
    inventory_path = args.contract / 'metric_inventory.json'
    extraction_path = args.calculation / 'extracted_values.json'
    defs = json.loads(definitions_path.read_text())
    inv = json.loads(inventory_path.read_text())
    result = json.loads(extraction_path.read_text())
    tmap = {t['id']: t for t in defs['table_inventory']}
    focus = issues['E20-01']['change']['focus_table_mapping']
    if len(focus) != 36 or len({x['table_id'] for x in focus}) != 36:
        raise ValueError('focus table mapping must cover exactly 36 tables')
    focus_by_id = {x['table_id']: x for x in focus}
    for f in focus:
        table = tmap[f['table_id']]
        sheet = f['source_sheet']
        for sid in SOURCE_HASHES:
            cells = books[sid][sheet]
            title = cells[f['item_title_cell']]['value']
            if normal(title) != normal(f['item_name']):
                raise ValueError(sid + ' focus item title mismatch ' + f['table_id'])
            hcell = f['population_heading_cell']
            if hcell and normal(f['population_scope'].split('：')[-1]) not in normal(cells[hcell]['value']):
                raise ValueError(sid + ' focus population mismatch ' + f['table_id'])
            head = f['statistics_heading_row']
            for pair, label in [('P', '選択'), ('RS', '最小値'), ('TU', '第1四分位点'),
                                ('VW', '中央値'), ('XY', '第3四分位点'), ('Z,AA', '最大値')]:
                options = pair.split(',') if ',' in pair else list(pair)
                if not any(normal(cells.get(col + str(head), {}).get('value')) == normal(label) for col in options):
                    raise ValueError(sid + ' focus statistic heading mismatch ' + f['table_id'])
        table.update({
            'item_id': f['item_id'], 'item_name': f['item_name'],
            'item_title_cell': f['item_title_cell'],
            'population_scope': f['population_scope'],
            'population_heading_cell': f['population_heading_cell'],
            'statistics_heading_row': f['statistics_heading_row'],
            'population': f['population_scope'],
            'statistic_rule': 'R/S～Z/AAは500件以上送信自治体の分布統計、AB/ACは三島市の提供選択率',
            'focus_exception_source_refs': ['Ⅱ（３）５項目!C37', 'Ⅱ（３）５項目!C38'],
        })
    certrows = {x['row']: x for x in issues['E20-01']['change']['certification_rows']}
    if set(certrows) != {287, 324, 355}:
        raise ValueError('certification summary rows incomplete')
    for sid in SOURCE_HASHES:
        cells = books[sid]['Ⅰ基礎情報']
        for row, x in certrows.items():
            if normal(x['name']) not in normal(cells[x['heading'].split('!')[1]]['value']):
                raise ValueError(sid + ' certification title mismatch ' + str(row))
            if cells[x['denominator_ref']]['value'] <= 0:
                raise ValueError(sid + ' certification denominator missing')
    certtable = tmap['I.certification.summary']
    certtable['row_semantics'] = certrows
    certtable['column_semantics'] = issues['E20-01']['change']['certification_columns']
    certtable['population'] = '各行の軽度・中重度を区別した第1号認定者数／65歳以上人口。J列は提供年齢補正値'
    c10 = issues['C10']['change']
    expected_ranges = {f'{col}71:{col}73' for col in COLS_C10}
    if c10['held_header_cell'] != 'P70' or set(c10['held_numeric_cells']) != expected_ranges:
        raise ValueError('C10 proposal range differs from 18 known numeric cells')
    for sid in SOURCE_HASHES:
        c = books[sid][c10['sheet']]
        if not isinstance(c['P70']['value'], (int, float)) or '薬の内服' not in c['C68']['value']:
            raise ValueError(sid + ' C10 header evidence differs')
    tmap['II.selection.07.70']['header_issue'] = {
        'status': 'held', 'source_ref_by_input': {
            sid: {'input': sid, 'sheet': c10['sheet'], 'cell': 'P70',
                  'raw_value': books[sid][c10['sheet']]['P70']['value']} for sid in SOURCE_HASHES},
        'reason': 'C10:P70の地域見出しが数値。正式な地域名・列位置は未確定',
    }
    defs['known_issue_policy']['C10'] = '薬の内服H/J/L/N/P/R71:73は入力別にheld。P70見出し異常を別記。P/R地域名を推定しない'
    defs['known_issue_policy']['C11'] = '申請区分別30比率は入力別held。ゼロ分子3件をvalidへ戻さず正式分母待ち'
    defs['role30_proposal'] = {'report_blob_sha': 'd46d6c69f11d0b1457a04e58acc9c2e032ccabe3',
                               'source_commit': proposal['source_commit']}
    metric_index = {m['id']: m for m in inv['metrics']}
    record_index = {(r['input_id'], r['id']): r for r in result['records']}
    if len(metric_index) != 3158 or len(record_index) != 6316:
        raise ValueError('fixed inventory/record counts differ')
    focus_count = cert_count = c10_count = c11_count = 0
    for mid, m in metric_index.items():
        t = tmap[m['table_id']]
        ref = m['source_ref']['cell']
        col = ''.join(c for c in ref if c.isalpha())
        rownum = int(''.join(c for c in ref if c.isdigit()))
        if m['table_id'] in focus_by_id:
            f = focus_by_id[m['table_id']]
            pair = (('R', 'S') if col in ('R', 'S') else
                    ('T', 'U') if col in ('T', 'U') else
                    ('V', 'W') if col in ('V', 'W') else
                    ('X', 'Y') if col in ('X', 'Y') else
                    ('Z', 'AA') if col in ('Z', 'AA') else ('P',))
            headref = next((c + str(f['statistics_heading_row']) for c in pair
                            if books['S01'][f['source_sheet']].get(c + str(f['statistics_heading_row']), {}).get('value') is not None), None)
            m.update({'item_id': f['item_id'], 'item_name': f['item_name'],
                      'population_scope': f['population_scope'],
                      'population': f['population_scope'],
                      'statistic_kind': STATS[col],
                      'heading_source_ref': {
                          'item': {'sheet': f['source_sheet'], 'cell': f['item_title_cell']},
                          'population': ({'sheet': f['source_sheet'], 'cell': f['population_heading_cell']}
                                         if f['population_heading_cell'] else None),
                          'statistic': {'sheet': f['source_sheet'], 'cell': headref},
                      },
                      'region': '市' if col in ('AB', 'AC') else '500件以上送信自治体分布',
                      'focus_exception': 'C37:C38の二次判定例外条件を個票補正済みとはみなさない'})
            focus_count += 1
        if m['table_id'] == 'I.certification.summary':
            x = certrows[rownum]
            m.update({'row_label': x['name'], 'certification_kind': x['name'],
                      'definition': x['definition'],
                      'numerator_source_ref': {'sheet': 'Ⅰ基礎情報', 'cell': x['numerator_ref']},
                      'denominator_source_ref': {'sheet': 'Ⅰ基礎情報', 'cell': x['denominator_ref']},
                      'population': x['definition'],
                      'ratio_basis': '65歳以上人口分母',
                      'region_adjustment_label': certtable['column_semantics'][col]})
            if col == 'J':
                m['verification_scope'] = '年齢補正の提供値。元件数からの再算出不可'
            cert_count += 1
        if m['table_id'] == 'II.selection.07.70' and col in ('P', 'R'):
            m['region'] = '未確定（P70見出し異常）'
            m['header_issue'] = 'C10:P70'
            c10_count += 1
        for sid in SOURCE_HASHES:
            r = record_index[(sid, mid)]
            for key in ('item_id', 'item_name', 'population_scope', 'statistic_kind',
                        'heading_source_ref', 'focus_exception', 'certification_kind',
                        'definition', 'numerator_source_ref', 'denominator_source_ref',
                        'ratio_basis', 'region_adjustment_label', 'header_issue'):
                if key in m: r[key] = m[key]
            r['population'] = m['population']
            r['region'] = m['region']
            if m['table_id'] == 'II.selection.07.70':
                if r['status'] != 'held':
                    raise ValueError('C10 numeric value no longer held ' + sid + ' ' + mid)
                if col in ('P', 'R'):
                    r['reason'] = 'C10:P70地域見出し異常と選択件数・割合不整合。正式元集計待ち'
                r['source_header_ref'] = t['header_issue']['source_ref_by_input'][sid]
            if mid in RATIO_IDS and (sid, mid) in {
                    ('S01', 'III.change.new_application:N371'),
                    ('S02', 'III.change.new_application:N371'),
                    ('S02', 'III.change.renewal:N432')}:
                if r['source_value'] != 0 or r['status'] != 'valid':
                    raise ValueError('C11 zero numerator state differs ' + sid + ' ' + mid)
                r['status'] = 'held'
                r['reason'] = 'C11:ゼロ分子でも正式な対象・除外ケース分母未確定'
                r['hold_override'] = {'issue': 'C11', 'proposal_report_blob_sha':
                                      'd46d6c69f11d0b1457a04e58acc9c2e032ccabe3'}
                c11_count += 1
            if m['table_id'] in focus_by_id or m['table_id'] == 'I.certification.summary':
                r['evidence_sha256'] = metric_evidence(r)
            if r['status'] != 'valid':
                r['comparison_eligible'] = False
            else:
                r['comparison_eligible'] = True
    if (focus_count, cert_count, c10_count, c11_count) != (648, 12, 6, 3):
        raise ValueError('role30 impact counts differ')
    # Every input status is explicit. A missing entry is an error rather than
    # a fallback to the shared inventory status.
    for mid, m in metric_index.items():
        statuses = {}
        for sid in SOURCE_HASHES:
            r = record_index.get((sid, mid))
            if r is None: raise ValueError('missing input record ' + sid + ' ' + mid)
            statuses[sid] = {'status': r['status'], 'reason': r['reason'],
                             'source_ref': r['source_ref'],
                             'input_sha256': r['input_hash']}
        m['extraction_status_by_input'] = statuses
        m['status'] = 'valid' if all(x['status'] == 'valid' for x in statuses.values()) else 'held'
        m['reason'] = None if m['status'] == 'valid' else '入力別状態を参照。共有statusだけでvalid判定しない'
        m['status_resolution'] = 'input_id+id+source_ref+input_sha256。入力別状態必須、issue override優先'
    for c in result['comparisons']:
        city = record_index[('S01', c['city_id'])]
        other = record_index[(c['reference_input'], c['reference_id'])]
        if city['status'] != 'valid' or other['status'] != 'valid':
            c['status'] = 'held'
            c['value'] = None
            c['reason'] = '比較元/先の入力別statusがheld/missing/not_applicable。比較抑止'
            c['dependent_status'] = {city['input_id']: city['status'],
                                     other['input_id']: other['status']}
    numeric_path = args.calculation / 'numeric_checks.json'
    numeric = json.loads(numeric_path.read_text())
    held_keys = {(sid, mid) for (sid, mid), r in record_index.items() if r['status'] != 'valid'}
    numeric['checks'] = [x for x in numeric['checks']
                         if (x['input'], x['id']) not in held_keys or x['check'] == 'provided_transcription_raw_only']
    numeric['counts'] = dict(collections.Counter(x['check'] for x in numeric['checks']))
    result.setdefault('correction_overlays', {})['ROLE30'] = {
        'proposal_report_blob_sha': 'd46d6c69f11d0b1457a04e58acc9c2e032ccabe3',
        'issues': ['E20-01', 'C10', 'C11', 'STATUS-PROPAGATION'],
        'focus_metrics': focus_count, 'certification_metrics': cert_count,
        'C10_uncertain_region_metrics': c10_count, 'C11_new_held_input_records': c11_count,
        'input_status_resolution': 'explicit input map followed by issue override; no top-level valid fallback',
        'C10_header_issue': tmap['II.selection.07.70']['header_issue'],
    }
    write_json(definitions_path, defs)
    write_json(inventory_path, inv)
    write_json(extraction_path, result)
    write_json(numeric_path, numeric)
    check = {
        'status': 'PASS', 'source_sha256': SOURCE_HASHES,
        'proposal_report_blob_sha': 'd46d6c69f11d0b1457a04e58acc9c2e032ccabe3',
        'E20-01': {'focus_tables': 36, 'focus_metrics': 648, 'certification_metrics': 12},
        'C10': {'per_input_numeric_held': 18, 'header_ref': 'P70',
                'header_source_values': {sid: books[sid][c10['sheet']]['P70']['value'] for sid in SOURCE_HASHES}},
        'C11': {'prior_mismatched_held': 27, 'zero_numerator_newly_held': 3,
                'all_30_held': all(record_index[(sid, mid)]['status'] == 'held'
                    for sid, mid in [(r['input_id'], r['id']) for r in result['records']]
                    if r['table_id'].startswith('III.change.') and r['unit'] == '比率'
                    and r['id'] in {x['id'] for x in result['records']
                        if (x['reason'] or '').startswith('C11')})},
        'status_propagation': {'input_records': len(record_index),
            'held_or_missing': sum(r['status'] != 'valid' for r in result['records']),
            'comparisons': len(result['comparisons']),
            'valid_comparisons': sum(c['status'] == 'valid' for c in result['comparisons'])},
    }
    write_json(args.checks, check)
    print(json.dumps(check, ensure_ascii=False))


if __name__ == '__main__':
    main()
