/**
 * FNXC:PlanningEvaluation 2026-11-04-10:05:
 * Exercise the real interview module only inside the offline namespace. Neither
 * a dashboard nor an execution engine is constructed. All outputs are test data.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

const run = '/run/fusion-eval';
if (process.env.FUSION_OFFLINE_NAMESPACE !== '1' || !fs.existsSync(`${run}/.offline-test`)) {
  throw new Error('offline_namespace_required');
}
const source = process.env.FUSION_SOURCE_ROOT!;
const endpoint = process.env.FUSION_OFFLINE_GATEWAY!;
if (!endpoint?.startsWith('http://127.0.0.1:')) throw new Error('loopback_gateway_required');
const scenario = process.env.FUSION_OFFLINE_SCENARIO!;
const collector = process.env.FUSION_OFFLINE_COLLECTOR!;
const {submitApprovedNativeAnswer}=await import(pathToFileURL(`${collector}/../controlled-coding/planning-approval-bridge.mts`).href);
const approvalChecks: Record<string,boolean>={};
const approvalRoot=`${run}/results/SYNTHETIC-approvals`;
fs.mkdirSync(approvalRoot);fs.writeFileSync(`${approvalRoot}/.offline-test`,'SYNTHETIC');
const sha = (s: string | Buffer) => crypto.createHash('sha256').update(s).digest('hex');
const write = (name: string, data: unknown) => fs.writeFileSync(`${run}/results/${name}`, JSON.stringify(data, null, 2), { flag: 'wx' });
const protocol = fs.readFileSync(process.env.FUSION_OFFLINE_PROTOCOL!);
const briefsBytes = fs.readFileSync(process.env.FUSION_OFFLINE_BRIEFS!);
const brief = JSON.parse(briefsBytes.toString()).objectives[0];
write('input-provenance.json', { classification: 'SYNTHETIC_OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS',
  protocol_sha256: sha(protocol), briefs_sha256: sha(briefsBytes), brief, rate_limit_identifier: 'fusion-phase2a-pilot' });

// Custom provider settings exist only in a freshly mounted, empty home. The key
// is a public test placeholder, not a loaded credential. No auth files inherited.
fs.mkdirSync('/home/agent/.fusion/agent', { recursive: true });
fs.writeFileSync('/home/agent/.fusion/agent/auth.json', '{}', { flag: 'wx' });
fs.writeFileSync('/home/agent/.fusion/settings.json', JSON.stringify({
  mcpServers: { enabled: false, servers: [] }, customProviders: [{
    id: 'offline-provider', name: 'Offline Evaluation', apiType: 'openai-compatible',
    baseUrl: endpoint + '/v1', apiKey: 'offline-placeholder',
    models: [{ id: 'gpt-4.1-mini-2025-04-14', name: 'SYNTHETIC transport fixture', contextWindow:32000, maxTokens:4096 }],
  }],
}), { flag: 'wx' });

// FNXC:OfflineFinal 2026-11-09-06:35: The wire model ID matches the supplied
// contract; all responses remain scripted test doubles, not model substitution.
// No stubbing of Fusion modules, prompts, parser, retry policy, or provider SDK.
const core = await import(pathToFileURL(`${source}/packages/core/src/index.ts`).href);
const native = await import(pathToFileURL(`${source}/packages/dashboard/src/mission-interview.ts`).href);
const { AiSessionStore } = await import(pathToFileURL(`${source}/packages/dashboard/src/ai-session-store.ts`).href);
const { resolveMcpServersForStore } = await import(pathToFileURL(`${source}/packages/engine/src/mcp/mcp-resolution.ts`).href);
const owner = await core.createTaskStoreForBackend({ rootDir: `${run}/project`,
  globalSettingsDir: '/home/agent/.fusion', embeddedDataDir: `${run}/database` });
const store = owner.taskStore;
const aiStore = new AiSessionStore(owner.asyncLayer);
native.setAiSessionStore(aiStore);
let sessionId: string | undefined;

async function snapshot(name: string) {
  const tables = await owner.asyncLayer.healthDb.execute(core.drizzleSql.raw(
    "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema IN ('project','central','public') AND table_type='BASE TABLE' ORDER BY 1,2"));
  const counts: Record<string, number> = {};
  const rows: Record<string, string> = {};
  for (const t of tables as any[]) {
    const ident = `"${t.table_schema.replaceAll('"', '""')}"."${t.table_name.replaceAll('"', '""')}"`;
    const result = await owner.asyncLayer.healthDb.execute(core.drizzleSql.raw(`SELECT row_to_json(t)::text AS row FROM ${ident} t`));
    counts[`${t.table_schema}.${t.table_name}`] = result.length;
    rows[`${t.table_schema}.${t.table_name}`] = sha(JSON.stringify((result as any[]).map(r => r.row).sort()));
  }
  write(name, { counts, row_hashes: rows });
}

async function settle(id: string) {
  const deadline = Date.now() + 90_000;
  while (Date.now() < deadline) {
    const s = await native.getMissionInterviewSession(id);
    if (s?.error) throw new Error('native_interview_error');
    if (s?.summary || s?.currentQuestion) return s;
    await new Promise(r => setTimeout(r, 25));
  }
  throw new Error('native_interview_timeout');
}

try {
  const mcp = await resolveMcpServersForStore(store);
  if (mcp.servers.length || mcp.errors.length) throw new Error('nonempty_or_invalid_mcp');
  write('mcp.json', { servers: mcp.servers, errors: mcp.errors });
  await snapshot('database-before.json');
  fs.writeFileSync(`${run}/ready`, 'ready', { flag: 'wx' });
  while (!fs.existsSync(`${run}/go`)) await new Promise(r => setTimeout(r, 25));
  sessionId = await native.createMissionInterviewSession('fusion-phase2a-pilot', brief.goal,
    `${run}/project`, store, undefined, 'offline-evaluation',
    scenario === 'model-mismatch' ? 'unauthorized-model' : 'gpt-4.1-mini-2025-04-14', 'off');
  let s = await settle(sessionId);
  const transcript: unknown[] = [];
  let turns = 0;
  while (!s.summary && turns < 3) {
    const q = s.currentQuestion;
    const fact = brief.answers_by_question_id[q.id];
    const value = fact ?? 'No preference; use your judgment.';
    // Native confirm formatting cannot express unknown without inventing a
    // boolean: preserve an incomplete interview rather than fabricate a fact.
    if (q.type === 'confirm' && typeof fact !== 'boolean') break;
    const responses = q.type === 'text' || q.type === 'confirm'
      ? { [q.id]: value } : { _other: value };
    transcript.push({ question: q, response: responses, source: fact === undefined ? 'fixed-unknown' : `brief:${q.id}` });
    // FNXC:BlockerResolution 2026-11-09-18:27: Exercise the real native
    // bridge through the existing SYNTHETIC approver; no TTY/human impersonation.
    const context={sessionId,taskId:'merge-intervals',preregistrationHash:sha(protocol),projectRoot:`${run}/project`,store};
    await submitApprovedNativeAnswer(context,async (question,binding,submit)=>{
      const answer='  '+JSON.stringify(responses)+'\n';
      const input={...binding,question,answer};
      const fixture=(operation:string)=>spawnSync(process.env.FUSION_OFFLINE_PYTHON!,[`${collector}/../controlled-coding/approval_fixture.py`,'--root',approvalRoot,'--operation',operation],{input:JSON.stringify(input),encoding:'utf8',env:{PATH:process.env.PATH!,PYTHONDONTWRITEBYTECODE:'1'}});
      const prepare=()=>{const p=fixture('prepare');if(p.status!==0)throw new Error('SYNTHETIC_approval_prepare_failed');return JSON.parse(p.stdout);};
      let prepared=prepare();Object.assign(approvalChecks,prepared.checks);
      approvalChecks.correct_question_hashing=prepared.question_hash===sha(question)&&binding.question_hash===sha(question);
      if(turns===0){
        if(fixture('crash').status!==23)throw new Error('SYNTHETIC_crash_intent_missing');
        const replay=fixture('replay');if(replay.status!==0||!JSON.parse(replay.stdout).restart_replay_rejected)throw new Error('SYNTHETIC_replay_accepted');
        approvalChecks.crash_restart_behavior=true;
        prepared=prepare(); // Explicit new SYNTHETIC approval after failed intent.
      }
      const consumed=fixture('consume');if(consumed.status!==0)throw new Error('SYNTHETIC_approval_consume_failed');
      const checked=JSON.parse(consumed.stdout);
      if(checked.answer!==answer||checked.answer_hash!==sha(answer))throw new Error('SYNTHETIC_answer_changed');
      approvalChecks.verbatim_answer_preservation=true;
      await submit(checked.answer);
    });
    s = await settle(sessionId);
    turns++;
  }
  write('approval-integration.json',{classification:'SYNTHETIC',checks:approvalChecks,native_response_turns:turns});
  const actual = s.agent?.session?.model;
  if (actual?.provider !== 'offline-evaluation' || actual?.id !== 'gpt-4.1-mini-2025-04-14') throw new Error('resolved_model_mismatch');
  // Raw assistant text remains native, unedited and explicitly non-genuine.
  write('native-test-double.json', { classification: 'SYNTHETIC_OFFLINE_MOCK_NOT_GENUINE_NOT_CORPUS',
    transcript, summary: await native.getMissionInterviewSummary(sessionId),
    actual_model: { provider: actual.provider, id: actual.id },
    raw_assistant: s.agent.session.state.messages.filter((m: any) => m.role === 'assistant')
      .map((m: any) => ({ content: m.content, model: m.model, usage: m.usage })),
    statistics: s.agent.session.getSessionStats?.(),
    usage_accounting: 'provider_reported_unverified',
    cost_accounting: 'native_catalog_cost_not_billable', turns, incomplete: !s.summary });
  if (scenario === 'comprehensive') {
    const session=s.agent.session;
    const settings=session.settingsManager.getCompactionSettings(session.model);
    const entries=session.sessionManager.getBranch();
    let attempted=false;
    try {
      attempted=true;
      await session.compact('SYNTHETIC compaction routing check; return a short factual summary.');
      write('compaction.json', { classification:'SYNTHETIC',status:'completed',attempted,settings,branch_entries:entries.length,statistics:session.getSessionStats?.() });
    } catch (error) {
      const text=(error as Error).message;
      const reason=text==='Nothing to compact (session too small)'?'SESSION_TOO_SMALL':text==='Already compacted'?'ALREADY_COMPACTED':'OTHER_ERROR';
      write('compaction.json', { classification:'SYNTHETIC',status:'not_completed',attempted,reason,error_sha256:sha(text),settings,branch_entries:entries.length,statistics:session.getSessionStats?.() });
      if(reason!=='SESSION_TOO_SMALL')throw error;
      // FNXC:BlockerResolution 2026-11-09-18:27: Separate SYNTHETIC trigger
      // control: retain a smaller tail in this disposable session only. This
      // does not change input/output/request/time/spend limits or frozen tasks.
      session.settingsManager.applyOverrides({compaction:{keepRecentTokens:512,reserveTokens:4096}});
      const triggerSettings=session.settingsManager.getCompactionSettings(session.model);
      await session.compact('SYNTHETIC compaction trigger control; return a short factual summary.');
      write('SYNTHETIC-triggered-compaction.json',{classification:'SYNTHETIC',status:'completed',settings:triggerSettings,statistics:session.getSessionStats?.()});
    }
  }
} catch (e) {
  write('native-failure.json', { classification: 'SYNTHETIC_OFFLINE_TEST_FAILURE', code: (e as Error).message });
} finally {
  // Await persistence without fabricating a completed row; take evidence before
  // cleanup so the native session record is visible in the after snapshot.
  for (let i = 0; sessionId && i < 80; i++) {
    if (await aiStore.get(sessionId)) break;
    await new Promise(r => setTimeout(r, 25));
  }
  await snapshot('database-after.json');
  if (sessionId) {
    const s = await native.getMissionInterviewSession(sessionId);
    await s?.agent?.session?.dispose?.();
  }
  fs.writeFileSync(`${run}/settled`, 'settled', { flag: 'wx' });
  while (!fs.existsSync(`${run}/shutdown`)) await new Promise(r => setTimeout(r, 25));
  await owner.shutdown();
}
