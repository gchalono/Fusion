/** FNXC:OfflineFinal 2026-11-09-05:40:
 * Genuine Fusion shared Pi session, not TaskExecutor/mission/autopilot. Existing
 * merger-purpose policy suppresses host extensions that could open a TaskStore.
 * Builtin file/bash tools only, no MCP, no fallback, in-memory session/fresh HOME.
 * This entry is model-driven but the offline upstream is a labeled test double.
 */
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [runtime,model,objectivePath]=process.argv.slice(2);
const token=fs.readFileSync('/run/local-token','utf8').trim();
const home=process.env.HOME!;
let outputTokens=512;
if(fs.existsSync('/run/offline-profile.json')){const p=JSON.parse(fs.readFileSync('/run/offline-profile.json','utf8'));if(p.offline_output_profile!=='experiment2-offline-test-double-768'||p.experiment_id!=='phase2m-personal-task-manager'||p.offline_only!==true||p.provider_spend_authorized_usd!=='0.00'||p.coding_attempts_per_run!==4)throw Error('invalid_offline_profile');outputTokens=768;}

fs.mkdirSync(path.join(home,'.fusion','agent'),{recursive:true});
fs.writeFileSync(path.join(home,'.fusion','agent','auth.json'),'{}',{flag:'wx',mode:0o600});
fs.writeFileSync(path.join(home,'.fusion','settings.json'),JSON.stringify({mcpServers:{enabled:false,servers:[]},customProviders:[{id:'phase2n-offline',name:'phase2n-offline',apiType:'openai-compatible',baseUrl:'http://127.0.0.1:39777/v1',apiKey:token,models:[{id:model,name:'OFFLINE WIRE TEST DOUBLE',contextWindow:32000,maxTokens:512,...(outputTokens===768?{maxTokens:768}:{})}]}]}),{flag:'wx',mode:0o600});
const {createResolvedAgentSession}=await import(pathToFileURL(runtime+'/packages/engine/src/agents/agent-session-helpers.ts').href);
const events:unknown[]=[];
const created=await createResolvedAgentSession({cwd:'/work',sessionPurpose:'merger',tools:'coding',toolsAllowlist:['read','write','bash'],mcpServers:[],customTools:[],builtinToolsAllowlist:[],defaultProvider:'phase2n-offline',defaultModelId:model,defaultThinkingLevel:'off',systemPrompt:'Complete the supplied coding objective using the provided tools. All execution is inside the evaluation sandbox.',skillSelection:{projectRootDir:'/work',requestedSkillNames:[],sessionPurpose:'merger'}});
if(created.runtimeId!=='pi')throw new Error('unexpected_runtime');
const unsubscribe=created.session.subscribe((event:any)=>{
 if(event.type==='tool_execution_start'||event.type==='tool_execution_end')events.push({type:event.type,tool:event.toolName,args:event.args,isError:event.isError,result:event.result});
 if(event.type==='message_end'&&event.message?.role==='assistant')events.push({type:'model_end',stopReason:event.message.stopReason,errorMessage:event.message.errorMessage});
});
try {
 await created.session.prompt(fs.readFileSync(objectivePath,'utf8'));
 const audit=JSON.stringify({test_double:true,runtime:created.runtimeId,model,events});
 if(audit.includes(token))throw new Error('gateway_token_in_audit');
 console.log('OFFLINE_AUDIT_ONLY '+audit);
} finally {unsubscribe?.();await created.session.dispose?.();}
