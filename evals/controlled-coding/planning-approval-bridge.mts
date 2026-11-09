/** FNXC:OfflineFinal 2026-11-09-05:40:
 * Harness-zone adapter around genuine native APIs. Approval records and channels
 * stay outside the coding view. No interview starts or synthesized approvals.
 * The trusted approval channel verifies all bindings and hashes immediately
 * before this callback; the callback rechecks native question bytes before submit.
 */
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
// FNXC:BlockerResolution 2026-11-09-18:27: Resolve the prepared native runtime
// in the trusted harness, so its actual session store is shared with the caller.
const source=process.env.FUSION_SOURCE_ROOT;
const {getMissionInterviewSession,submitMissionInterviewResponse}=await import(source?pathToFileURL(source+'/packages/dashboard/src/mission-interview.ts').href:'../../packages/dashboard/src/mission-interview.ts');

export async function submitApprovedNativeAnswer(
  context: { sessionId: string; taskId: string; preregistrationHash: string; projectRoot: string; store: unknown },
  approve: (question: string, binding: Record<string,string>, submit: (answer: string) => Promise<void>) => Promise<void>,
) {
  const session = await getMissionInterviewSession(context.sessionId);
  if (!session?.currentQuestion) throw new Error('native_question_missing');
  const question=JSON.stringify(session.currentQuestion);
  const hash=(text: string)=>crypto.createHash('sha256').update(text).digest('hex');
  return approve(question,{session_id:context.sessionId,task_id:context.taskId,preregistration_hash:context.preregistrationHash,question_hash:hash(question)},async answer=>{
    const current=await getMissionInterviewSession(context.sessionId);
    if (!current?.currentQuestion || hash(JSON.stringify(current.currentQuestion))!==hash(question)) throw new Error('native_question_changed');
    const responses=JSON.parse(answer);
    if (!responses || typeof responses!=='object' || Array.isArray(responses)) throw new Error('native_response_map_required');
    await submitMissionInterviewResponse(context.sessionId,responses,context.projectRoot,context.store as never);
  });
}
