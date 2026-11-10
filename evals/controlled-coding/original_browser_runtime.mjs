// Trusted launch adapter only. Original assertion bytes arrive over stdin, never
// as a file mounted for the browser or as source code in process arguments.
import fs from 'node:fs';import crypto from 'node:crypto';
const source=fs.readFileSync(0);fs.closeSync(0);fs.openSync('/dev/null','r');
if(crypto.createHash('sha256').update(source).digest('hex')!=='708c0230d42fb518a5f3442992241bdd9e5023b1c7f41505d4f0a5795a44d88a')throw Error('original_browser_assertions_changed');
if(fs.existsSync('/checks')||fs.existsSync('/workspace')||['OPENAI_API_KEY','ANTHROPIC_API_KEY','GH_TOKEN','GITHUB_TOKEN'].some(k=>k in process.env))throw Error('browser_namespace_visibility');
const {chromium}=await import('/opt/playwright/index.mjs');const launch=chromium.launch.bind(chromium);
chromium.launch=options=>launch({...options,args:[...options.args,'--single-process','--no-zygote','--no-proxy-server']});
process.argv=[process.argv[0],'/private-original-browser.mjs','/bridge/app.sock','/opt/playwright/index.mjs'];
await import('data:text/javascript;base64,'+source.toString('base64'));
