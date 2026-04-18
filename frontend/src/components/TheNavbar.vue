<template>
  <!-- Top accent line -->
  <div class="h-[3px] w-full" style="background: linear-gradient(90deg, #059669, #10b981 50%, #fbbf24)"></div>

  <nav style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.07)">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-14">

        <!-- Logo + wordmark -->
        <div class="flex items-center gap-7">
          <RouterLink to="/" class="flex items-center gap-2.5 flex-shrink-0">
            <img src="@/assets/logo.png" alt="Ibeju-Lekki LGA"
                 class="w-8 h-8 object-contain"
                 style="filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5))"/>
            <div class="leading-tight">
              <span class="text-white font-bold text-sm tracking-wide block">SNRMS</span>
              <span class="text-emerald-400 text-[10px] tracking-widest uppercase block" style="margin-top:-1px">Ibeju-Lekki LGA</span>
            </div>
          </RouterLink>

          <!-- Desktop nav links -->
          <div class="hidden md:flex items-center gap-0.5">
            <template v-if="auth.isApplicant">
              <NavLink to="/applications">My Applications</NavLink>
            </template>
            <template v-if="auth.isStaff">
              <NavLink to="/staff/dashboard">Dashboard</NavLink>
              <NavLink to="/staff/applications">Applications</NavLink>
            </template>
            <template v-if="auth.isChairman">
              <NavLink to="/admin/staff">Staff</NavLink>
            </template>
            <template v-if="auth.isNamingCommittee">
              <NavLink to="/admin/street-types">Street Types</NavLink>
              <NavLink to="/admin/renewal-settings">Renewal Settings</NavLink>
            </template>
            <template v-if="auth.isFinance">
              <NavLink to="/admin/fees">Fee Config</NavLink>
            </template>
          </div>
        </div>

        <!-- Right: bell + user menu -->
        <div class="hidden md:flex items-center gap-1">
          <!-- Notification bell -->
          <RouterLink to="/notifications"
                      class="relative p-2 rounded-lg transition-colors"
                      style="color: rgba(255,255,255,0.5)"
                      :class="['hover:bg-white/5 hover:!text-white']">
            <BellIcon class="w-5 h-5" />
            <span v-if="notificationStore.unreadCount > 0"
                  class="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center font-bold leading-none">
              {{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}
            </span>
          </RouterLink>

          <!-- User dropdown -->
          <Menu as="div" class="relative ml-1">
            <MenuButton class="flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors hover:bg-white/5"
                        style="color: rgba(255,255,255,0.85)">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                   style="background: linear-gradient(135deg, #059669, #047857)">
                {{ initials }}
              </div>
              <span class="text-sm font-medium">{{ auth.user?.full_name || auth.user?.email }}</span>
              <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                    style="background: rgba(5,150,105,0.2); color: #34d399; border: 1px solid rgba(52,211,153,0.3)">
                {{ roleLabel }}
              </span>
              <ChevronDownIcon class="w-3.5 h-3.5 opacity-50" />
            </MenuButton>
            <Transition enter-active-class="transition ease-out duration-100"
                        enter-from-class="transform opacity-0 scale-95"
                        enter-to-class="transform opacity-100 scale-100"
                        leave-active-class="transition ease-in duration-75"
                        leave-from-class="transform opacity-100 scale-100"
                        leave-to-class="transform opacity-0 scale-95">
              <MenuItems class="absolute right-0 mt-2 w-52 rounded-xl shadow-xl ring-1 ring-black/10 focus:outline-none z-50 overflow-hidden"
                         style="background: #fff">
                <div class="px-4 py-3 border-b border-slate-100">
                  <p class="text-xs font-semibold text-slate-900 truncate">{{ auth.user?.full_name }}</p>
                  <p class="text-xs text-slate-500 truncate mt-0.5">{{ auth.user?.email }}</p>
                </div>
                <div class="py-1">
                  <MenuItem v-slot="{ active }">
                    <RouterLink to="/profile"
                                :class="[active ? 'bg-slate-50' : '', 'flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700']">
                      <UserCircleIcon class="w-4 h-4 text-slate-400" />
                      My Profile
                    </RouterLink>
                  </MenuItem>
                  <MenuItem v-slot="{ active }">
                    <RouterLink to="/notifications"
                                :class="[active ? 'bg-slate-50' : '', 'flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700']">
                      <BellIcon class="w-4 h-4 text-slate-400" />
                      Notifications
                    </RouterLink>
                  </MenuItem>
                </div>
                <div class="border-t border-slate-100 py-1">
                  <MenuItem v-slot="{ active }">
                    <button :class="[active ? 'bg-red-50' : '', 'w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-600']"
                            @click="handleLogout">
                      <ArrowRightOnRectangleIcon class="w-4 h-4" />
                      Sign out
                    </button>
                  </MenuItem>
                </div>
              </MenuItems>
            </Transition>
          </Menu>
        </div>

        <!-- Mobile: bell + hamburger -->
        <div class="md:hidden flex items-center gap-1">
          <RouterLink to="/notifications" class="relative p-2 rounded-lg" style="color: rgba(255,255,255,0.5)">
            <BellIcon class="w-5 h-5" />
            <span v-if="notificationStore.unreadCount > 0"
                  class="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center font-bold">
              {{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}
            </span>
          </RouterLink>
          <button class="p-2 rounded-lg transition-colors"
                  style="color: rgba(255,255,255,0.6)"
                  @click="mobileOpen = !mobileOpen">
            <Bars3Icon v-if="!mobileOpen" class="w-5 h-5" />
            <XMarkIcon v-else class="w-5 h-5" />
          </button>
        </div>

      </div>
    </div>

    <!-- Mobile menu -->
    <Transition enter-active-class="transition ease-out duration-150"
                enter-from-class="opacity-0 -translate-y-2"
                enter-to-class="opacity-100 translate-y-0"
                leave-active-class="transition ease-in duration-100"
                leave-from-class="opacity-100 translate-y-0"
                leave-to-class="opacity-0 -translate-y-2">
      <div v-if="mobileOpen"
           class="md:hidden pb-4"
           style="border-top: 1px solid rgba(255,255,255,0.07)">

        <!-- User identity strip -->
        <div class="flex items-center gap-3 px-4 py-4" style="border-bottom: 1px solid rgba(255,255,255,0.06)">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
               style="background: linear-gradient(135deg, #059669, #047857)">
            {{ initials }}
          </div>
          <div class="min-w-0">
            <p class="text-sm font-semibold text-white truncate">{{ auth.user?.full_name }}</p>
            <p class="text-[11px] text-emerald-400 font-semibold tracking-wide uppercase mt-0.5">{{ roleLabel }}</p>
          </div>
        </div>

        <!-- Nav links -->
        <div class="px-3 pt-3 space-y-0.5">
          <template v-if="auth.isApplicant">
            <MobileLink to="/applications" @click="mobileOpen = false">My Applications</MobileLink>
          </template>
          <template v-if="auth.isStaff">
            <MobileLink to="/staff/dashboard" @click="mobileOpen = false">Dashboard</MobileLink>
            <MobileLink to="/staff/applications" @click="mobileOpen = false">Applications</MobileLink>
          </template>
          <template v-if="auth.isChairman">
            <MobileLink to="/admin/staff" @click="mobileOpen = false">Staff Management</MobileLink>
          </template>
          <template v-if="auth.isNamingCommittee">
            <MobileLink to="/admin/street-types" @click="mobileOpen = false">Street Types</MobileLink>
            <MobileLink to="/admin/renewal-settings" @click="mobileOpen = false">Renewal Settings</MobileLink>
          </template>
          <template v-if="auth.isFinance">
            <MobileLink to="/admin/fees" @click="mobileOpen = false">Fee Configuration</MobileLink>
          </template>
          <MobileLink to="/profile" @click="mobileOpen = false">My Profile</MobileLink>
        </div>

        <!-- Sign out -->
        <div class="px-3 pt-2" style="border-top: 1px solid rgba(255,255,255,0.06); margin-top: 8px; padding-top: 12px">
          <button class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-red-400 hover:bg-red-500/10 transition-colors"
                  @click="handleLogout">
            <ArrowRightOnRectangleIcon class="w-4 h-4" />
            Sign out
          </button>
        </div>
      </div>
    </Transition>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue'
import {
  BellIcon,
  UserCircleIcon,
  ChevronDownIcon,
  Bars3Icon,
  XMarkIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notifications'

const auth = useAuthStore()
const notificationStore = useNotificationStore()
const router = useRouter()
const mobileOpen = ref(false)

const roleLabel = computed(() => {
  const map: Record<string, string> = {
    applicant: 'Applicant',
    finance: 'Finance',
    naming_committee: 'Committee',
    committee_chairman: 'Chairman',
  }
  return map[auth.user?.role ?? ''] ?? auth.user?.role ?? ''
})

const initials = computed(() => {
  const u = auth.user
  if (!u) return '?'
  if (u.first_name && u.last_name) return (u.first_name[0] + u.last_name[0]).toUpperCase()
  return (u.email?.[0] ?? '?').toUpperCase()
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(() => {
  notificationStore.fetchUnreadCount()
})
</script>

<script lang="ts">
import { defineComponent, h } from 'vue'
import { RouterLink as RL, useLink } from 'vue-router'

export const NavLink = defineComponent({
  props: { to: String },
  setup(props, { slots }) {
    return () => {
      const link = useLink({ to: props.to! })
      const isActive = link.isActive?.value || link.isExactActive?.value
      return h(
        RL,
        {
          to: props.to!,
          class: [
            'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            isActive
              ? 'text-emerald-400 bg-emerald-500/10'
              : 'text-white/60 hover:text-white hover:bg-white/5',
          ],
        },
        slots.default,
      )
    }
  },
})

export const MobileLink = defineComponent({
  props: { to: String },
  emits: ['click'],
  setup(props, { slots, emit }) {
    return () => {
      const link = useLink({ to: props.to! })
      const isActive = link.isActive?.value || link.isExactActive?.value
      return h(
        RL,
        {
          to: props.to!,
          class: [
            'flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-colors',
            isActive
              ? 'text-emerald-400 bg-emerald-500/10'
              : 'text-white/65 hover:text-white hover:bg-white/5',
          ],
          onClick: () => emit('click'),
        },
        slots.default,
      )
    }
  },
})
</script>
