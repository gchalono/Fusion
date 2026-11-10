// TEST DOUBLE. Plans bounded native tool replies; no code is mounted into the agent.
import fs from'node:fs';import crypto from'node:crypto';import{fileURLToPath,pathToFileURL}from'node:url';import path from'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));const tokenizer=process.argv[2];if(!tokenizer)throw Error('explicit_tokenizer_required');const {encodingForModel}=await import(pathToFileURL(path.resolve(tokenizer)).href);
const manifest=JSON.parse(fs.readFileSync(path.resolve(path.dirname(tokenizer),'../package.json'),'utf8'));if(manifest.name!=='js-tiktoken'||manifest.version!=='1.0.21')throw Error('unverified_tokenizer');
const e=encodingForModel('gpt-4.1-mini-2025-04-14'),lines=fs.readFileSync(path.join(root,'task_manager_positive_source.py'),'utf8').split('');
function delta(step,part,last=false){const call=(name,args,index)=>({index,id:'TEST_DOUBLE_'+step+'_'+index,type:'function',function:{name,arguments:JSON.stringify(args)}});let calls=[];
if(step==0)calls=[call('read',{path:'/run/objective.txt'},0),call('write',{path:'application.py',content:part},1)];
else {let command="head -c -1 >> application.py <<'TEST_DOUBLE_CODE'\n"+part+"\nTEST_DOUBLE_CODE\n";
if(last)command+="printf 'TEST DOUBLE local task manager; python application.py; python application.py --test\\n' > README.md\nset -e\npython application.py --test\nDATA_DIR=/tmp/positive-smoke PORT=8080 python application.py >/tmp/positive-app.log 2>&1 & p=$!\ntrap 'kill $p; wait $p || true' EXIT\nfor n in 1 2 3 4 5; do curl -fsS -o /tmp/positive-page http://127.0.0.1:8080/ && break; sleep .1; done\ncurl -fsS -o /tmp/positive-tasks http://127.0.0.1:8080/api/tasks\n";
calls=[call('bash',{command},0)];}
return {role:'assistant',tool_calls:calls};}
let chunks=[],offset=0;
for(let step=0;step<3;step++){let part='';for(;offset<lines.length;offset++){const t=part+lines[offset];if(e.encode(JSON.stringify(delta(step,t,step==2))).length+16>512)break;part=t;}chunks.push(delta(step,part,step==2));}
if(offset!==lines.length)throw Error('fixture_exceeds_three_tool_replies');const hash=x=>crypto.createHash('sha256').update(x).digest('hex');console.log(JSON.stringify({classification:'TEST DOUBLE; no treatment effectiveness claim',deltas:chunks,counts:chunks.map(x=>e.encode(JSON.stringify(x)).length),output_ceiling:512,serialization_headroom:16,encoding:'o200k_base',tokenizer_version:manifest.version,source_sha256:hash(fs.readFileSync(path.join(root,'task_manager_positive_source.py'))),rank_sha256:hash(fs.readFileSync(path.resolve(path.dirname(tokenizer),'ranks/o200k_base.js')))}));
