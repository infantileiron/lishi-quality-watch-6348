from dataclasses import dataclass,field
from typing import Any
@dataclass
class MeasurementDataset:
 id:str
 name:str
 source:str
 rows:list[dict]
 created_at:str=''
 version:int=1
 current_fingerprint:str=''
 supplement_count:int=0
 supplements:list[dict]=field(default_factory=list)
@dataclass
class SupplementLog:
 id:str
 dataset_id:str
 source:str
 status:str
 fingerprint:str
 applied:bool
 added:list[dict]=field(default_factory=list)
 corrected:list[dict]=field(default_factory=list)
 duplicated:list[dict]=field(default_factory=list)
 conflicts:list[dict]=field(default_factory=list)
 invalid:list[dict]=field(default_factory=list)
 before_count:int=0
 after_count:int=0
 from_version:int=1
 to_version:int=1
 actor:str=''
 note:str=''
 created_at:str=''
@dataclass
class BaselineWindow:
 id:str
 name:str
 dataset_id:str
 machine:str
 start:int
 end:int
 values:list[float]
 mean:float
 sigma:float
 created_at:str=''
@dataclass
class ControlStudy:
 id:str
 name:str
 baseline_id:str
 monitoring_start:int
 monitoring_end:int
 smoothing:float=.2
 control_width:float=3
 lsl:float=19.95
 usl:float=20.05
 created_at:str=''
@dataclass
class ControlRun:
 id:str
 study_id:str
 status:str='queued'
 result:dict[str,Any]=field(default_factory=dict)
 error:str=''
 created_at:str=''
@dataclass
class DeviationReview:
 id:str
 run_id:str
 comment:str
 status:str='pending'
 reviewer:str=''
 created_at:str=''
@dataclass
class Report:
 id:str
 run_id:str
 review_id:str
 title:str
 created_at:str=''
