/** Keep the latest assistant outcome; native retries do not make errors permanent. */
export function nextModelError(previous, event, token) {
  if (event.type !== 'message_end' || event.message?.role !== 'assistant') return previous;
  if (event.message.stopReason === 'error' || event.message.stopReason === 'aborted') {
    return String(event.message.errorMessage ?? 'model run failed').replaceAll(token, '[redacted]');
  }
  if (event.message.stopReason === 'stop' || event.message.stopReason === 'toolUse') return undefined;
  return previous;
}
