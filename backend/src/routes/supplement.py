from fastapi import APIRouter,Depends
from src.controllers import supplement as controller
from src.schemas.entities import SupplementInput
from src.services.auth import current,editor
router=APIRouter(tags=["supplements"])
@router.post("/datasets/{dataset_id}/supplements",status_code=201)
def apply_supplement(dataset_id:str,data:SupplementInput,user=Depends(editor)):
 return controller.apply_supplement(dataset_id,data,user)
@router.get("/datasets/{dataset_id}/supplements")
def list_supplements(dataset_id:str,user=Depends(current)):
 return controller.list_supplements(dataset_id)
@router.get("/supplements/{supplement_id}")
def detail(supplement_id:str,user=Depends(current)):
 return controller.detail(supplement_id)
