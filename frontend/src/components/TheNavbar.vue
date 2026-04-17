<template>
  <nav class="bg-blue-700 shadow-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <div class="flex items-center gap-8">
          <RouterLink to="/" class="flex flex-col leading-tight">
            <span class="text-white font-bold text-lg tracking-wide">SNRMS</span>
            <span class="text-blue-200 text-xs">Ibeju-Lekki LGA</span>
          </RouterLink>

          <!-- Desktop nav links -->
          <div class="hidden md:flex items-center gap-1">
            <template v-if="auth.isApplicant">
              <NavLink to="/applications">My Applications</NavLink>
            </template>
            <template v-if="auth.isStaff">
              <NavLink to="/staff/dashboard">Dashboard</NavLink>
              <NavLink to="/staff/applications">Applications</NavLink>
            </template>
            <template v-if="auth.isChairman">
              <NavLink to="/admin/staff">Staff</NavLink>
              <NavLink to="/admin/street-types">Street Types</NavLink>
            </template>
            <template v-if="auth.isChairman || auth.isFinance">
              <NavLink to="/admin/fees">Fee Config</NavLink>
            </template>
          </div>
        </div>

        <!-- Right side -->
        <div class="hidden md:flex items-center gap-3">
          <!-- Notification bell -->
          <RouterLink
            to="/notifications"
            class="relative p-2 rounded-lg text-blue-200 hover:text-white hover:bg-blue-600 transition-colors"
          >
            <BellIcon class="w-5 h-5" />
            <span
              v-if="notificationStore.unreadCount > 0"
              class="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold"
            >
              {{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}
            </span>
          </RouterLink>

          <!-- User menu -->
          <Menu as="div" class="relative">
            <MenuButton
              class="flex items-center gap-2 px-3 py-2 rounded-lg text-white hover:bg-blue-600 transition-colors text-sm"
            >
              <UserCircleIcon class="w-5 h-5 text-blue-200" />
              <span class="font-medium">{{ auth.user?.full_name || auth.user?.email }}</span>
              <span class="text-xs bg-blue-500 px-2 py-0.5 rounded-full text-blue-100 capitalize">
                {{ roleLabel }}
              </span>
              <ChevronDownIcon class="w-4 h-4 text-blue-300" />
            </MenuButton>
            <Transition
              enter-active-class="transition ease-out duration-100"
              enter-from-class="transform opacity-0 scale-95"
              enter-to-class="transform opacity-100 scale-100"
              leave-active-class="transition ease-in duration-75"
              leave-from-class="transform opacity-100 scale-100"
              leave-to-class="transform opacity-0 scale-95"
            >
              <MenuItems
                class="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50 py-1"
              >
                <MenuItem v-slot="{ active }">
                  <RouterLink
                    to="/profile"
                    :class="[active ? 'bg-gray-50' : '', 'flex items-center gap-2 px-4 py-2 text-sm text-gray-700']"
                  >
                    <UserCircleIcon class="w-4 h-4" />
                    Profile
                  </RouterLink>
                </MenuItem>
                <MenuItem v-slot="{ active }">
                  <button
                    :class="[active ? 'bg-gray-50' : '', 'w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600']"
                    @click="handleLogout"
                  >
                    <ArrowRightOnRectangleIcon class="w-4 h-4" />
                    Sign out
                  </button>
                </MenuItem>
              </MenuItems>
            </Transition>
          </Menu>
        </div>

        <!-- Mobile hamburger -->
        <button
          class="md:hidden p-2 rounded-lg text-blue-200 hover:text-white hover:bg-blue-600 transition-colors"
          @click="mobileOpen = !mobileOpen"
        >
          <Bars3Icon v-if="!mobileOpen" class="w-6 h-6" />
          <XMarkIcon v-else class="w-6 h-6" />
        </button>
      </div>
    </div>

    <!-- Mobile menu -->
    <div v-if="mobileOpen" class="md:hidden border-t border-blue-600 bg-blue-700 pb-3">
      <div class="px-4 pt-3 space-y-1">
        <template v-if="auth.isApplicant">
          <MobileLink to="/applications" @click="mobileOpen = false">My Applications</MobileLink>
        </template>
        <template v-if="auth.isStaff">
          <MobileLink to="/staff/dashboard" @click="mobileOpen = false">Dashboard</MobileLink>
          <MobileLink to="/staff/applications" @click="mobileOpen = false">Applications</MobileLink>
        </template>
        <template v-if="auth.isChairman">
          <MobileLink to="/admin/staff" @click="mobileOpen = false">Staff</MobileLink>
          <MobileLink to="/admin/street-types" @click="mobileOpen = false">Street Types</MobileLink>
        </template>
        <template v-if="auth.isChairman || auth.isFinance">
          <MobileLink to="/admin/fees" @click="mobileOpen = false">Fee Config</MobileLink>
        </template>
        <MobileLink to="/notifications" @click="mobileOpen = false">
          Notifications
          <span v-if="notificationStore.unreadCount > 0" class="ml-1 bg-red-500 text-white text-xs rounded-full px-1.5">
            {{ notificationStore.unreadCount }}
          </span>
        </MobileLink>
        <MobileLink to="/profile" @click="mobileOpen = false">Profile</MobileLink>
        <button
          class="w-full text-left px-3 py-2 text-sm text-red-300 hover:bg-blue-600 rounded-lg"
          @click="handleLogout"
        >
          Sign out
        </button>
      </div>
    </div>
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

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(() => {
  notificationStore.fetchUnreadCount()
})
</script>

<script lang="ts">
// Sub-components defined inline for simplicity
import { defineComponent, h } from 'vue'
import { RouterLink as RL } from 'vue-router'

export const NavLink = defineComponent({
  props: { to: String },
  setup(props, { slots }) {
    return () =>
      h(
        RL,
        {
          to: props.to!,
          class:
            'px-3 py-2 rounded-lg text-sm font-medium text-blue-100 hover:text-white hover:bg-blue-600 transition-colors',
          activeClass: 'bg-blue-800 text-white',
        },
        slots.default,
      )
  },
})

export const MobileLink = defineComponent({
  props: { to: String },
  emits: ['click'],
  setup(props, { slots, emit }) {
    return () =>
      h(
        RL,
        {
          to: props.to!,
          class:
            'block px-3 py-2 rounded-lg text-sm font-medium text-blue-100 hover:text-white hover:bg-blue-600 transition-colors',
          activeClass: 'bg-blue-800 text-white',
          onClick: () => emit('click'),
        },
        slots.default,
      )
  },
})
</script>
