const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('/workspace/sites/care-analysis-atlas/dist/index.html','utf8');
const calls=[];
const ctx=new Proxy({measureText:t=>({width:t.length*7})},{get:(o,k)=>k in o?o[k]:(...x)=>calls.push([k,...x])});
class E{constructor(tag){this.tag=tag;this.children=[];this.style={setProperty(){}};this.value='';this.dataset={};this.classList={toggle(){return true},contains(){return false}};}append(...x){this.children.push(...x)}prepend(x){this.children.unshift(x)}insertBefore(x){this.children.push(x)}replaceChildren(){this.children=[]}setAttribute(k,v){this[k]=v}scrollIntoView(){}getContext(){return ctx}getBoundingClientRect(){return {width:820,height:640,left:0,top:0}}setPointerCapture(){}addEventListener(k,f){this[k]=f}}
const ids={};for(const m of html.matchAll(/id="([^"]+)"/g))ids[m[1]]=new E('div');
ids.data.textContent=html.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const tabs=['history','process','files','updates'].map(x=>Object.assign(new E('button'),{dataset:{tab:x},click(){this.onclick()}}));
const stage=new E('div');let animation;
const c={document:{hidden:false,getElementById:x=>ids[x],createElement:x=>new E(x),querySelectorAll:()=>tabs,querySelector:x=>x==='.stage'?stage:tabs[2]},Option:function(t,v){this.text=t;this.value=v},matchMedia:()=>({matches:false}),ResizeObserver:class{observe(){}},devicePixelRatio:2,requestAnimationFrame:f=>(animation=f,1),location:{hash:'#files'},window:{},console};vm.createContext(c);
for(const script of html.matchAll(/<script>([\s\S]*?)<\/script>/g))vm.runInContext(script[1],c);
assert.equal(ids.files.hidden,false);
const g=c.window.careGraph3D;assert(g.nodeCount>100);assert.equal(g.edgeCount,g.nodeCount-1);
for(const p of g.positions.values())assert(['x','y','z'].every(k=>Number.isFinite(p[k])));
animation(50);assert(calls.some(x=>x[0]==='fillText'));
const f=[...g.positions.keys()].find(p=>p.endsWith('PLAN.md'));g.select(f);animation(100);assert(ids.details.children.length>0);
const canvas=ids.space.children[0];canvas.onpointerdown({pointerId:1,clientX:0,clientY:0});canvas.onpointermove({pointerId:1,clientX:80,clientY:30});canvas.onpointerup({pointerId:1,clientX:80,clientY:30});
canvas.onpointerdown({pointerId:1,clientX:20,clientY:20});canvas.onpointerdown({pointerId:2,clientX:80,clientY:20});canvas.onpointermove({pointerId:2,clientX:120,clientY:20});canvas.onpointercancel({pointerId:1});canvas.onpointercancel({pointerId:2});animation(150);
console.log(JSON.stringify({nodes:g.nodeCount,edges:g.edgeCount,render:'PASS',selection:'PASS',orbit:'PASS',pinch:'PASS',scope:'Node canvas/DOM fixture, not real browser/iPad visual QA'}));
