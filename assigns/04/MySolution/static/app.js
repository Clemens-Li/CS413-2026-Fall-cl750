/* View: draft editing, control enablement, literal rendering, request forwarding.
   When served by app.py, language work goes through the Python MVC HTTP API.
   file:// / offline opens use the bundled JavaScript worker as a fallback. */
const $ = id => document.getElementById(id);
let state = {source:'',name:'Untitled',revision:0,results:[]}, examples = {}, busy = false, draftName = 'Untitled';
const dirty = () => $('editor').value !== state.source;
const bytes = text => new TextEncoder().encode(text).length;
function notice(text='') { $('notice').textContent=text; $('notice').hidden=!text; }
function render() {
  $('source-name').textContent = draftName;
  $('revision').textContent = state.revision ? `Revision ${state.revision}` : 'No applied source';
  $('edit-state').textContent = dirty() ? 'Unapplied changes' : state.revision ? 'All changes applied' : 'Ready to write';
  $('size').textContent = `${bytes($('editor').value).toLocaleString()} bytes · UTF-8`;
  $('editor').disabled=busy;
  $('load').disabled=busy || dirty();
  $('apply').disabled=busy || !dirty();
  $('discard').disabled=busy || !dirty();
  document.querySelectorAll('[data-action]').forEach(button => button.disabled=busy || dirty() || !state.revision || button.dataset.action==='execute');
  $('status').textContent=busy ? 'Working…' : dirty() ? 'Apply or discard your edits to continue' : 'Ready';
  $('result-count').textContent=state.results.length;
  if (state.results.length) {
    $('results').replaceChildren(...state.results.slice().reverse().map(result => {
      const item=document.createElement('article'); item.className='result'; item.dataset.outcome=result.outcome;
      const meta=document.createElement('div'); meta.className='result-meta'; meta.textContent=`${result.operation} / Revision ${result.revision} / ${result.outcome.replaceAll('_',' ')}`;
      const text=document.createElement('pre'); text.textContent=result.text;
      item.append(meta,text); return item;
    }));
  } else { $('results').replaceChildren(empty.cloneNode(true)); }
}
const empty=$('results').firstElementChild.cloneNode(true);
// Browser counterpart of the Python model/controller; used only for offline / file://.
const workerURL = typeof URL !== 'undefined' && typeof Blob !== 'undefined' && globalThis.LambdaWorkerSource
  ? URL.createObjectURL(new Blob([globalThis.LambdaWorkerSource], {type:'text/javascript'}))
  : 'worker.js';
if (typeof window !== 'undefined') window.addEventListener('unload', () => { if (workerURL.startsWith('blob:')) URL.revokeObjectURL(workerURL); });
function runWorker(operation, source) {
  return new Promise((resolve) => {
    const worker = new Worker(workerURL);
    const finish = value => { clearTimeout(timer); worker.terminate(); resolve(value); };
    const timer = setTimeout(() => finish({outcome:'backend_error', text:'Execution stopped after the 3-second time limit. Edit your program or retry.'}), 3000);
    worker.onmessage = event => finish(event.data);
    worker.onerror = event => { event.preventDefault(); finish({outcome:'backend_error', text:'Language worker failed. Your source is preserved; try again.'}); };
    worker.postMessage({operation, source});
  });
}
async function localApi(path, data) {
  if (path === '/api/state') return state;
  if (path === '/api/examples') return globalThis.LambdaExamples;
  if (path === '/api/source') {
    if (typeof data.source !== 'string' || !data.source.trim()) throw Error('Source cannot be empty. Enter a constructor expression.');
    if (bytes(data.source)>65536) throw Error('Source exceeds the 65,536-byte limit.');
    return {...state, source:data.source, name:String(data.name).slice(0,200), revision:state.revision+1, results:[]};
  }
  if (path === '/api/action') {
    if (!state.revision) throw Error('Apply source before running tools.');
    if (!['lint','interpret','typecheck','compile'].includes(data.operation)) throw Error('Unknown operation.');
    const result = await runWorker(data.operation, state.source);
    return {...state, results:[...state.results, {...result, operation:data.operation, revision:state.revision}]};
  }
  throw Error('Unknown operation.');
}
async function api(path, data) {
  const http = typeof location !== 'undefined' && /^https?:/.test(location.protocol);
  if (!http) return localApi(path, data);
  const options = data === undefined
    ? undefined
    : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)};
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw Error(body.error || 'Request failed.');
  return body;
}
async function work(callback) {
  busy=true;notice();render();
  try { await callback(); } catch(error) {notice(error.message || 'Connection failed. Your edits are preserved.');}
  finally {busy=false;render();}
}
async function apply(source,name) {
  state=await api('/api/source',{source,name});
  $('editor').value=state.source;draftName=state.name;
}
$('editor').addEventListener('input',render);
$('apply').onclick=()=>work(()=>apply($('editor').value,draftName));
$('discard').onclick=()=>{$('editor').value=state.source;draftName=state.name;notice();render();};
$('load').onchange=async event=>{
  const choice=event.target.value;event.target.value='';
  if(choice==='file') return $('file').click();
  if(choice==='manual') { $('editor').value='';draftName='Untitled';notice();render();$('editor').focus();return; }
  if(examples[choice]) await work(()=>apply(examples[choice],`${choice}.lambda`));
};
$('file').onchange=async()=>{
  const file=$('file').files[0];$('file').value='';if(!file)return;
  await work(async()=>{
    if(file.size>65536) throw new Error('File exceeds the 65,536-byte limit.');
    let source;
    try {source=new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer());}
    catch {throw new Error('The file is not valid UTF-8.');}
    await apply(source,file.name);
  });
};
document.querySelectorAll('[data-action]').forEach(button=>button.onclick=()=>work(async()=>{state=await api('/api/action',{operation:button.dataset.action});}));
$('editor').addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key==='Enter'){event.preventDefault();if(!$('apply').disabled)$('apply').click();}});
window.addEventListener('beforeunload',event=>{if(dirty()){event.preventDefault();event.returnValue='';}});
work(async()=>{
  [state,examples]=await Promise.all([api('/api/state'),api('/api/examples')]);
  $('editor').value=state.source;draftName=state.name;
  const mode = document.querySelector('.local');
  if (mode) {
    const http = typeof location !== 'undefined' && /^https?:/.test(location.protocol);
    mode.innerHTML = http ? '<i></i> Local Python server' : '<i></i> Browser environment';
  }
});
