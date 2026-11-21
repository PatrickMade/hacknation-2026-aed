#!/usr/bin/env node
// Read-only source-qualified identity check; tracker search remains the caller's job.
import {readFileSync,realpathSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
export function resolveIdentity(x){
 const blocked=reason=>({status:'blocked',reason});
 if(!x||x.complete!==true||typeof x.target!=='string'||!x.target||typeof x.source!=='string'||!x.source||x.source.startsWith('/')||x.source.includes('\\')||x.source.split('/').some(p=>!p||p==='.'||p==='..')||typeof x.id!=='string'||!x.id||!Array.isArray(x.issues))return blocked('Incomplete search or invalid identity');
 const exact=[];
 for(const issue of x.issues){
  if(issue.target!==x.target||typeof issue.reference!=='string'||!issue.reference||typeof issue.body!=='string'||typeof issue.url!=='string'||!issue.url.startsWith('https://'))return blocked('Unbound tracker result');
  const comments=issue.adoptionComments??[];
  if(!Array.isArray(comments)||comments.some(c=>!c||typeof c.body!=='string')||(comments.length&&issue.commentsComplete!==true))return blocked('Incomplete adoption read-back');
  const pairs=[];
  for(const body of [issue.body,...comments.map(c=>c.body)]){
   const sources=[...body.matchAll(/^Backlog source: (.+)\r?$/gm)].map(m=>m[1].trim());
   const ids=[...body.matchAll(/^Backlog id: (.+)\r?$/gm)].map(m=>m[1].trim());
   if(!sources.length&&!ids.length)continue;
   if(sources.length!==1||ids.length!==1)return blocked('Ambiguous identity markers');
   pairs.push(JSON.stringify([sources[0],ids[0]]));
  }
  if(!pairs.length||new Set(pairs).size!==1)return blocked('Candidate needs explicit adoption or conflicting marker resolution');
  if(pairs[0]===JSON.stringify([x.source,x.id]))exact.push(issue);
 }
 if(exact.length>1)return blocked('Duplicate source/id mappings');
 return exact.length?{status:'reuse',reference:exact[0].reference,url:exact[0].url}:{status:'new',reason:'No exact mapping; intake semantic dedupe still required'};
}
if(process.argv[1]&&realpathSync(fileURLToPath(import.meta.url))===realpathSync(process.argv[1])){
 try{console.log(JSON.stringify(resolveIdentity(JSON.parse(readFileSync(0,'utf8')))));}catch{console.error('Invalid identity JSON');process.exitCode=1;}
}
