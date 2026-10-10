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
 ['Ⅳ事務データ','D205:AA205','C04：市の表示はS10 R7年度市独自集計25.6日へ置換。S01第2回の復元ではなく比較対象外。下図はS01原値を含む旧図で結論に使わない。']
];
const noteSheets=new Map();for(const [name,range,note] of notes){if(!noteSheets.has(name))noteSheets.set(name,wb.worksheets.add(name));let sheet=noteSheets.get(name);sheet.getRange(range).merge();sheet.getRange(range.split(':')[0]).values=[[note]];sheet.getRange(range).format={font:{name:'Yu Gothic',size:9,color:'#9C1B1B'},wrapText:false};}
await fs.writeFile(out+'/local_notes.json',JSON.stringify(notes,null,2));
wb.recalculate();
await(await SpreadsheetFile.exportXlsx(wb)).save(out+'/summary_donor.xlsx');
const png=await wb.render({sheetName:'分析要点',range:'A1:N15',scale:1,format:'png'});await fs.writeFile(out+'/summary_preview.png',new Uint8Array(await png.arrayBuffer()));
console.log(JSON.stringify({status:'authored',sheets:1,rows:data.rows.length,header:data.header_row}));
