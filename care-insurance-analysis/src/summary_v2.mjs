import fs from 'node:fs/promises';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const [input,out]=process.argv.slice(2);const data=JSON.parse(await fs.readFile(input,'utf8'));
await fs.mkdir(out,{recursive:true});const wb=Workbook.create();const sh=wb.worksheets.add('分析要点');sh.showGridLines=false;
for(let i=0;i<data.rows.length;i+=100)sh.getRange(`A${i+1}:N${Math.min(i+100,data.rows.length)}`).values=data.rows.slice(i,i+100);
sh.getRange(`A1:N${data.rows.length}`).format={font:{name:'Yu Gothic',size:10},wrapText:true,rowHeight:90};
const widths=[20,31,22,16,6,10,10,10,10,9,9,10,28,31];
for(let i=0;i<14;i++)sh.getRange(`${String.fromCharCode(65+i)}:${String.fromCharCode(65+i)}`).format.columnWidth=widths[i];
for(let r=1;r<data.header_row;r++){if(data.rows[r-1].filter(v=>v!=='').length===1)sh.getRange(`A${r}:N${r}`).merge();sh.getRange(`A${r}:N${r}`).format.rowHeight=48;}
// S10 compact rows retain separate cells, not a second worksheet.
for(let r=1;r<data.rows.length;r++){
 const f=data.row_formats[r];if(f){if(f.startsWith('headline_')||f.startsWith('supplement_'))sh.getRange(`D${r+1}`).setNumberFormat(f.endsWith('ratio')?'0.0%':f.endsWith('percent')?'0.0"%"':f.endsWith('days')?'0.0':'0');else{sh.getRange(`F${r+1}:I${r+1}`).setNumberFormat(f==='ratio'?'0.0%':f==='days'?'0.0':'0');sh.getRange(`J${r+1}:L${r+1}`).setNumberFormat(f==='ratio'?'0.0" pp"':f==='days'?'0.0':'0');}}
}
for(const r of [1,data.header_row])sh.getRange(`A${r}:N${r}`).format={fill:'#26445C',font:{name:'Yu Gothic',size:r===1?16:10,bold:true,color:'#FFFFFF'},rowHeight:40};
const notes=[
 ['Ⅱ調査項目データ（第５群）','C69:AD69','未検証 C10：P70見出し・H/J/L/N/P/R71:73。下図も比較・結論から除外。'],
 ['Ⅲ審査判定データ（変更率）','D99:AA99','C09：市の軽度変更内訳は分母0のため未算出（0%ではない）。原数式エラーを保持。'],
 ['Ⅲ審査判定データ（変更率）','D367:AA367','C11：市・県・全国の新規変更率6セルは未検証。ゼロ分子も正式分母待ち、比較・結論除外。'],
 ['Ⅲ審査判定データ（変更率）','D428:AA428','C11：県・全国の更新変更率4セルは未検証。市2セルは有効（S02市は保留）、比較は入力別。'],
 ['Ⅲ審査判定データ（変更率）','D489:AA489','C11：県・全国の区分変更率4セルは未検証。市2セルは有効。保留率・依存図は比較・結論除外。'],
 ['Ⅳ事務データ','D205:AA205','C04：市のJ208と下図は未検証・比較/結論対象外。S10 R7年度25.6日は期間の異なる独立参考で、J208の置換や比較には使わない。']
,
 ['Ⅳ事務データ','D203:AC203',"C04 年度参考 | S10 R7 annual city 25.6 days (table62 p53): different period, no comparison."],
 ['Ⅳ事務データ','D209:AC209',"C04 未検証・比較/結論対象外 | J208 city UNVERIFIED: exclude comparison/conclusion."],
 ['Ⅳ事務データ','D221:AC221',"C04 図の市値は比較/結論対象外 | City figure UNVERIFIED; S10 annual reference is separate."],
 ['Ⅱ調査項目データ（第５群）','C74:AD74',"C10 未検証・比較/結論対象外 | Medication labels/counts/rates UNVERIFIED."],
 ['Ⅱ調査項目データ（第５群）','C84:AD84',"C10 chart78 保管表示のみ | Medication chart UNVERIFIED: exclude comparison/conclusion."],
 ['Ⅲ審査判定データ（変更率）','D117:AD119',"C09 N110:N116：市の分母J109=0のため未算出（元数式エラー保持）。\n0%・資料待ちと扱わない。県・全国の率は対象外。分析要点参照。\nNOT COMPUTABLE: denominator=0; not 0%; original errors retained."],
 ['Ⅲ審査判定データ（変更率）','D372:AD372',"C11 正式分母待ち | ONLY N/T/Z370:371 held: denominator unverified; no comparisons."],
 ['Ⅲ審査判定データ（変更率）','D385:AD386',"C11 N370/T370/Z370：正式分母待ち、指定率は比較/結論対象外。分析要点参照。\nONLY N370/T370/Z370 held: denominator unverified; exclude comparison."],
 ['Ⅲ審査判定データ（変更率）','D399:AD400',"C11 N371/T371/Z371：正式分母待ち、指定率は比較/結論対象外。分析要点参照。\nONLY N371/T371/Z371 held: denominator unverified; exclude comparison."],
 ['Ⅲ審査判定データ（変更率）','D433:AD433',"C11 正式分母待ち | ONLY T/Z431:432 held; city N431:N432 NOT held."],
 ['Ⅲ審査判定データ（変更率）','D446:AD447',"C11 T431/Z431：正式分母待ち、指定率は比較/結論対象外。分析要点参照。\nONLY T431/Z431 held: denominator unverified; exclude comparison. City N431 NOT held."],
 ['Ⅲ審査判定データ（変更率）','D460:AD461',"C11 T432/Z432：正式分母待ち、指定率は比較/結論対象外。分析要点参照。\nONLY T432/Z432 held: denominator unverified; exclude comparison. City N432 NOT held."],
 ['Ⅲ審査判定データ（変更率）','D494:AD494',"C11 正式分母待ち | ONLY T/Z492:493 held; city N492:N493 NOT held."],
 ['Ⅲ審査判定データ（変更率）','D507:AD508',"C11 T492/Z492：正式分母待ち、指定率は比較/結論対象外。分析要点参照。\nONLY T492/Z492 held: denominator unverified; exclude comparison. City N492 NOT held."],
 ['Ⅲ審査判定データ（変更率）','D521:AD522',"C11 T493/Z493：正式分母待ち、指定率は比較/結論対象外。分析要点参照。\nONLY T493/Z493 held: denominator unverified; exclude comparison. City N493 NOT held."]
];
const noteSheets=new Map();for(const [name,range,note] of notes){if(!noteSheets.has(name))noteSheets.set(name,wb.worksheets.add(name));let sheet=noteSheets.get(name);sheet.getRange(range).merge();sheet.getRange(range.split(':')[0]).values=[[note]];sheet.getRange(range).format={font:{name:'Yu Gothic',size:9,color:'#9C1B1B'},wrapText:false};}
await fs.writeFile(out+'/local_notes.json',JSON.stringify(notes,null,2));
wb.recalculate();
await(await SpreadsheetFile.exportXlsx(wb)).save(out+'/summary_donor.xlsx');
const png=await wb.render({sheetName:'分析要点',range:'A1:N15',scale:1,format:'png'});await fs.writeFile(out+'/summary_preview.png',new Uint8Array(await png.arrayBuffer()));
console.log(JSON.stringify({status:'authored',sheets:1,rows:data.rows.length,header:data.header_row}));

