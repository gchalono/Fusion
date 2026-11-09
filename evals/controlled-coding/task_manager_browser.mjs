/** FNXC:TaskManagerIntegration 2026-11-09-19:53: TEST DOUBLE reference UI behavior control; original CRUD/browser behavior, no invented style or validation criteria. */
import {chromium} from '/opt/task-playwright/index.mjs';
import assert from 'node:assert/strict';
const browser=await chromium.launch({executablePath:'/usr/lib/chromium/chromium',args:['--no-sandbox','--disable-dev-shm-usage','--disable-background-networking','--disable-component-update','--disable-gpu']});
try {
 const context=await browser.newContext({serviceWorkers:'block'});const external=[];
 await context.route('**/*',route=>{if(route.request().url().startsWith('http://127.0.0.1:8080/'))return route.continue();external.push(route.request().url());return route.abort();});
 const page=await context.newPage();await page.goto('http://127.0.0.1:8080/');
 await page.getByLabel('Task title',{exact:true}).fill('browser control task');await page.getByLabel('Due date').fill('2027-04-17');await page.getByRole('button',{name:'Create task',exact:true}).click();
 const row=page.locator('li').filter({hasText:'browser control task'});await row.waitFor();assert.match(await row.textContent(),/2027-04-17/);
 page.once('dialog',dialog=>dialog.accept('browser edited task'));await row.getByRole('button',{name:'Edit',exact:true}).click();
 const edited=page.locator('li').filter({hasText:'browser edited task'});await edited.waitFor();
 await edited.getByRole('button',{name:'Complete',exact:true}).click();await page.getByText('browser edited task 2027-04-17 completed',{exact:true}).waitFor();
 await page.reload();await edited.waitFor();await edited.getByRole('button',{name:'Delete',exact:true}).click();await edited.waitFor({state:'detached'});
 assert.deepEqual(external,[]);console.log(JSON.stringify({classification:'TEST DOUBLE reference UI control',browser_CRUD:true,external_requests:0}));
} finally {await browser.close();}
