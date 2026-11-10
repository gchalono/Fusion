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

// FNXC:RealModelReadiness 2026-11-10-04:59: Separate local 4096 rehearsal; no paid entry point.
if(fs.existsSync('/run/readiness-profile.json')){const p=JSON.parse(fs.readFileSync('/run/readiness-profile.json','utf8'));if(fs.existsSync('/run/offline-profile.json')||p.readiness_profile!=='phase3-local-real-shape-4096'||p.offline_only!==true||p.provider_spend_authorized_usd!=='0.00'||p.max_output_tokens!==4096||p.coding_attempts_per_run!==4)throw Error('invalid_readiness_profile');outputTokens=4096;}

// FNXC:LiveCoding 2026-11-10-06:16: Approved gateway profile; legacy defaults stay unchanged.
let supervised=false,synthetic=true;
if(fs.existsSync('/run/supervisor-profile.json')){const p=JSON.parse(fs.readFileSync('/run/supervisor-profile.json','utf8'));if(fs.existsSync('/run/offline-profile.json')||fs.existsSync('/run/readiness-profile.json')||p.profile!=='phase3d-approved-gateway'||p.model!==model||p.arm!=='A'||p.requests!==4||p.output!==4096)throw Error('invalid_supervisor_profile');outputTokens=4096;supervised=true;synthetic=p.synthetic===true;}

fs.mkdirSync(path.join(home,'.fusion','agent'),{recursive:true});
fs.writeFileSync(path.join(home,'.fusion','agent','auth.json'),'{}',{flag:'wx',mode:0o600});
fs.writeFileSync(path.join(home,'.fusion','settings.json'),JSON.stringify({mcpServers:{enabled:false,servers:[]},customProviders:[{id:'phase2n-offline',name:'phase2n-offline',apiType:'openai-compatible',baseUrl:'http://127.0.0.1:39777/v1',apiKey:token,models:[{id:model,name:supervised?'APPROVED BUDGET GATEWAY':'OFFLINE WIRE TEST DOUBLE',contextWindow:32000,maxTokens:512,...(outputTokens!==512?{maxTokens:outputTokens}:{})}]}]}),{flag:'wx',mode:0o600});
const {createResolvedAgentSession}=await import(pathToFileURL(runtime+'/packages/engine/src/agents/agent-session-helpers.ts').href);
const events:unknown[]=[];
const created=await createResolvedAgentSession({cwd:'/work',sessionPurpose:'merger',tools:'coding',toolsAllowlist:['read','write','bash'],mcpServers:[],customTools:[],builtinToolsAllowlist:[],defaultProvider:'phase2n-offline',defaultModelId:model,defaultThinkingLevel:'off',systemPrompt:'Complete the supplied coding objective using the provided tools. All execution is inside the evaluation sandbox.',skillSelection:{projectRootDir:'/work',requestedSkillNames:[],sessionPurpose:'merger'}});
if(created.runtimeId!=='pi')throw new Error('unexpected_runtime');
// FNXC:LiveCoding 2026-11-10-06:54: Fusion's custom-provider registry hardcodes
// 16384 despite settings.maxTokens. Apply the approved 4096 via Pi's PUBLIC API,
// keeping the same snapshot/provider/context and native retry/compaction defaults.
if(supervised){const session:any=created.session;const current=session.model;if(current?.id!==model||current?.provider!=='phase2n-offline')throw Error('unexpected_native_model');await session.setModel({...current,maxTokens:4096});if(session.model.maxTokens!==4096)throw Error('approved_output_limit_not_active');}

const unsubscribe=created.session.subscribe((event:any)=>{
 if(event.type==='tool_execution_start'||event.type==='tool_execution_end')events.push({type:event.type,tool:event.toolName,args:event.args,isError:event.isError,result:event.result});
 if(event.type==='message_end'&&event.message?.role==='assistant')events.push({type:'model_end',stopReason:event.message.stopReason,errorMessage:event.message.errorMessage});
});
try {
 await created.session.prompt(fs.readFileSync(objectivePath,'utf8'));
 // FNXC:RealModelReadiness 2026-11-10-04:59: Synthetic eligibility control only;
 // default compaction is tried first. Override never enters a normal/paid run.
 if(fs.existsSync('/run/local-compaction-control')){
  if(outputTokens!==4096||!fs.existsSync('/run/readiness-profile.json'))throw Error('compaction_control_local_only');
  const session:any=created.session;
  try{await session.compact('LOCAL default compaction eligibility probe');events.push({type:'local_compaction_control',default:'completed'});}
  catch(error){if((error as Error).message!=='Nothing to compact (session too small)')throw error;events.push({type:'local_compaction_control',default:'SESSION_TOO_SMALL'});session.settingsManager.applyOverrides({compaction:{keepRecentTokens:512,reserveTokens:4096}});await session.compact('LOCAL synthetic compaction routing probe; summarize briefly');events.push({type:'local_compaction_control',synthetic:'completed',keepRecentTokens:512});}
 }

 const audit=JSON.stringify({test_double:synthetic,runtime:created.runtimeId,model,events});
 if(audit.includes(token))throw new Error('gateway_token_in_audit');
 console.log((supervised?'SUPERVISED_CODING_AUDIT ':'OFFLINE_AUDIT_ONLY ')+audit);
} finally {unsubscribe?.();await created.session.dispose?.();}
