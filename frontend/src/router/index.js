import { createRouter, createWebHistory } from 'vue-router'
import RegisterView from '../views/RegisterView.vue'
import TicketView from '../views/TicketView.vue'
import CheckinView from '../views/CheckinView.vue'
import StatsView from '../views/StatsView.vue'

const routes = [
  { path: '/', redirect: '/register' },
  { path: '/register', component: RegisterView, meta: { title: '游客注册' } },
  { path: '/tickets', component: TicketView, meta: { title: '门票管理' } },
  { path: '/checkin', component: CheckinView, meta: { title: '入园核销' } },
  { path: '/stats', component: StatsView, meta: { title: '客流统计' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
