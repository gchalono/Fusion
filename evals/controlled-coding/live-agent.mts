/** Dedicated live adapter; same Pi tools and isolation contract as the offline adapter. */
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [runtime,model,objectivePath]=process.argv.slice(2);
const token=fs.readFileSync('/run/local-token','utf8').trim();
const home=process.env.HOME!;
fs.mkdirSync(path.join(home,'.fusion','agent'),{recursive:true});
fs.writeFileSync(path.join(home,'.fusion','agent','auth.json'),'{}',{flag:'wx',mode:0o600});
fs.writeFileSync(path.join(home,'.fusion','settings.json'),JSON.stringify({mcpServers:{enabled:false,servers:[]},customProviders:[{id:'controlled-live',name:'controlled-live',apiType:'openai-compatible',baseUrl:'http://127.0.0.1:39777/v1',apiKey:token,models:[{id:model,name:'Operator-authorized live model',contextWindow:32000,maxTokens:512}]}]}),{flag:'wx',mode:0o600});
const {createResolvedAgentSession}=await import(pathToFileURL(runtime+'/packages/engine/src/agents/agent-session-helpers.ts').href);
const events:unknown[]=[];
let modelError:string|undefined;
const created=await createResolvedAgentSession({cwd:'/work',sessionPurpose:'merger',tools:'coding',toolsAllowlist:['read','write','bash'],mcpServers:[],customTools:[],builtinToolsAllowlist:[],defaultProvider:'controlled-live',defaultModelId:model,defaultThinkingLevel:'off',systemPrompt:'Complete the supplied coding objective using the provided tools. All execution is inside the evaluation sandbox.',skillSelection:{projectRootDir:'/work',requestedSkillNames:[],sessionPurpose:'merger'}});
if(created.runtimeId!=='pi')throw new Error('unexpected_runtime');
const unsubscribe=created.session.subscribe((event:any)=>{
 if(event.type==='message_end'&&event.message?.role==='assistant'&&event.message?.stopReason==='error')modelError=String(event.message.errorMessage??'model error').replaceAll(token,'[redacted]');
 if(event.type==='tool_execution_start'||event.type==='tool_execution_end')events.push({type:event.type,tool:event.toolName,isError:event.isError,result:event.result});
});
try {
 await created.session.prompt(fs.readFileSync(objectivePath,'utf8'));
 if(modelError)throw new Error(modelError);
 const audit=JSON.stringify({test_double:false,runtime:created.runtimeId,model,events});
 if(audit.includes(token))throw new Error('gateway_token_in_audit');
 console.log('LIVE_AGENT_AUDIT '+audit);
} finally {unsubscribe?.();await created.session.dispose?.();}
