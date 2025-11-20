import axios from 'axios';
import { SearchResult, SearchFilters } from '@/types/notebook';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
});

export const searchNotebooks = async (
  query: string, 
  filters: SearchFilters,
  page: number = 1
): Promise<SearchResult> => {
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  params.append('page', page.toString());
  
  if (filters.tags) filters.tags.forEach(t => params.append('tags', t));
  if (filters.services) filters.services.forEach(s => params.append('services', s));
  if (filters.difficulty) filters.difficulty.forEach(d => params.append('difficulty', d));

  const response = await api.get<SearchResult>('/search', { params });
  return response.data;
};

export const getNotebook = async (id: string) => {
  const response = await api.get(`/notebooks/${id}`);
  return response.data;
};
