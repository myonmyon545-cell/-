import fs from 'node:fs/promises';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';

const [tablesPath, outputDir] = process.argv.slice(2);
const data = JSON.parse(await fs.readFile(tablesPath, 'utf8'));
if (data.schema !== 'care_candidate_tables/v1' ||
    data.checks.metrics !== 6316 || data.checks.comparisons !== 1478)
  throw Error('candidate table input coverage differs');
await fs.mkdir(outputDir, {recursive: true});
const wb = Workbook.create();
const specs = [
  ['候補案内', data.guide, 4, [31, 24, 51, 36]],
  ['指標一覧', data.metrics, 15, [9, 39, 28, 40, 29, 25, 21, 19, 12, 18, 18, 12, 52, 56, 38]],
  ['比較一覧', data.comparisons, 11, [48, 41, 41, 12, 14, 12, 18, 12, 40, 20, 53]],
  ['定義・保留', data.definitions, 6, [14, 37, 30, 55, 46, 59]],
];
const colLetter = n => {
  let s = '';
  for (let x=n; x; x=Math.floor((x-1)/26)) s=String.fromCharCode(65+(x-1)%26)+s;
  return s;
};
for(const [name, rows, cols, widths] of specs){
  const sheet = wb.worksheets.add(name);
  sheet.showGridLines = false;
  const endCol = colLetter(cols);
  for(let start=0;start<rows.length;start+=200){
    const block = rows.slice(start,start+200);
    sheet.getRange('A'+(start+1)+':'+endCol+(start+block.length)).values=block;
  }
  for(let i=0;i<cols;i++)
    sheet.getRange(colLetter(i+1)+':'+colLetter(i+1)).format.columnWidth=widths[i];
  const headerRow=name==='候補案内'?2:1;
  sheet.getRange('A'+headerRow+':'+endCol+headerRow).format={
    fill:'#26445C',font:{name:'Yu Gothic',size:11,bold:true,color:'#FFFFFF'}
  };
  if(name==='候補案内'){
    sheet.getRange('A1:D1').merge();
    sheet.getRange('A1').format={
      fill:'#DCE8EF',font:{name:'Yu Gothic',size:17,bold:true,color:'#17324D'}
    };
    sheet.getRange('A1:D14').format.wrapText=true;
    sheet.getRange('A1:D14').format.rowHeight=33;
  }
}
await(await SpreadsheetFile.exportXlsx(wb)).save(outputDir+'/candidate_donor.xlsx');
const guide=wb.worksheets.getItem('候補案内');
const preview=await wb.render({sheetName:'候補案内',range:'A1:D14',scale:1,format:'png'});
await fs.writeFile(outputDir+'/candidate_guide.png',new Uint8Array(await preview.arrayBuffer()));
const inspect=await wb.inspect({kind:'table',range:'候補案内!A1:D14',include:'values',tableMaxRows:14,tableMaxCols:4});
await fs.writeFile(outputDir+'/candidate_guide.inspect.ndjson',inspect.ndjson);
console.log(JSON.stringify({status:'PASS',sheets:specs.map(x=>x[0]),rows:specs.map(x=>x[1].length),
  held_or_missing:data.checks.held_or_missing,valid_comparisons:data.checks.valid_comparisons}));
