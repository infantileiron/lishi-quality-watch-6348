import csv,io,math,json,hashlib
from dataclasses import asdict
from src.models.entities import MeasurementDataset
from src.utils import repository as repo
from src.utils.identity import new_id,now

REQUIRED_COLUMNS={'sample_id','machine','sequence','value'}
MAX_ROWS=5000

def fingerprint(rows):
 # 以机台序号与样本编号排序后的规范内容计算指纹，保证同一份补传文件指纹稳定
 canonical=json.dumps(sorted(rows,key=lambda r:(r['machine'],r['sequence'],r['sample_id'])),ensure_ascii=False,sort_keys=True)
 return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def normalize(item):
 # 兼容补传功能上线前写入的旧数据集，补全版本与溯源字段
 item.setdefault('version',1)
 item.setdefault('current_fingerprint',fingerprint(item['rows']))
 item.setdefault('supplement_count',0)
 item.setdefault('supplements',[])
 return item

def parse_csv(csv_text):
 reader=csv.DictReader(io.StringIO(csv_text.lstrip('\ufeff')))
 if not REQUIRED_COLUMNS.issubset(reader.fieldnames or []):
  raise ValueError('CSV需要sample_id,machine,sequence,value列；value单位mm')
 rows=[];ids=set();keys=set();invalid=[]
 for n,r in enumerate(reader,2):
  if n>MAX_ROWS+1:raise ValueError(f'最多{MAX_ROWS}次单值观测')
  try:
   seq=int(r['sequence']);value=float(r['value']);machine=(r.get('machine') or '').strip();sample=(r.get('sample_id') or '').strip()
   key=(machine,seq)
   if not math.isfinite(value) or not 0<value<=1000000 or seq<1 or not machine or not sample or sample in ids or key in keys:raise ValueError()
  except (TypeError,ValueError):
   invalid.append({'line':n,'sample_id':(r.get('sample_id') or '').strip(),'machine':(r.get('machine') or '').strip(),'sequence':(r.get('sequence') or '').strip(),'value':(r.get('value') or '').strip(),'reason':'样本编号/机台序号/尺寸无效或文件内重复'})
   continue
  ids.add(sample);keys.add(key);rows.append({'sample_id':sample,'machine':machine,'sequence':seq,'value':value})
 return rows,invalid

def summary(item):return {k:v for k,v in item.items() if k!='rows'}|{'row_count':len(item['rows']),'machines':sorted({r['machine'] for r in item['rows']})}
def list_datasets():return [summary(normalize(x)) for x in repo.all_rows('datasets')]
def detail(id):return normalize(repo.get('datasets',id))
def rename(id,data):
 item=normalize(repo.get('datasets',id));item['name']=data.name;repo.put('datasets',item);return summary(item)
def create(data):
 rows,invalid=parse_csv(data.csv_text)
 if invalid:raise ValueError(f"第{invalid[0]['line']}行样本编号/机台序号/尺寸无效或重复")
 if len(rows)<5:raise ValueError('至少5次单值观测')
 item=MeasurementDataset(new_id('ds'),data.name,data.source,rows,now(),1,fingerprint(rows),0,[])
 repo.put('datasets',item);return summary(asdict(item))
