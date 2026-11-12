import {request} from './client';import type {Dataset,SupplementLog} from '../types/entities';
export const list=()=>request<Dataset[]>('/datasets');
export const create=(data:unknown)=>request<Dataset>('/datasets','POST',data);
export const detail=(id:string)=>request<Dataset>(`/datasets/${id}`);
export const supplements=(id:string)=>request<SupplementLog[]>(`/datasets/${id}/supplements`);
export const supplementDetail=(id:string)=>request<SupplementLog>(`/supplements/${id}`);
export const applySupplement=(datasetId:string,data:unknown)=>request<SupplementLog>(`/datasets/${datasetId}/supplements`,'POST',data);
