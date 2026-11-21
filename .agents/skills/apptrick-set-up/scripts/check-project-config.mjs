#!/usr/bin/env node
// Project-local integrity check. The reviewed manifest is not a trust signature.
import {lstatSync,readFileSync,readdirSync,existsSync,realpathSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const fail=message=>{throw new Error(message);};
try {
 const args=process.argv.slice(2);
 if(args.length!==2||args[0]!=='--project')fail('Usage: check-project-config.mjs --project <target>');
 const root=realpathSync(resolve(args[1]));
 const safe=rel=>{
  if(typeof rel!=='string'||!rel||rel.startsWith('/')||rel.includes('\\')||rel.split('/').some(x=>!x||x==='.'||x==='..'))fail('Unsafe manifest path');
  let p=root;
  for(const part of rel.split('/')){p=join(p,part);try{if(lstatSync(p).isSymbolicLink())fail(`Symlink: ${rel}`);}catch(e){if(e.code!=='ENOENT')throw e;}}
  return p;
 };
 const manifestPath=safe('.ai/client-config.json');
 const manifest=JSON.parse(readFileSync(manifestPath,'utf8'));
 const keys=Object.keys(manifest).sort().join(',');
 if(keys!=='files,packageRoots,personalFiles,roots,version'||manifest.version!==1)fail('Unsupported manifest schema');
 const roots=['.agents','.claude','.codex'];
 if(!Array.isArray(manifest.roots)||[...manifest.roots].sort().join(',')!==roots.join(','))fail('Client roots must include .agents, .claude and .codex');
 const packages=['.agents/skills','.claude/skills'];
 const personal=['.claude/settings.local.json','.codex/config.local.toml'];
 if(!Array.isArray(manifest.packageRoots)||[...manifest.packageRoots].sort().join(',')!==packages.join(','))fail('Only the two package roots may be exempt');
 if(!Array.isArray(manifest.personalFiles)||manifest.personalFiles.some(p=>!['.claude/settings.local.json','.codex/config.local.toml'].includes(p)))fail('Unsupported personal-file exception');
 if(!manifest.files||typeof manifest.files!=='object'||Array.isArray(manifest.files))fail('Invalid files inventory');
 const under=(p,dir)=>p===dir||p.startsWith(dir+'/');
 for(const [rel,digest] of Object.entries(manifest.files)){
  if(packages.some(dir=>under(rel,dir))||personal.includes(rel)||rel==='.ai/client-config.json')fail(`Invalid inventory ownership: ${rel}`);
  const p=safe(rel);
  if(!/^[a-f0-9]{64}$/.test(digest)||!lstatSync(p).isFile())fail(`Invalid file: ${rel}`);
  if(createHash('sha256').update(readFileSync(p)).digest('hex')!==digest)fail(`Changed configuration: ${rel}`);
 }
 const walk=rel=>{
  const p=safe(rel);if(!existsSync(p))return;
  // The package verifier owns descendants, but a root link must never hide them.
  if(packages.includes(rel)){if(!lstatSync(p).isDirectory())fail(`Package root is not a directory: ${rel}`);return;}
  const st=lstatSync(p);
  if(st.isDirectory()){for(const entry of readdirSync(p))walk(rel+'/'+entry);return;}
  if(!st.isFile())fail(`Unsupported filesystem entry: ${rel}`);
  if(!Object.hasOwn(manifest.files,rel)&&!manifest.personalFiles.includes(rel))fail(`Undeclared client file: ${rel}`);
 };
 roots.forEach(walk);
 // Known root-level client declarations must be inventoried too.
 for(const rel of ['.mcp.json','agent-browser.json','AGENTS.md','CLAUDE.md']){
  const p=safe(rel);if(existsSync(p)&&!Object.hasOwn(manifest.files,rel))fail(`Undeclared configuration: ${rel}`);
 }
 const git=args=>spawnSync('git',['-C',root,...args],{encoding:'utf8'});
 if(git(['rev-parse','--is-inside-work-tree']).stdout.trim()!=='true')fail('Git checkout required to verify personal-file tracking');
 for(const rel of personal){
  const tracked=git(['ls-files','--error-unmatch','--',rel]);
  if(tracked.status===0)fail(`Personal settings tracked: ${rel}`);
  if(tracked.status!==1)fail('Unable to read Git index');
  if(!manifest.personalFiles.includes(rel)&&!existsSync(safe(rel)))continue;
  if(!manifest.personalFiles.includes(rel))fail(`Personal settings missing from personal inventory: ${rel}`);
  safe(rel);
  if(git(['check-ignore','-q','--',rel]).status!==0)fail(`Personal settings not ignored: ${rel}`);
 }
 console.log(`CLIENT_CONFIG_OK: ${Object.keys(manifest.files).length} declared files. Package and live capabilities require separate checks.`);
} catch(error){console.error(`CLIENT_CONFIG_FAILED: ${error.message}`);process.exitCode=1;}
