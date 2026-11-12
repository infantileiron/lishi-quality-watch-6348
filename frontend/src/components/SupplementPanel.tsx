import {useState,useEffect} from 'react';
import * as api from '../api/datasets';
import {refreshResources} from '../stores/resources';
import type {Dataset,SupplementLog,SupplementRow} from '../types/entities';

const fmt=(v?:number)=>v===undefined?'—':Number(v).toFixed(5);
const time=(iso:string)=>iso?new Date(iso).toLocaleString('zh-CN',{hour12:false}):'—';

function ResultTable({title,rows,kind}:{title:string;rows:SupplementRow[];kind:string}){
 if(!rows.length)return null;
 return <div className="sup-group">
  <h3><span className={'sup-tag '+kind}>{title}</span><b>{rows.length}</b></h3>
  <div className="table-scroll"><table><thead><tr><th>样本编号</th><th>机台</th><th>序号</th><th>原尺寸 mm</th><th>补传尺寸 mm</th><th>原因</th></tr></thead>
  <tbody>{rows.map((r,i)=><tr key={i}><td>{r.sample_id}</td><td>{r.machine}</td><td>{r.sequence}</td><td>{fmt(r.before_value)}</td><td>{fmt(r.after_value??r.value)}</td><td className="sup-reason">{r.reason}</td></tr>)}</tbody></table></div>
 </div>;
}

export default function SupplementPanel({datasets,canEdit}:{datasets:Dataset[];canEdit:boolean}){
 const [datasetId,setDatasetId]=useState(datasets[0]?.id??'');
 const [csv,setCsv]=useState('');const [source,setSource]=useState('shaft_diameter_202611_supplement.csv');
 const [note,setNote]=useState('');const [message,setMessage]=useState('');
 const [result,setResult]=useState<SupplementLog|null>(null);
 const [history,setHistory]=useState<SupplementLog[]>([]);
 const [activeDataset,setActiveDataset]=useState('');

 const target=datasets.find(d=>d.id===datasetId)||datasets[0];
 useEffect(()=>{if(target&&!activeDataset){setActiveDataset(target.id);api.supplements(target.id).then(setHistory).catch(()=>setHistory([]));}},[datasets]);
 const pick=async(id:string)=>{setDatasetId(id);setResult(null);setActiveDataset(id);
  try{setHistory(await api.supplements(id));}catch{setHistory([]);}}
 const submit=async(e:React.FormEvent)=>{e.preventDefault();
  if(!target){setMessage('请先选择要合入的测量文件');return;}
  try{const log=await api.applySupplement(target.id,{source,csv_text:csv,note});setResult(log);setMessage('');
   setHistory(await api.supplements(target.id));refreshResources();
   if(log.applied){setCsv('');setNote('');}
  }catch(err:any){setMessage(err.message);}};
 const viewLog=async(id:string)=>{try{setResult(await api.supplementDetail(id));}catch(err:any){setMessage(err.message);}};

 return <section className="paper">
  <h2>量测文件补传合入</h2>
  <p className="method-note"><small>逐条比对样本编号与机台序号：新增观测直接合入；同一观测尺寸变更记为更正；完全一致记为原样重复。样本编号与机台序号互相冲突或行内校验失败时整批不生效、不新增版本。同一份文件重复补传按内容指纹识别，不重复产生版本。已锁定基线、运行、复核与报告保留原始快照，新建基线才使用更正后的数据。</small></p>
  {!datasets.length?<div className="empty">暂无测量文件，请先导入初始测量数据</div>:<>
  {canEdit&&<form className="form-grid" onSubmit={submit}>
   <label>合入目标测量文件<select value={target?.id??''} onChange={e=>pick(e.target.value)}>{datasets.map(d=><option key={d.id} value={d.id}>{d.name}（v{d.version} · {d.row_count}条）</option>)}</select></label>
   <label>补传来源文件<input value={source} onChange={e=>setSource(e.target.value)} placeholder="补传CSV文件名"/></label>
   <label>选择补传CSV<input type="file" accept=".csv" onChange={async e=>{const f=e.target.files?.[0];if(f){if(f.size>1000000){setMessage('CSV不能超过1MB');return}setCsv(await f.text());}}}/></label>
   <label>补传说明（可选）<input value={note} maxLength={500} onChange={e=>setNote(e.target.value)} placeholder="本次补传的更正背景"/></label>
   <label className="wide">补传内容<textarea value={csv} onChange={e=>setCsv(e.target.value)} placeholder="sample_id,machine,sequence,value"/></label>
   <button className="primary" type="submit">校验并合入补传</button>
  </form>}
  {!canEdit&&<p className="method-note"><small>当前为只读账号，可查看补传溯源；合入操作需分析员或管理员权限。</small></p>}
  {message&&<div role="alert" className="notice">{message}</div>}

  {result&&<div className="sup-result">
   <div className="sup-summary">
    <span className={'badge '+result.status}>{!result.applied?'整批冲突未生效':result.idempotent_replay?'幂等重复':result.status==='unchanged'?'原样未变':'已合入'}</span>
    <b>{result.source}</b>
    <small>版本 v{result.from_version}{result.applied&&!result.idempotent_replay?` → v${result.to_version}`:''} · 观测 {result.before_count} → {result.after_count} · {time(result.created_at)}{result.actor?` · ${result.actor}`:''}</small>
    {result.idempotent_replay&&<small className="sup-reason">该内容指纹已存在，原样返回上次结果，未新增版本。</small>}
    {result.note&&<small>说明：{result.note}</small>}
   </div>
   <ResultTable title="新增" kind="added" rows={result.added}/>
   <ResultTable title="更正" kind="corrected" rows={result.corrected}/>
   <ResultTable title="原样重复" kind="duplicated" rows={result.duplicated}/>
   <ResultTable title="冲突（整批不生效）" kind="conflicted" rows={result.conflicts}/>
   <ResultTable title="无效行（整批不生效）" kind="conflicted" rows={result.invalid as SupplementRow[]}/>
  </div>}

  <div className="sup-history">
   <h3>补传溯源（{target?.name}）</h3>
   {!canEdit&&<label className="sup-viewer-pick">选择测量文件<select value={target?.id??''} onChange={e=>pick(e.target.value)}>{datasets.map(d=><option key={d.id} value={d.id}>{d.name}（v{d.version}）</option>)}</select></label>}
   {!history.length?<div className="empty">该测量文件暂无补传记录</div>:
    <div className="table-scroll"><table><thead><tr><th>补传时间</th><th>来源</th><th>状态</th><th>版本变化</th><th>新增/更正/重复</th><th>冲突/无效</th><th>操作</th></tr></thead>
    <tbody>{history.map(h=><tr key={h.id}><td>{time(h.created_at)}</td><td>{h.source}</td><td><span className={'badge '+h.status}>{h.status==='conflicted'?'未生效':h.status==='unchanged'?'原样未变':'已合入'}</span></td><td>v{h.from_version}{h.applied&&h.to_version!==h.from_version?` → v${h.to_version}`:'（不变）'}</td><td>{h.added.length} / {h.corrected.length} / {h.duplicated.length}</td><td>{h.conflicts.length} / {h.invalid.length}</td><td><button type="button" onClick={()=>viewLog(h.id)}>查看前后变化</button></td></tr>)}</tbody></table></div>}
  </div>
  </>}
 </section>;
}
