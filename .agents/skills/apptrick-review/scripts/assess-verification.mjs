#!/usr/bin/env node
// Assess normalized observed evidence, never fetch, mutate, or infer missing data.
import {readFileSync} from 'node:fs';
const sha=x=>typeof x==='string'&&/^[a-f0-9]{40,64}$/.test(x);
const result=(status,reason)=>({status,reason});
function assess(x){
 if(!sha(x.head)||x.observedHead!==x.head)return result('unverified','Missing or changed target head');
 if(x.kind==='qa'){
  if(x.ordered!==true||!Array.isArray(x.results))return result('unverified','QA ordering or completeness unknown');
  const q=x.results.filter(r=>r.qualifying===true).at(-1);
  if(!q||!sha(q.head))return result('unverified','No qualifying SHA-bound QA result');
  if(q.head!==x.head)return result('stale','Latest qualifying QA result tested another head');
  if(q.verdict==='fail')return result('fail','Latest current QA result failed');
  if(q.verdict!=='pass')return result('unverified','Latest QA result is incomplete');
  return result('pass',q.scopeReconfirmation===true?'Current scope reconfirmed; not a test rerun':'Current QA evidence');
 }
 if(x.kind!=='ci'||!['pr','branch'].includes(x.mode))return result('unverified','Unknown assessment mode');
 if(x.checksComplete!==true||x.runsComplete!==true||!Array.isArray(x.checks)||!Array.isArray(x.runs))return result('unverified','Incomplete check or run reading');
 if(x.requiredChecks!==null&&!Array.isArray(x.requiredChecks))return result('unverified','Required checks unknown');
 if(x.expectedWorkflows!==null&&!Array.isArray(x.expectedWorkflows))return result('unverified','Expected workflows unknown');
 if(!Array.isArray(x.allowSkipped))return result('unverified','Skip policy unavailable');
 const checks=x.checks.filter(c=>c.headSha===x.head);
 const runs=x.runs.filter(r=>r.headSha===x.head);
 const required=x.requiredChecks??checks.map(c=>c.name);
 const expected=x.expectedWorkflows??[...new Set(runs.map(r=>r.workflow))];
 if(required.length===0&&expected.length===0)return result('unverified','No positive CI evidence');
 const selected=[];
 for(const name of required){
  const found=checks.filter(c=>c.name===name);
  if(found.length!==1)return result('unverified','Missing or ambiguous required check');
  selected.push({...found[0],identity:name});
 }
 for(const name of expected){
  const found=runs.filter(r=>r.workflow===name);
  if(!found.length||found.some(r=>!Number.isInteger(r.attempt)||r.attempt<1))return result('unverified','Missing workflow or attempt identity');
  if(found.some(r=>typeof r.runId!=='string'||!r.runId||!Number.isFinite(Date.parse(r.createdAt))))return result('unverified','Missing run identity or chronology');
  for(const runId of new Set(found.map(r=>r.runId))){
   const attempts=found.filter(r=>r.runId===runId);
   if(new Set(attempts.map(r=>r.createdAt)).size!==1)return result('unverified','Inconsistent run chronology');
   const attempt=Math.max(...attempts.map(r=>r.attempt));
   const newest=attempts.filter(r=>r.attempt===attempt);
   if(newest.length!==1)return result('unverified','Ambiguous workflow attempt');
   selected.push({...newest[0],identity:name});
  }
 }
 // Without an explicit workflow inventory, at least one current run must exist.
 if(x.expectedWorkflows===null&&!runs.length)return result('unverified','Run visibility absent');
 let pending=false,unknown=false;
 for(const item of selected){
  const status=String(item.status??'').toLowerCase(),conclusion=String(item.conclusion??'').toLowerCase();
  if(['queued','in_progress','pending','waiting','requested'].includes(status)){pending=true;continue;}
  if(status!=='completed'){unknown=true;continue;}
  if(['failure','cancelled','canceled','timed_out','action_required','startup_failure','stale'].includes(conclusion))return result('fail','Required CI failed');
  if(conclusion==='success')continue;
  if(conclusion==='skipped'&&x.allowSkipped.includes(item.identity))continue;
  unknown=true;
 }
 return unknown?result('unverified','Unexplained conclusion or skip'):pending?result('pending','Required CI still running'):result('pass','Required checks and runs agree at current head');
}
try{console.log(JSON.stringify(assess(JSON.parse(readFileSync(0,'utf8')))));}
catch{console.error('Invalid evidence JSON');process.exitCode=1;}
