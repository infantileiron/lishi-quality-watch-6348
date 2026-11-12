from dataclasses import asdict
from src.models.entities import SupplementLog
from src.utils import repository as repo
from src.utils.identity import new_id,now
from src.services.dataset import parse_csv,fingerprint,normalize

def list_supplements(dataset_id):
 # 仅返回该数据集的补传批次元数据与逐条结论，避免重复搬运整个测量数据
 logs=[x for x in repo.all_rows('supplements') if x['dataset_id']==dataset_id]
 return sorted(logs,key=lambda x:x['created_at'])

def detail(supplement_id):
 return repo.get('supplements',supplement_id)

def _index_existing(rows):
 by_sample={r['sample_id']:r for r in rows}
 by_key={(r['machine'],r['sequence']):r for r in rows}
 return by_sample,by_key

def supplement(dataset_id,data,actor):
 dataset=normalize(repo.get('datasets',dataset_id))
 existing_rows=dataset['rows']
 incoming,invalid=parse_csv(data.csv_text)
 fp=fingerprint(incoming)
 before_count=len(existing_rows)
 from_version=dataset['version']

 # 幂等：同一份补传文件（内容指纹相同）重复执行，原样返回上次批次且不新增版本
 prior=next((s for s in reversed(dataset['supplements']) if s['fingerprint']==fp),None)
 if prior is not None:
  saved=repo.get('supplements',prior['id'])
  saved['idempotent_replay']=True
  return saved

 added=[];corrected=[];duplicated=[];conflicts=[]
 by_sample,by_key=_index_existing(existing_rows)

 for row in incoming:
  same_sample=by_sample.get(row['sample_id'])
  same_key=by_key.get((row['machine'],row['sequence']))
  payload={'sample_id':row['sample_id'],'machine':row['machine'],'sequence':row['sequence'],'value':row['value']}
  if same_sample is not None and same_key is not None:
   if same_sample is same_key:
    if same_sample['value']==row['value']:
     duplicated.append({**payload,'reason':'样本编号与机台序号均一致且尺寸相同，原样重复'})
    else:
     corrected.append({**payload,'before_value':same_sample['value'],'after_value':row['value'],
      'before_machine':same_sample['machine'],'before_sequence':same_sample['sequence'],
      'reason':'同一观测尺寸更正'})
   else:
    # 样本编号和机台序号分别命中两条不同的既有记录，键归属互相冲突
    conflicts.append({**payload,'reason':f"样本编号已属于 {same_sample['machine']} 第{same_sample['sequence']}次；机台序号已属于样本 {same_key['sample_id']}"})
  elif same_sample is not None:
   # 同一目标机台序号空闲（same_key 为空），允许把该样本更正到新机台/序号；若被占用则落入冲突分支
   moved=(same_sample['machine']!=row['machine'] or same_sample['sequence']!=row['sequence'])
   value_changed=same_sample['value']!=row['value']
   if moved:
    reason=f"机台序号更正：{same_sample['machine']} 第{same_sample['sequence']}次 → {row['machine']} 第{row['sequence']}次"+('，且尺寸更正' if value_changed else '')
   else:
    reason='同一观测尺寸更正'
   corrected.append({**payload,'before_value':same_sample['value'],'after_value':row['value'],
    'before_machine':same_sample['machine'],'before_sequence':same_sample['sequence'],'reason':reason})
  elif same_key is not None:
   conflicts.append({**payload,'reason':f"机台序号 {row['machine']} 第{row['sequence']}次已属于样本 {same_key['sample_id']}，样本编号 {row['sample_id']} 与之冲突"})
  else:
   added.append(payload)

 has_blocking=bool(conflicts or invalid)
 applied=not has_blocking
 # 仅当数据真实变化（新增或更正）才升版本；纯原样重复不改变数据与版本
 changed=bool(added or corrected)
 after_count=before_count
 to_version=from_version

 if applied:
  # 以样本编号为主键合入：更正替换旧行，新增追加，保持机台/序号排序稳定
  merged={r['sample_id']:dict(r) for r in existing_rows}
  for row in incoming:
   merged[row['sample_id']]=dict(row)
  new_rows=sorted(merged.values(),key=lambda r:(r['machine'],r['sequence'],r['sample_id']))
  after_count=len(new_rows)
  if changed:
   to_version=from_version+1
   dataset['rows']=new_rows
   dataset['version']=to_version
   dataset['current_fingerprint']=fingerprint(new_rows)

 status='conflicted' if has_blocking else ('applied' if changed else 'unchanged')
 log=SupplementLog(new_id('sup'),dataset_id,data.source,status,fp,applied,
  added,corrected,duplicated,conflicts,invalid,before_count,after_count,from_version,to_version,
  actor=actor,note=data.note,created_at=now())
 saved=asdict(log)
 repo.put('supplements',saved)

 # 无论生效与否都留存批次引用，保证页面可追溯；计数随引用列表推导，避免漂移
 dataset.setdefault('supplements',[]).append({'id':saved['id'],'fingerprint':fp,'status':saved['status'],'created_at':saved['created_at'],'applied':applied})
 dataset['supplement_count']=len(dataset['supplements'])
 repo.put('datasets',dataset)

 return saved
