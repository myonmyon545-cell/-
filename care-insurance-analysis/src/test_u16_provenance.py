"""Synthetic, bounded fixtures for U16 provenance and numeric dataflow."""
import json
import tempfile
import unittest
from pathlib import Path

from replay_pipeline import (OUTPUTS, STAGE_ID, _copy_available,
                            compare_id_sets, reserve_run_directory,
                            verify_extraction_manifest, persist_run_evidence,
                            sha, write_json)
from summary_v2 import comparison_trace, input_provenance, build_summary


def extraction(n=9):
    records=[]; comparisons=[]
    for i in range(n):
        city=f'c{i}'; ref=f'r{i}'; label=f'provided_period_{i}'
        records.extend([
            {'input_id':'S01','id':city,'source_ref':{'input':'S01','sheet':'Ⅱ調査項目','cell':f'G{513+i}'},
             'region':'市','requirements':[],'adjustment':'通常','row_label':f'行{i}','table_id':'fixture',
             'population':'母集団','kind':'率','unit':'比率','value':0.1,'status':'valid','reason':None,
             'period':'fixture-period','item_name':'合議体別の比較試験'},
            {'input_id':'S02','id':ref,'source_ref':{'input':'S02','sheet':'Ⅱ調査項目','cell':f'G{513+i}'},
             'region':'市','requirements':[],'adjustment':'通常','row_label':f'行{i}','table_id':'fixture',
             'population':'母集団','kind':'率','unit':'比率','value':0.2,'status':'valid','reason':None,
             'period':'fixture-period','item_name':'合議体別の比較試験'}])
        comparisons.append({'id':f'I.first_decision_duplicate:{city}:{label}',
            'city_id':city,'label':label,'reference_input':'S02','reference_id':ref,
            'value':i+0.25,'status':'valid','reason':None,'dependent_status':{'S01':'valid','S02':'valid'}})
    return {'records':records,'comparisons':comparisons}


class U16ProvenanceTests(unittest.TestCase):
    def make_run(self, root, run_id='fixture-run-0001', data=None, complete=True):
        run_dir=Path(root)/run_id/STAGE_ID
        run_dir.mkdir(parents=True)
        out=Path(root)/'transient'; sources={}
        for name,(source_rel,dest_name) in OUTPUTS.items():
            if name=='definitions': rel='contract/'+dest_name
            elif name in ('inventory','summary'): rel='final_checks/'+dest_name
            elif name in ('extracted','numeric'): rel='calculation/'+dest_name
            else: rel=dest_name
            path=out/rel;path.parent.mkdir(parents=True,exist_ok=True)
            payload=(data if name=='extracted' and data is not None else
                {'records':[],'comparisons':[]} if name=='extracted' else {'fixture':name})
            path.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
            sources[name]=path
        artifacts=_copy_available(sources,run_dir)
        ext=next(x for x in artifacts if x['name']=='extracted')
        counts={'record_count':ext['record_count'],'comparison_count':ext['comparison_count']}
        ids=[x['id'] for x in (data or {'comparisons':[]}).get('comparisons',[])]
        manifest={'schema':'care_numeric_run_manifest/v1','run_id':run_id,'stage_id':STAGE_ID,
            'complete':complete,'comparison_set':{'complete':True,'actual_count':len(ids),'required_count':9},
            'record_set':{'complete':True,'actual_count':counts['record_count']},
            'counts':counts,'contract_counts':{'record_count':18,'comparison_count':9},'artifacts':artifacts,
            'code_identity':{'commit':'fixture-code','files':{'replay_pipeline.py':'fixture-sha'}},
            'input_identity':{'S01':{'library_file_id':'fixture-S01','sha256':'fixture-input-sha'}}}
        path=run_dir/'run_manifest.json';write_json(path,manifest)
        import shutil;shutil.rmtree(out)
        return run_dir,path,run_dir/'outputs/calculation/extracted_values.json',manifest

    def test_u16_t1_retained_bytes_and_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);run_dir,manifest,extraction_path,m=self.make_run(root,data=extraction())
            expected=sha(extraction_path.read_bytes())
            # Removing the producer's transient workspace does not affect retained run bytes.
            transient=root/'transient';transient.mkdir();(transient/'discard').write_text('temporary')
            import shutil;shutil.rmtree(transient)
            self.assertEqual(sha(extraction_path.read_bytes()),expected)
            self.assertEqual(len(m['artifacts']),6)
            self.assertEqual(m['counts'],{'record_count':18,'comparison_count':9})
            for item in m['artifacts']:
                saved=run_dir/item['relative_path'];raw=saved.read_bytes()
                self.assertEqual(sha(raw),item['sha256'])
                self.assertEqual(len(raw),item['size_bytes'])
                self.assertEqual(item['processing_stage'],STAGE_ID)
                self.assertEqual(item['record_count'],18)
                self.assertEqual(item['comparison_count'],9)
            with self.assertRaises(FileExistsError):
                reserve_run_directory(root,'fixture-run-0001')
            commands={'commands':[{'command':['python','synthetic.py'],'exit_code':0,'stdout':'ok','stderr':''}]}
            persist_run_evidence(run_dir,m,commands)
            reread=json.loads((run_dir/'subprocess_log.json').read_text())
            self.assertEqual(reread['commands'][0]['stdout'],'ok')
            self.assertEqual(reread['commands'][0]['exit_code'],0)

    def test_u16_t2_nine_c03_comparisons_flow_to_trace(self):
        actual=extraction(9); baseline=extraction(9)
        self.assertTrue(compare_id_sets(actual,baseline,9)['complete'])
        trace=comparison_trace(actual)
        self.assertEqual(len(trace),9)
        self.assertEqual(trace[0]['value'],0.25)
        self.assertEqual(trace[0]['status'],'valid')
        self.assertEqual(trace[0]['reference_source_ref']['input'],'S02')

    def test_u16_t3_invalid_provenance_and_incomplete_set_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir,manifest,extraction_path,m=self.make_run(td,data=extraction())
            self.assertTrue(verify_extraction_manifest(extraction_path,manifest,'fixture-run-0001')['counts']['comparison_count']==9)
            with self.assertRaisesRegex(ValueError,'run_id'):
                verify_extraction_manifest(extraction_path,manifest,'another-run-0001')
            wrong=json.loads(manifest.read_text());wrong['stage_id']='pre_C03';write_json(manifest,wrong)
            with self.assertRaisesRegex(ValueError,'stage'):
                verify_extraction_manifest(extraction_path,manifest,'fixture-run-0001')
            wrong['stage_id']=STAGE_ID;wrong['comparison_set']['complete']=False;write_json(manifest,wrong)
            with self.assertRaisesRegex(ValueError,'incomplete'):
                verify_extraction_manifest(extraction_path,manifest,'fixture-run-0001')
            wrong['comparison_set']['complete']=True;write_json(manifest,wrong)
            wrong['record_set']['complete']=False;write_json(manifest,wrong)
            with self.assertRaisesRegex(ValueError,'record set is incomplete'):
                verify_extraction_manifest(extraction_path,manifest,'fixture-run-0001')
            wrong['record_set']['complete']=True;write_json(manifest,wrong)
            saved=json.loads(manifest.read_text());saved['artifacts']=[x for x in saved['artifacts'] if x['name']!='extracted'];write_json(manifest,saved)
            with self.assertRaisesRegex(ValueError,'lacks final extraction'):
                verify_extraction_manifest(extraction_path,manifest,'fixture-run-0001')
            write_json(manifest,wrong)
            extraction_path.unlink()
            with self.assertRaisesRegex(ValueError,'missing'):
                verify_extraction_manifest(extraction_path,manifest,'fixture-run-0001')
            # Restore a valid byte sequence, then prove the manifest catches mutation.
            _,_,other_path,_=self.make_run(Path(td)/'second',data=extraction())
            extraction_path.parent.mkdir(parents=True,exist_ok=True)
            extraction_path.write_bytes(other_path.read_bytes())
            extraction_path.write_text('{"records":[],"comparisons":[]}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'bytes differ'):
                verify_extraction_manifest(extraction_path,manifest,'fixture-run-0001')
            with self.assertRaisesRegex(ValueError,'baseline'):
                verify_extraction_manifest(td+'/baseline/extracted_values.json',manifest,'fixture-run-0001')
            self.assertFalse(compare_id_sets(extraction(0),extraction(9),9)['complete'])

    def test_u16_t4_manifest_binds_summary_input_identity(self):
        with tempfile.TemporaryDirectory() as td:
            _,manifest,extraction_path,m=self.make_run(td,data=extraction())
            checked=verify_extraction_manifest(extraction_path,manifest,'fixture-run-0001')
            result=build_summary(checked['extraction'],{'blocks':[],'supplemental_metrics':[]},checked,m['run_id'],m['stage_id'])
            provenance=result['input_provenance']
            self.assertEqual(len(result['comparison_trace']),9)
            self.assertEqual(provenance['extraction_sha256'],m['artifacts'][2]['sha256'])
            self.assertEqual(provenance['stage_id'],STAGE_ID)
            self.assertEqual(checked['counts']['comparison_count'],9)


if __name__=='__main__':
    unittest.main()
