import axios from 'axios'

const http = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
})

// ── Visitors ──────────────────────────────────────────────────────────────
export function registerVisitor(formData) {
  return http.post('/api/visitors/register', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getVisitor(visitorId) {
  return http.get(`/api/visitors/${visitorId}`)
}

// ── Tickets ───────────────────────────────────────────────────────────────
export function createTicket(data) {
  return http.post('/api/tickets', data)
}

export function listTickets(params) {
  return http.get('/api/tickets', { params })
}

export function getTicket(ticketId) {
  return http.get(`/api/tickets/${ticketId}`)
}

// ── Checkin ───────────────────────────────────────────────────────────────
export function verifyCheckin(formData) {
  return http.post('/api/checkin/verify', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ── Stats ─────────────────────────────────────────────────────────────────
export function getDailyStats(date) {
  return http.get('/api/stats/daily', { params: { date } })
}

export function getRangeStats(start, end) {
  return http.get('/api/stats/range', { params: { start, end } })
}

export function getRealtimeStats() {
  return http.get('/api/stats/realtime')
}
