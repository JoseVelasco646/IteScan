import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import WhitelistAdmin from '@/components/WhitelistAdmin.vue'
import NotFound from '@/views/NotFound.vue'
import AccessDenied from '@/views/AccessDenied.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/whitelist',
      name: 'whitelist',
      component: WhitelistAdmin
    },
    {
      path: '/access-denied',
      name: 'access-denied',
      component: AccessDenied
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFound
    }
  ],
})

export default router
