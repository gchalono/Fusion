Implement the supplied objective autonomously in the empty Git repository /app.
Use only the supplied treatment material. Do not request human clarification.
Produce working code and real local automated tests; explanations alone are not completion.
Do not modify provided input files, create Fusion missions, use autopilot, push, merge,
deploy, access other implementations, or attempt to discover evaluator files.

All arms use the same offline runtime: Python 3 standard library and Node 24 built-ins
(including node:sqlite), Git, and ordinary local shell/file tools. No package downloads,
external network, real provider credentials, cloud services or paid application services
are available. Choose an implementation within these identical dependencies; no framework
or reference implementation is supplied. Keep generated runtime data outside source.

Public interoperability contract (identical in every condition):
- Provide executable ./run-app and ./run-tests in /app. The final application must already
  be runnable without an install/download step. run-app is a foreground process, listens
  only on 127.0.0.1:$PORT and uses $DATA_DIR/tasks.sqlite3 for SQLite persistence.
  Startup may write only DATA_DIR or /tmp. Root GET / serves the local web interface.
- Anonymous JSON API: GET /api/tasks returns an array; POST /api/tasks accepts title
  (trimmed, nonempty string, <=200 characters) and due_date (null/omitted or real ISO
  YYYY-MM-DD date), returns HTTP 201 and the created task. A task has nonempty string
  id, string title, nullable date due_date and boolean completed (initially false).
- GET /api/tasks/:id returns the task. PATCH /api/tasks/:id accepts title, due_date
  and/or boolean completed, returns the updated task (200). DELETE returns 204.
  Unknown IDs return 404. Invalid JSON/field values return 400 or 422 without losing
  existing data. Titles containing quotes/HTML are data, not executable code.
- Browser test hooks: task-title-input, task-due-input, task-create-button;
  each task-row has data-task-id equal to its API id and contains task-title,
  task-edit-button, task-complete-toggle and task-delete-button. Editing exposes
  task-title-edit, task-due-edit and task-save-button within that row. Toggle supports
  completion and reopening. Dates use HTML date inputs; delete requires no modal.
  Use these data-testid hooks alongside ordinary accessible labels. Hooks specify an
  interface, not a layout or design. Serve all runtime assets locally, without login.
- ./run-tests must run real local Python unittest or Node built-in tests and exit
  nonzero on failure. Preserve their ordinary summary/TAP output with a positive test
  count. Include actual test source files with assertions; do not fabricate test logs.
- Do not include authentication, cloud deployment configuration or paid-service SDKs.
  No hidden evaluator or reference solution will be supplied to you. The same public
  contract and execution/resource limits apply regardless of treatment material.
