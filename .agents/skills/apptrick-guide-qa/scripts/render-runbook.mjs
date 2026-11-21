#!/usr/bin/env node
import {readFileSync,writeFileSync,existsSync,lstatSync,} from 'node:fs';
import {resolve,parse,join} from 'node:path';
import {createHash} from 'node:crypto';
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const check=(v,message)=>{if(!v)throw new Error(message);};
try{
 const [input,output,...extra]=process.argv.slice(2);check(input&&output&&!extra.length,'Usage: render-runbook.mjs <input.json> <runbook.html>');
 const absolute=resolve(output),parts=absolute.slice(parse(absolute).root.length).split('/');
 let current=parse(absolute).root;
 for(const part of parts){current=join(current,part);try{check(!lstatSync(current).isSymbolicLink(),'Symlink output path refused');}catch(e){if(e.code!=='ENOENT')throw e;}}
 const x=JSON.parse(readFileSync(input,'utf8'));
 check(Object.keys(x).every(k=>['runId','headSha','scenarioId','title','cases'].includes(k)),'Unexpected input field; credentials do not belong in a runbook');
 for(const k of ['runId','headSha','scenarioId','title'])check(typeof x[k]==='string'&&x[k].length>0,`Missing ${k}`);
 check(/^[a-f0-9]{40,64}$/.test(x.headSha),'Full tested SHA required');
 check(Array.isArray(x.cases)&&x.cases.length>0,'Cases required');
 const ids=new Set();
 for(const c of x.cases){
  check(Object.keys(c).every(k=>['id','title','steps','expected','status','observed','evidence'].includes(k)),'Unexpected case field');
  check(typeof c.id==='string'&&/^[A-Za-z0-9_-]+$/.test(c.id)&&!ids.has(c.id),'Unique stable case id required');ids.add(c.id);
  check(typeof c.title==='string'&&typeof c.expected==='string'&&Array.isArray(c.steps)&&c.steps.every(v=>typeof v==='string'),'Invalid case');
  check(['not-run','pass','fail','blocked'].includes(c.status),'Explicit AI status required');
  check(c.observed===undefined||typeof c.observed==='string','Invalid observation');
  check(c.evidence===undefined||Array.isArray(c.evidence)&&c.evidence.every(p=>typeof p==='string'&&/^screenshots\/[A-Za-z0-9_.\/-]+\.(png|jpg|jpeg)$/.test(p)&&!p.split('/').some(s=>s==='..'||s==='.'||s==='')),'Unsafe evidence path');
 }
 const identity=hash([x.runId,x.headSha,x.scenarioId]);
 if(existsSync(output)){
  check(lstatSync(output).isFile()&&lstatSync(output).nlink===1,'Output must be a regular unshared file');
  check(readFileSync(output,'utf8').includes(`<!-- runbook:${identity} -->`),'Different run/revision: use a new output path');
 }
 const records=x.cases.map(c=>({id:c.id,key:hash([identity,c.id,c.title,c.steps,c.expected])}));
 const data=JSON.stringify(records).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');
 const cards=x.cases.map(c=>`<section data-case="${esc(c.id)}"><h2>${esc(c.id)}: ${esc(c.title)}</h2><ol>${c.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol><p><strong>Expected:</strong> ${esc(c.expected)}</p><p>AI: ${esc(c.status)}${c.observed?' - '+esc(c.observed):''}</p>${(c.evidence??[]).map(p=>`<a href="${esc(p)}">${esc(p)}</a>`).join(' ')}<p>Human: <span data-verdict>not checked</span></p><div>${['pass','fail','skip'].map(v=>`<button type="button" data-value="${v}">${v}</button>`).join(' ')}</div></section>`).join('\n');
 writeFileSync(output,`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(x.title)}</title><style>body{font:16px system-ui;max-width:900px;margin:2rem auto;padding:0 1rem;color:#242424}section{border-top:1px solid #aaa;padding:1rem 0}button{padding:.5rem 1rem;margin-right:.5rem}a{display:block}#storage{color:#704400}</style><!-- runbook:${identity} --><h1>${esc(x.title)}</h1><p>Tested revision: ${esc(x.headSha)}. Run: ${esc(x.runId)}.</p><p id="progress" aria-live="polite"></p><p id="storage"></p>${cards}<script type="application/json" id="records">${data}</script><script>
const records=JSON.parse(document.getElementById('records').textContent),memory=new Map();
function load(key){try{return localStorage.getItem(key);}catch{document.getElementById('storage').textContent='Browser storage unavailable; verdicts last only until this page closes.';return memory.get(key);}}
function save(key,value){memory.set(key,value);try{localStorage.setItem(key,value);}catch{document.getElementById('storage').textContent='Browser storage unavailable; verdicts last only until this page closes.';}}
function refresh(){let done=0;for(const r of records){const card=[...document.querySelectorAll('[data-case]')].find(c=>c.dataset.case===r.id);const raw=load(r.key),v=['pass','fail','skip'].includes(raw)?raw:null;card.querySelector('[data-verdict]').textContent=v||'not checked';if(v)done++;}document.getElementById('progress').textContent=done+' / '+records.length+' cases checked by a human';}
for(const card of document.querySelectorAll('[data-case]'))card.addEventListener('click',e=>{if(!e.target.matches('button[data-value]'))return;const r=records.find(r=>r.id===card.dataset.case);save(r.key,e.target.dataset.value);refresh();});refresh();
</script></html>`);
 console.log(JSON.stringify({output,identity,cases:x.cases.length}));
}catch(e){console.error(e.message);process.exitCode=1;}
