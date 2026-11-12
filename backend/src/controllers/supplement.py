from src.services import supplement as service
def list_supplements(dataset_id): return service.list_supplements(dataset_id)
def detail(supplement_id): return service.detail(supplement_id)
def apply_supplement(dataset_id,data,user): return service.supplement(dataset_id,data,user['email'])
