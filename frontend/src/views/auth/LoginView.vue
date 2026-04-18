<template>
  <div class="min-h-screen flex flex-col md:flex-row overflow-hidden">

    <!-- ═══════════════════════════════════════════════════════════════
         LEFT PANEL — Branding (desktop only, hidden on mobile)
    ═══════════════════════════════════════════════════════════════ -->
    <div class="hidden md:flex md:w-[58%] relative flex-col justify-between overflow-hidden">
      <!-- Base background -->
      <div class="absolute inset-0 bg-[#050f1e]"></div>

      <!-- Ambient glow — top left (emerald) -->
      <div
        class="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full pointer-events-none"
        style="background: radial-gradient(circle, rgba(5,150,105,0.28) 0%, transparent 70%)"
      ></div>
      <!-- Ambient glow — bottom right (gold) -->
      <div
        class="absolute -bottom-60 right-0 w-[700px] h-[700px] rounded-full pointer-events-none"
        style="background: radial-gradient(circle, rgba(217,119,6,0.18) 0%, transparent 65%)"
      ></div>

      <!-- Street grid SVG illustration — kept very subtle so text is dominant -->
      <svg
        class="absolute inset-0 w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="xMidYMid slice"
        viewBox="0 0 900 700"
      >
        <!-- Secondary streets -->
        <line x1="0" y1="80"  x2="900" y2="80"  stroke="#34d399" stroke-width="1" opacity="0.07"/>
        <line x1="0" y1="290" x2="900" y2="290" stroke="#34d399" stroke-width="1" opacity="0.07"/>
        <line x1="0" y1="450" x2="900" y2="450" stroke="#34d399" stroke-width="1" opacity="0.07"/>
        <line x1="0" y1="630" x2="900" y2="630" stroke="#34d399" stroke-width="1" opacity="0.07"/>
        <line x1="70"  y1="0" x2="70"  y2="700" stroke="#34d399" stroke-width="1" opacity="0.07"/>
        <line x1="300" y1="0" x2="300" y2="700" stroke="#34d399" stroke-width="1" opacity="0.07"/>
        <line x1="570" y1="0" x2="570" y2="700" stroke="#34d399" stroke-width="1" opacity="0.07"/>
        <line x1="820" y1="0" x2="820" y2="700" stroke="#34d399" stroke-width="1" opacity="0.07"/>
        <!-- Major roads -->
        <line x1="0" y1="180" x2="900" y2="180" stroke="#10b981" stroke-width="2.5" opacity="0.13"/>
        <line x1="0" y1="370" x2="900" y2="370" stroke="#10b981" stroke-width="3"   opacity="0.15"/>
        <line x1="0" y1="540" x2="900" y2="540" stroke="#10b981" stroke-width="2"   opacity="0.10"/>
        <line x1="180" y1="0" x2="180" y2="700" stroke="#10b981" stroke-width="2.5" opacity="0.13"/>
        <line x1="420" y1="0" x2="420" y2="700" stroke="#10b981" stroke-width="3"   opacity="0.15"/>
        <line x1="690" y1="0" x2="690" y2="700" stroke="#10b981" stroke-width="2"   opacity="0.10"/>
        <!-- City blocks -->
        <rect x="72"  y="82"  width="106" height="96"  fill="#059669" opacity="0.09" rx="2"/>
        <rect x="182" y="82"  width="116" height="96"  fill="#059669" opacity="0.05" rx="2"/>
        <rect x="302" y="82"  width="116" height="96"  fill="#059669" opacity="0.07" rx="2"/>
        <rect x="422" y="82"  width="146" height="96"  fill="#059669" opacity="0.04" rx="2"/>
        <rect x="72"  y="182" width="106" height="106" fill="#059669" opacity="0.06" rx="2"/>
        <rect x="302" y="182" width="116" height="106" fill="#059669" opacity="0.09" rx="2"/>
        <rect x="572" y="182" width="116" height="106" fill="#059669" opacity="0.06" rx="2"/>
        <rect x="72"  y="372" width="106" height="76"  fill="#059669" opacity="0.08" rx="2"/>
        <rect x="182" y="292" width="116" height="76"  fill="#059669" opacity="0.04" rx="2"/>
        <rect x="422" y="292" width="146" height="76"  fill="#059669" opacity="0.06" rx="2"/>
        <rect x="182" y="372" width="116" height="76"  fill="#059669" opacity="0.09" rx="2"/>
        <rect x="572" y="372" width="116" height="76"  fill="#059669" opacity="0.05" rx="2"/>
        <rect x="72"  y="452" width="106" height="86"  fill="#059669" opacity="0.04" rx="2"/>
        <rect x="302" y="452" width="116" height="86"  fill="#059669" opacity="0.07" rx="2"/>
        <rect x="692" y="452" width="126" height="86"  fill="#059669" opacity="0.06" rx="2"/>
        <!-- Gold accents -->
        <rect x="422" y="82"  width="146" height="96"  fill="#fbbf24" opacity="0.04" rx="2"/>
        <rect x="572" y="372" width="116" height="76"  fill="#fbbf24" opacity="0.04" rx="2"/>
        <rect x="692" y="452" width="126" height="86"  fill="#fbbf24" opacity="0.03" rx="2"/>
        <!-- Roundabout -->
        <circle cx="420" cy="370" r="22" fill="none" stroke="#fbbf24" stroke-width="2.5" opacity="0.20"/>
        <circle cx="420" cy="370" r="10" fill="#fbbf24" opacity="0.08"/>
        <circle cx="180" cy="180" r="16" fill="none" stroke="#34d399" stroke-width="2" opacity="0.15"/>
      </svg>

      <!-- Dark scrim — lifts text contrast above the illustration -->
      <div class="absolute inset-0 pointer-events-none" style="background: rgba(5,15,30,0.55)"></div>

      <!-- Thin gold left-edge accent -->
      <div
        class="absolute top-0 left-0 w-1 h-full pointer-events-none"
        style="background: linear-gradient(to bottom, transparent, rgba(251,191,36,0.65), transparent)"
      ></div>

      <!-- Branding content -->
      <div class="relative z-10 p-12 pt-14 flex flex-col h-full justify-between">

        <!-- Logo + wordmark -->
        <div>
          <div class="flex items-center gap-4 mb-12">
            <div class="flex-shrink-0">
              <img
                src="@/assets/logo.png"
                alt="Ibeju-Lekki LGA Seal"
                class="w-24 h-24 object-contain drop-shadow-xl"
              />
            </div>
            <div>
              <h1 class="text-white font-bold text-2xl tracking-wide leading-none">SNRMS</h1>
              <p class="text-emerald-400 text-xs font-medium tracking-widest uppercase mt-1">Official Portal</p>
            </div>
          </div>

          <!-- Hero headline -->
          <div class="max-w-sm">
            <h2 class="text-white text-4xl font-bold leading-tight tracking-tight">
              Street Names<br/>
              <span style="background: linear-gradient(90deg, #34d399, #fbbf24); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                Made Official.
              </span>
            </h2>
            <p class="text-slate-200 mt-5 text-base leading-relaxed">
              The authoritative platform for street naming registration,
              review, and certification across Ibeju-Lekki LGA.
            </p>
          </div>

          <!-- Feature list -->
          <div class="mt-10 space-y-5">
            <div v-for="item in features" :key="item.label" class="flex items-start gap-3.5">
              <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
                   :style="`background: ${item.bgColor}`">
                <svg class="w-4.5 h-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                     :style="`color: ${item.iconColor}; width:18px; height:18px;`">
                  <path :d="item.path"/>
                </svg>
              </div>
              <div>
                <p class="text-white text-sm font-semibold">{{ item.label }}</p>
                <p class="text-slate-300 text-xs mt-0.5 leading-snug">{{ item.desc }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Official seal footer -->
        <div class="border-t border-white/10 pt-6">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                 style="background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3)">
              <svg class="w-4 h-4 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
              </svg>
            </div>
            <div>
              <p class="text-slate-300 text-xs font-semibold">Ibeju-Lekki Local Government Area</p>
              <p class="text-slate-400 text-xs">Lagos State, Federal Republic of Nigeria</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════════
         RIGHT PANEL — Sign-in form
    ═══════════════════════════════════════════════════════════════ -->
    <div class="flex-1 flex flex-col relative overflow-hidden bg-[#050f1e] md:bg-white"
         style="min-height: 100dvh; min-height: 100vh">

      <!-- ── Mobile background ──────────────────────────────────── -->
      <div class="absolute inset-0 md:hidden"
           style="background: linear-gradient(160deg, #071628 0%, #0d2040 55%, #071020 100%)"></div>
      <div class="absolute inset-0 md:hidden pointer-events-none"
           style="background-image: repeating-linear-gradient(0deg, rgba(255,255,255,0.025) 0px, rgba(255,255,255,0.025) 1px, transparent 1px, transparent 64px), repeating-linear-gradient(90deg, rgba(255,255,255,0.025) 0px, rgba(255,255,255,0.025) 1px, transparent 1px, transparent 64px)">
      </div>
      <!-- rainbow strip — mobile only -->
      <div class="absolute top-0 left-0 right-0 h-[3px] md:hidden"
           style="background: linear-gradient(90deg, #059669, #10b981, #fbbf24)"></div>
      <!-- Desktop separator -->
      <div class="absolute top-0 left-0 bottom-0 w-px hidden md:block"
           style="background: linear-gradient(to bottom, transparent, #e2e8f0, transparent)"></div>

      <!-- ══════════════════════════════════════════════════════════
           MOBILE layout — two-zone flex column, fills exactly 100dvh
      ══════════════════════════════════════════════════════════ -->
      <div class="relative z-10 flex flex-col h-full md:hidden"
           style="min-height: 100dvh; min-height: 100vh">

        <!-- Zone 1: dark header — logo + wordmark -->
        <div class="flex-none flex flex-col items-center justify-center pt-10 pb-6 px-6">
          <img
            src="@/assets/logo.png"
            alt="Ibeju-Lekki LGA Seal"
            class="w-36 h-36 object-contain mx-auto"
            style="filter: drop-shadow(0 8px 24px rgba(0,0,0,0.55))"
          />
          <h1 class="text-white text-3xl font-bold tracking-wide mt-2 leading-none">SNRMS</h1>
          <p class="text-emerald-400 text-[11px] font-bold tracking-[0.2em] uppercase mt-1.5">Official Portal</p>
          <p class="text-slate-400 text-xs mt-2 text-center leading-relaxed">
            Street Names Registration &amp; Management<br/>Ibeju-Lekki Local Government Area
          </p>
        </div>

        <!-- Zone 2: white sheet — fills remaining height, rounded top corners -->
        <div class="flex-1 flex flex-col bg-white rounded-t-3xl px-6 pt-7 pb-6"
             style="box-shadow: 0 -8px 40px rgba(0,0,0,0.25)">

          <!-- Sheet handle indicator -->
          <div class="w-10 h-1 rounded-full bg-slate-200 mx-auto mb-5"></div>

          <h2 class="text-slate-900 text-xl font-bold tracking-tight">Sign in</h2>
          <p class="text-slate-500 text-sm mt-1 mb-5">Enter your credentials to continue</p>

          <!-- Error alert -->
          <transition enter-active-class="transition duration-200 ease-out"
                      enter-from-class="opacity-0 -translate-y-1"
                      enter-to-class="opacity-100 translate-y-0">
            <div v-if="errorMessage"
                 class="mb-4 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-3.5">
              <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
              </svg>
              <p class="text-sm text-red-700">{{ errorMessage }}</p>
            </div>
          </transition>

          <!-- Form -->
          <form @submit.prevent="handleLogin" class="space-y-4" novalidate>
            <div>
              <label for="email-m" class="block text-sm font-semibold text-slate-700 mb-1.5">Email address</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"/>
                  </svg>
                </div>
                <input id="email-m" v-model="form.email" type="email" autocomplete="email" required
                       placeholder="you@example.com"
                       class="block w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-4 py-3 text-sm text-slate-900 placeholder-slate-400 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white"/>
              </div>
            </div>
            <div>
              <label for="password-m" class="block text-sm font-semibold text-slate-700 mb-1.5">Password</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"/>
                  </svg>
                </div>
                <input id="password-m" v-model="form.password" :type="showPassword ? 'text' : 'password'"
                       autocomplete="current-password" required placeholder="••••••••"
                       class="block w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-12 py-3 text-sm text-slate-900 placeholder-slate-400 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white"/>
                <button type="button" @click="showPassword = !showPassword"
                        class="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 transition-colors">
                  <svg v-if="!showPassword" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="pt-1">
              <button type="submit" :disabled="loading || !form.email || !form.password"
                      class="w-full flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl text-sm font-semibold text-white tracking-wide transition-all duration-200 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed"
                      style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 20px rgba(5,150,105,0.35)">
                <svg v-if="loading" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <span>{{ loading ? 'Signing in…' : 'Sign in' }}</span>
                <svg v-if="!loading" class="w-4 h-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"/>
                </svg>
              </button>
            </div>
          </form>

          <!-- Divider + register -->
          <div class="my-4 flex items-center gap-4">
            <div class="flex-1 h-px bg-slate-200"></div>
            <span class="text-xs text-slate-400 font-medium">New to SNRMS?</span>
            <div class="flex-1 h-px bg-slate-200"></div>
          </div>
          <RouterLink to="/register"
                      class="flex items-center justify-center w-full py-3.5 rounded-xl text-sm font-semibold text-slate-700 border border-slate-200 hover:bg-slate-50 transition-all duration-200">
            Create an account
          </RouterLink>

          <!-- Footer -->
          <p class="mt-auto pt-5 text-center text-[11px] text-slate-400">
            © {{ new Date().getFullYear() }} Ibeju-Lekki Local Government Area
          </p>
        </div>
      </div>

      <!-- ══════════════════════════════════════════════════════════
           DESKTOP layout — hidden on mobile
      ══════════════════════════════════════════════════════════ -->
      <div class="hidden md:flex flex-1 flex-col items-center justify-center px-12 lg:px-16 py-12">
        <div class="w-full max-w-sm">
          <!-- Desktop heading -->
          <div class="mb-8">
            <p class="text-xs font-bold text-emerald-600 tracking-widest uppercase mb-2">
              Ibeju-Lekki LGA · Official Streets Portal
            </p>
            <h2 class="text-slate-900 text-3xl font-bold tracking-tight leading-tight">Welcome back</h2>
            <p class="text-slate-500 mt-2.5 text-sm leading-relaxed">
              Sign in to access the Street Names Registration &amp; Management System.
            </p>
          </div>

          <!-- Error alert -->
          <transition enter-active-class="transition duration-200 ease-out"
                      enter-from-class="opacity-0 -translate-y-1"
                      enter-to-class="opacity-100 translate-y-0">
            <div v-if="errorMessage"
                 class="mb-5 flex items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-4">
              <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
              </svg>
              <p class="text-sm text-red-700">{{ errorMessage }}</p>
            </div>
          </transition>

          <!-- Form -->
          <form @submit.prevent="handleLogin" class="space-y-5" novalidate>
            <div>
              <label for="email" class="block text-sm font-semibold text-slate-700 mb-1.5">Email address</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"/>
                  </svg>
                </div>
                <input id="email" v-model="form.email" type="email" autocomplete="email" required
                       placeholder="you@example.com"
                       class="block w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-4 py-3 text-sm text-slate-900 placeholder-slate-400 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white"/>
            </div>
            </div>
            <div>
              <label for="password" class="block text-sm font-semibold text-slate-700 mb-1.5">Password</label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"/>
                  </svg>
                </div>
                <input id="password" v-model="form.password" :type="showPassword ? 'text' : 'password'"
                       autocomplete="current-password" required placeholder="••••••••"
                       class="block w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-12 py-3 text-sm text-slate-900 placeholder-slate-400 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent focus:bg-white"/>
                <button type="button" @click="showPassword = !showPassword"
                        class="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 transition-colors">
                  <svg v-if="!showPassword" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="pt-1">
              <button type="submit" :disabled="loading || !form.email || !form.password"
                      class="w-full flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl text-sm font-semibold text-white tracking-wide transition-all duration-200 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed"
                      style="background: linear-gradient(135deg, #059669, #047857); box-shadow: 0 4px 20px rgba(5,150,105,0.35)">
                <svg v-if="loading" class="animate-spin w-4 h-4 opacity-80" viewBox="0 0 24 24" fill="none">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <span>{{ loading ? 'Signing in…' : 'Sign in' }}</span>
                <svg v-if="!loading" class="w-4 h-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"/>
                </svg>
              </button>
            </div>
          </form>

          <div class="my-6 flex items-center gap-4">
            <div class="flex-1 h-px bg-slate-200"></div>
            <span class="text-xs text-slate-400 font-medium">New to SNRMS?</span>
            <div class="flex-1 h-px bg-slate-200"></div>
          </div>
          <RouterLink to="/register"
                      class="flex items-center justify-center w-full py-3.5 rounded-xl text-sm font-semibold text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 transition-all duration-200">
            Create an account
          </RouterLink>
          <p class="mt-8 text-center text-xs text-slate-400">
            © {{ new Date().getFullYear() }} Ibeju-Lekki Local Government Area
          </p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getRoleDefault } from '@/router/index'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ email: '', password: '' })
const errorMessage = ref('')
const showPassword = ref(false)
const loading = ref(false)

const features = [
  {
    label: 'End-to-end Application Tracking',
    desc: 'Submit, monitor and manage street naming requests through every approval stage.',
    path: 'M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z',
    bgColor: 'rgba(5,150,105,0.18)',
    iconColor: '#34d399',
  },
  {
    label: 'Multi-level Review & Approval',
    desc: 'Structured committee review, chairman sign-off, and Finance confirmation in one place.',
    path: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z',
    bgColor: 'rgba(16,185,129,0.15)',
    iconColor: '#6ee7b7',
  },
  {
    label: 'Official Certificate Issuance',
    desc: 'Receive a certified street name registration recognised by the LGA.',
    path: 'M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75',
    bgColor: 'rgba(217,119,6,0.18)',
    iconColor: '#fbbf24',
  },
]

async function handleLogin() {
  errorMessage.value = ''
  loading.value = true
  try {
    await auth.login(form.value.email, form.value.password)
    const redirect =
      (router.currentRoute.value.query.redirect as string) ||
      getRoleDefault(auth.user?.role)
    router.push(redirect)
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string; non_field_errors?: string[] } } }
    errorMessage.value =
      e.response?.data?.detail ||
      e.response?.data?.non_field_errors?.[0] ||
      'Invalid email or password. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
