// API 函数封装
import client from './client';
import type {
  Person,
  PersonCreate,
  PersonUpdate,
  PersonStats,
  GiftEvent,
  EventCreate,
  EventUpdate,
  Gift,
  GiftCreate,
  GiftUpdate,
  Relation,
  RelationCreate,
  GraphData,
  HouseholdGraphData,
  DashboardStats,
  Suggestion,
  PersonGroup,
  EventRole,
} from '@/types';

// ========== Persons ==========
export function getPersons(params?: { search?: string; group?: PersonGroup | '' }) {
  return client.get<Person[]>('/persons', { params }).then((r) => r.data);
}

export function createPerson(data: PersonCreate) {
  return client.post<Person>('/persons', data).then((r) => r.data);
}

export function getPerson(id: string) {
  return client.get<Person>(`/persons/${id}`).then((r) => r.data);
}

export function updatePerson(id: string, data: PersonUpdate) {
  return client.put<Person>(`/persons/${id}`, data).then((r) => r.data);
}

export function deletePerson(id: string) {
  return client.delete<{ ok: boolean }>(`/persons/${id}`).then((r) => r.data);
}

export function getPersonStats(id: string) {
  return client.get<PersonStats>(`/persons/${id}/stats`).then((r) => r.data);
}

// ========== Events ==========
export function getEvents(params?: { search?: string; role?: EventRole | '' }) {
  return client.get<GiftEvent[]>('/events', { params }).then((r) => r.data);
}

export function createEvent(data: EventCreate) {
  return client.post<GiftEvent>('/events', data).then((r) => r.data);
}

export function getEvent(id: string) {
  return client.get<GiftEvent>(`/events/${id}`).then((r) => r.data);
}

export function updateEvent(id: string, data: EventUpdate) {
  return client.put<GiftEvent>(`/events/${id}`, data).then((r) => r.data);
}

export function deleteEvent(id: string) {
  return client.delete<{ ok: boolean }>(`/events/${id}`).then((r) => r.data);
}

export function getEventTypes() {
  return client.get<string[]>('/events/types').then((r) => r.data);
}

// ========== Gifts ==========
export function getGifts(params?: { event_id?: string; person_id?: string }) {
  return client.get<Gift[]>('/gifts', { params }).then((r) => r.data);
}

export function createGift(data: GiftCreate) {
  return client.post<Gift>('/gifts', data).then((r) => r.data);
}

export function updateGift(id: string, data: GiftUpdate) {
  return client.put<Gift>(`/gifts/${id}`, data).then((r) => r.data);
}

export function deleteGift(id: string) {
  return client.delete<{ ok: boolean }>(`/gifts/${id}`).then((r) => r.data);
}

// ========== Relations ==========
export function getRelations(personId?: string) {
  return client
    .get<Relation[]>('/relations', { params: { person_id: personId } })
    .then((r) => r.data);
}

export function createRelation(data: RelationCreate) {
  return client.post<Relation>('/relations', data).then((r) => r.data);
}

export function deleteRelation(id: string) {
  return client.delete<{ ok: boolean }>(`/relations/${id}`).then((r) => r.data);
}

// ========== Graph ==========
export function getFamilyTree(params?: { anchor_id?: string; group?: PersonGroup }) {
  return client.get<HouseholdGraphData>('/graph/family', { params }).then((r) => r.data);
}

export function getFriendGraph() {
  return client.get<GraphData>('/graph/friends').then((r) => r.data);
}

// ========== Stats ==========
export function getDashboardStats() {
  return client.get<DashboardStats>('/stats/dashboard').then((r) => r.data);
}

export function getSuggestions() {
  return client.get<Suggestion[]>('/stats/suggestions').then((r) => r.data);
}

// ========== Data ==========
export function exportData() {
  return client
    .post('/data/export', {}, { responseType: 'blob' })
    .then((r) => r.data as Blob);
}

export function importData(file: File) {
  const formData = new FormData();
  formData.append('files', file);
  return client
    .post('/data/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then((r) => r.data);
}
