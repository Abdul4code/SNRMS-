import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ── Public ──────────────────────────────────────────────────────────────
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { public: true },
    },

    // ── Root redirect ────────────────────────────────────────────────────────
    {
      path: '/',
      redirect: '/dashboard',
    },

    // ── Dashboard ────────────────────────────────────────────────────────────
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },

    // ── Applicant routes ─────────────────────────────────────────────────────
    {
      path: '/applications',
      name: 'application-list',
      component: () => import('@/views/applicant/ApplicationListView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/applications/new',
      name: 'application-new',
      component: () => import('@/views/applicant/ApplicationNewView.vue'),
      meta: { requiresAuth: true, roles: ['applicant'] },
    },
    {
      path: '/applications/:id',
      name: 'application-detail',
      component: () => import('@/views/applicant/ApplicationDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/applications/:id/documents',
      name: 'application-documents',
      component: () => import('@/views/applicant/ApplicationDocumentsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/applications/:id/payment',
      name: 'application-payment',
      component: () => import('@/views/applicant/ApplicationPaymentView.vue'),
      meta: { requiresAuth: true },
    },

    // ── Common authenticated ─────────────────────────────────────────────────
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('@/views/NotificationsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },

    // ── Staff routes ─────────────────────────────────────────────────────────
    {
      path: '/staff/dashboard',
      name: 'staff-dashboard',
      component: () => import('@/views/staff/StaffDashboardView.vue'),
      meta: { requiresAuth: true, roles: ['finance', 'naming_committee', 'committee_chairman'] },
    },
    {
      path: '/staff/applications',
      name: 'staff-application-list',
      component: () => import('@/views/staff/StaffApplicationListView.vue'),
      meta: { requiresAuth: true, roles: ['finance', 'naming_committee', 'committee_chairman'] },
    },
    {
      path: '/staff/applications/:id',
      name: 'staff-application-detail',
      component: () => import('@/views/staff/StaffApplicationDetailView.vue'),
      meta: { requiresAuth: true, roles: ['finance', 'naming_committee', 'committee_chairman'] },
    },

    // ── Admin routes ──────────────────────────────────────────────────────────
    {
      path: '/admin/staff',
      name: 'staff-management',
      component: () => import('@/views/admin/StaffManagementView.vue'),
      meta: { requiresAuth: true, roles: ['committee_chairman'] },
    },
    {
      path: '/admin/fees',
      name: 'fee-config',
      component: () => import('@/views/admin/FeeConfigView.vue'),
      meta: { requiresAuth: true, roles: ['finance'] },
    },
    {
      path: '/admin/street-types',
      name: 'street-type-config',
      component: () => import('@/views/admin/StreetTypeConfigView.vue'),
      meta: { requiresAuth: true, roles: ['naming_committee'] },
    },

    // ── 404 fallback ─────────────────────────────────────────────────────────
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { public: true },
    },
  ],
})

// ── Navigation guard ─────────────────────────────────────────────────────────
router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()

  // If route is public, allow always
  if (to.meta.public) {
    // If already authenticated, redirect to dashboard
    if (auth.accessToken && !to.path.includes('/login') && !to.path.includes('/register')) {
      if (!auth.user) await auth.fetchProfile().catch(() => {})
      return next(getRoleDefault(auth.user?.role))
    }
    return next()
  }

  // Requires auth
  if (to.meta.requiresAuth) {
    if (!auth.accessToken) {
      return next({ name: 'login', query: { redirect: to.fullPath } })
    }
    // Load user profile if not loaded
    if (!auth.user) {
      try {
        await auth.fetchProfile()
      } catch {
        auth.logout()
        return next({ name: 'login' })
      }
    }
    // Role check
    const allowedRoles = to.meta.roles as string[] | undefined
    if (allowedRoles && auth.user && !allowedRoles.includes(auth.user.role)) {
      return next(getRoleDefault(auth.user.role))
    }
    return next()
  }

  next()
})

function getRoleDefault(role?: string): string {
  switch (role) {
    case 'applicant':
      return '/applications'
    case 'finance':
    case 'naming_committee':
    case 'committee_chairman':
      return '/staff/dashboard'
    default:
      return '/login'
  }
}

export { getRoleDefault }
export default router
