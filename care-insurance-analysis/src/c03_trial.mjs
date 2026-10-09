import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';

const [input, out] = process.argv.slice(2);
await fs.mkdir(out, {recursive:true});
const started=Date.now();
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(input));
const basic=wb.worksheets.getItem('Ⅰ基礎情報');
const decision=wb.worksheets.getItem('Ⅲ審査判定データ（一次・二次判定）');
const office=wb.worksheets.getItem('Ⅳ事務データ');
const old=basic.getRange('G513:G521').values.map(x=>x[0]);
const proposed=[66,255,198,432,259,190,230,157,1787];
const iii=decision.getRange('G128:G136').values.map(x=>x[0]);
const labelsI=basic.getRange('C513:C521').values.map(x=>x[0]);
const labelsIII=decision.getRange('C128:C136').values.map(x=>x[0]);
const ratioColumns=['K','N','Q','U','Y'];
const ratios=ratioColumns.map(col=>basic.getRange(col+'513:'+col+'520').values.map(x=>x[0]));
const decisionRatios=ratioColumns.map(col=>decision.getRange(col+'128:'+col+'135').values.map(x=>x[0]));
const iv={J189:office.getRange('J189').values[0][0],J207:office.getRange('J207').values[0][0],J225:office.getRange('J225').values[0][0]};
const independentCommit='b5b14b75d8329850b441640ff5b92408a9ccca81';
if(JSON.stringify(labelsI)!==JSON.stringify(labelsIII))throw Error('C03 labels do not match');
if(JSON.stringify(iii)!==JSON.stringify(proposed))throw Error('C03 proposed values differ from III');
if(iii.slice(0,8).reduce((a,b)=>a+b,0)!==iii[8]||iv.J189!==iii[8]||iv.J207!==iii[8]||iv.J225!==iii[8])throw Error('C03 total cross-check failed');
if(ratios.some((series,j)=>series.some((x,i)=>Math.abs(x-decisionRatios[j][i])>1e-10)))throw Error('C03 ratio-column cross-check failed');

// This is the authorized repair: only I!G513:G521 in this in-memory work copy.
basic.getRange('G513:G521').values=proposed.map(x=>[x]);
const wbSummary=wb.worksheets.add('分析要点');
wbSummary.showGridLines=false;
wbSummary.getRange('A2:D2').merge();
wbSummary.getRange('A2').values=[['介護保険データ解析 — 作業コピーの保持試験']];
wbSummary.getRange('A4:D14').values=[
 ['確認項目','値','根拠・分母','状態'],
 ['総人口',104961,'2025年1月基準','原表値'],
 ['65歳以上人口',32297,'2025年1月基準','原表値'],
 ['75歳以上人口',18791,'2025年1月基準','原表値'],
 ['85歳以上人口',5782,'2025年1月基準','原表値'],
 ['第1号被保険者認定率',null,'Ⅰ!F261 / Ⅰ!F260 = 5,125 / 32,297','計算式を再確認'],
 ['一次判定件数合計（C03）',null,'修正後のⅠ!G513:G520','Ⅲ!G136・Ⅳ3件数と一致'],
 ['軽度変更構成比（C09）','未算出（分母0）','Ⅲ!J109=0','保留'],
 ['調査依頼から実施まで（C04）','保留','正式元集計または対象日付が必要','保留'],
 ['薬の内服（C10）','保留','件数・割合・見出しに不整合','保留'],
 ['申請区分別変更率（C11）','保留','正式分母・対象定義が未確認','保留']
];
wbSummary.getRange('B9').formulas=[["='Ⅰ基礎情報'!F261/'Ⅰ基礎情報'!F260"]];
wbSummary.getRange('B10').formulas=[["=SUM('Ⅰ基礎情報'!G513:G520)"]];
wbSummary.getRange('A17:D17').merge();
wbSummary.getRange('A17').values=[['C03修正履歴 — このS01作業コピーだけに適用']];
wbSummary.getRange('A18:D27').values=[
 ['Ⅰのセル','修正前','修正後','根拠（同じ見出しのⅢ件数）'],
 ...old.map((value,i)=>['G'+(513+i),value,proposed[i],'Ⅲ!G'+(128+i)+' = '+proposed[i]])
];
wbSummary.getRange('A29:D31').values=[
 ['独立確認','ROLE=20 C03 PASS','Ⅲ内訳・割合','Ⅳ件数を照合'],
 ['S01原本SHA256（先頭16桁）','5721ee2b38cb8f55','原本不変更','作業コピーに適用'],
 ['判定','構造保持試験用','最終候補ではない','表示検査中']
];
wbSummary.getRange('A2:D31').format.font={name:'Yu Gothic',size:11};
wbSummary.getRange('A2').format.font={name:'Yu Gothic',size:16,bold:true};
wbSummary.getRange('A4:D4').format={fill:'#26445C',font:{name:'Yu Gothic',size:11,bold:true,color:'#FFFFFF'}};
wbSummary.getRange('A18:D18').format={fill:'#345B74',font:{name:'Yu Gothic',size:10,bold:true,color:'#FFFFFF'}};
wbSummary.getRange('A17:D17').format={fill:'#DCE8EF',font:{name:'Yu Gothic',size:12,bold:true,color:'#17324D'}};
wbSummary.getRange('A29:D29').format={fill:'#E2F0D9',font:{name:'Yu Gothic',size:10,bold:true}};
wbSummary.getRange('A:A').format.columnWidth=25;
wbSummary.getRange('B:B').format.columnWidth=16;
wbSummary.getRange('C:C').format.columnWidth=28;
wbSummary.getRange('D:D').format.columnWidth=24;
wbSummary.getRange('A2:D31').format.wrapText=true;
wbSummary.getRange('A2:D31').format.verticalAlignment='center';
wbSummary.getRange('A4:D31').format.rowHeight=30;
wbSummary.getRange('A2:D2').format.rowHeight=36;
wbSummary.getRange('B9').setNumberFormat('0.0%');
const cert=wbSummary.getRange('B9').values[0][0];
const total=wbSummary.getRange('B10').values[0][0];
if(Math.abs(cert-5125/32297)>1e-10||total!==1787)throw Error('Summary recalculation failed');

// Change a C03 input temporarily, prove the summary responds, then restore.
basic.getRange('G513').values=[[67]];
const changedTotal=wbSummary.getRange('B10').values[0][0];
if(changedTotal!==1788)throw Error('C03 dependency did not recalculate');
basic.getRange('G513').values=[[66]];
wb.recalculate();
if(wbSummary.getRange('B10').values[0][0]!==1787)throw Error('C03 restoration failed');

const preview=await wb.render({sheetName:'分析要点',range:'A1:D31',scale:1,format:'png'});
await fs.writeFile(out+'/summary.png',new Uint8Array(await preview.arrayBuffer()));
const details=await wb.inspect({kind:'table',range:'分析要点!A4:D14',include:'values,formulas',tableMaxRows:11,tableMaxCols:4});
await fs.writeFile(out+'/artifact_values.ndjson',details.ndjson);
await(await SpreadsheetFile.exportXlsx(wb)).save(out+'/donor.xlsx');
const evidence={sourceBefore:old,sourceAfter:basic.getRange('G513:G521').values.map(x=>x[0]),independent_commit:independentCommit,
 labels_match:true,iii_counts:iii,iii_parts_sum:iii.slice(0,8).reduce((a,b)=>a+b,0),ratio_columns:ratioColumns,ratios_match:true,iv_counts:iv,
 summary:{certification_rate:cert,total_formula:total,changed_input_total:changedTotal,restored_total:wbSummary.getRange('B10').values[0][0]},
 change_scope:['Ⅰ基礎情報!G513:G521'],elapsed_seconds:(Date.now()-started)/1000};
await fs.writeFile(out+'/artifact_evidence.json',JSON.stringify(evidence,null,2)+'\n');
console.log(JSON.stringify(evidence));
