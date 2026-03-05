import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import AdminPanel from '@/components/AdminPanel.vue'
import Login from '@/views/Login.vue'
import NotFound from '@/views/NotFound.vue'

const API_URL = import.meta.env.VITE_API_URL || window.location.origin.replace(':3000', ':8000')

// Decode JWT locally to check expiry without network call
function isTokenValid(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp * 1000 > Date.now()
  } catch {
    return false
  }
}

function getUserFromToken(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return { 
      user_id: payload.user_id, 
      username: payload.username, 
      role: payload.role || 'viewer' 
    }
  } catch {
    return null
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: { public: true }
    },
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminPanel,
      meta: { requiresAuth: true, requiresRole: 'admin' }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFound
    }
  ],
})

// Guard de autenticación - JWT se decodifica localmente, 
// solo se valida con el servidor al boot o periódicamente
router.beforeEach(async (to, from, next) => {
  if (to.meta.public) {
    const token = localStorage.getItem('admin_token')
    if (token && to.name === 'login' && isTokenValid(token)) {
      return next({ name: 'dashboard' })
    }
    return next()
  }

  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('admin_token')
    if (!token) {
      return next({ name: 'login', query: { redirect: to.fullPath } })
    }

    // Verificar token localmente (sin network call)
    if (!isTokenValid(token)) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
      window.dispatchEvent(new CustomEvent('session-expired'))
      return next({ name: 'login', query: { redirect: to.fullPath, expired: '1' } })
    }

    // Verificar rol si la ruta lo requiere
    if (to.meta.requiresRole) {
      const ROLE_LEVELS = { admin: 4, mod: 3, op: 2, viewer: 1 }
      const user = getUserFromToken(token) || JSON.parse(localStorage.getItem('admin_user') || '{}')
      const userLevel = ROLE_LEVELS[user.role] || 1
      const requiredLevel = ROLE_LEVELS[to.meta.requiresRole] || 1
      if (userLevel < requiredLevel) {
        return next({ name: 'dashboard' })
      }
    }
    
    return next()
  }

  next()
})

export default router
