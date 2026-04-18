<template>
  <div class="min-h-screen" style="background: #f1f5f9">

    <div v-if="loading" class="flex flex-col items-center justify-center py-32 gap-3">
      <div class="w-10 h-10 rounded-full border-2 border-slate-200 border-t-emerald-500 animate-spin"></div>
      <p class="text-sm text-slate-500">Loading application…</p>
    </div>

    <template v-else-if="application">

      <!-- Header band -->
      <div style="background: #0a1628; border-bottom: 1px solid rgba(255,255,255,0.06)">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 py-5">
          <nav class="flex items-center gap-2 text-xs text-slate-400 mb-3">
            <RouterLink to="/staff/applications" class="hover:text-emerald-400 transition-colors">Applications</RouterLink>
            <ChevronRightIcon class="w-3.5 h-3.5 opacity-40" />
            <span class="text-slate-300 font-mono">{{ application.reference_number || `APP-${application.id}` }}</span>
          </nav>
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div class="flex items-center gap-3 flex-wrap">
                <h1 class="text-white text-xl font-bold tracking-tight">{{ application.proposed_street_name }}</h1>
                <StatusBadge :status="application.status" />
              </div>
              <p class="text-slate-400 text-sm mt-1">
                {{ application.street_type_name }} &nbsp;·&nbsp; {{ formatDate(application.created_at) }}
              </p>
            </div>
          </div>
          <!-- Alerts -->
          <div v-if="actionError" class="mt-4 flex items-start gap-3 rounded-xl border border-red-300/40 bg-red-500/10 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-red-300">{{ actionError }}</p>
          </div>
          <div v-if="actionSuccess" class="mt-4 flex items-start gap-3 rounded-xl border border-emerald-400/30 bg-emerald-500/10 p-3.5">
            <svg class="w-4 h-4 mt-0.5 flex-shrink-0 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd"/>
            </svg>
            <p class="text-sm text-emerald-300">{{ actionSuccess }}</p>
          </div>
        </div>
      </div>

      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">

          <!-- Left: applicant info + payment evidence + documents -->
          <div class="lg:col-span-2 space-y-4">

            <!-- Applicant info -->
            <div class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Applicant Information</h2>
              </div>
              <dl class="p-5 grid grid-cols-2 gap-5 text-sm">
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Full Name</dt>
                  <dd class="text-slate-900 font-semibold">{{ application.applicant?.full_name || '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Email</dt>
                  <dd class="text-slate-700">{{ application.applicant?.email || '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Phone</dt>
                  <dd class="text-slate-700">{{ application.applicant?.phone || '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Street Type</dt>
                  <dd class="text-slate-700">{{ application.street_type_name }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Ward</dt>
                  <dd class="text-slate-700">{{ application.ward_display || '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">LGA Area</dt>
                  <dd class="text-slate-700">{{ application.lga_area || '—' }}</dd>
                </div>
                <div class="col-span-2">
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Location Description</dt>
                  <dd class="text-slate-700 leading-relaxed whitespace-pre-line">{{ application.location_description }}</dd>
                </div>
              </dl>
            </div>

            <!-- Street Location Map — hidden for finance -->
            <div v-if="!auth.isFinance" class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4 flex items-center gap-2.5" style="border-bottom: 1px solid #f1f5f9">
                <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                     style="background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.15)">
                  <MapPinIcon class="w-4 h-4" style="color: #059669" />
                </div>
                <h2 class="text-sm font-bold text-slate-900">Street Location</h2>
              </div>
              <div class="p-4">
                <ApplicationMap
                  :location-description="application.location_description"
                  :street-name="application.proposed_street_name"
                  :proposed-street-name="application.proposed_street_name"
                />
              </div>
            </div>

            <!-- Payment Evidence — shown for finance and chairman only -->
            <div v-if="submittedPayment && !auth.isNamingCommittee" class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4 flex items-center gap-2.5" style="border-bottom: 1px solid #f1f5f9">
                <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                     style="background: rgba(2,132,199,0.08); border: 1px solid rgba(2,132,199,0.18)">
                  <BanknotesIcon class="w-4 h-4" style="color: #0284c7" />
                </div>
                <div>
                  <h2 class="text-sm font-bold text-slate-900">Payment Evidence</h2>
                  <p class="text-xs text-slate-500 mt-0">Submitted by applicant — awaiting your confirmation</p>
                </div>
                <span class="ml-auto text-xs font-bold px-2.5 py-1 rounded-full bg-blue-100 text-blue-700">Under Review</span>
              </div>
              <dl class="p-5 grid grid-cols-2 gap-5 text-sm">
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Payment Reference</dt>
                  <dd class="text-slate-900 font-mono font-semibold">{{ submittedPayment.payment_reference || '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Bank</dt>
                  <dd class="text-slate-700">{{ submittedPayment.bank_name || '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Payment Date</dt>
                  <dd class="text-slate-700">{{ submittedPayment.payment_date ? formatDate(submittedPayment.payment_date) : '—' }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Amount Submitted</dt>
                  <dd class="text-lg font-bold" style="color: #059669">₦{{ formatAmount(submittedPayment.amount_submitted) }}</dd>
                </div>
                <div v-if="submittedPayment.amount_expected">
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Amount Expected</dt>
                  <dd class="text-slate-700">₦{{ formatAmount(submittedPayment.amount_expected) }}</dd>
                </div>
                <div>
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Submitted On</dt>
                  <dd class="text-slate-700">{{ submittedPayment.submitted_at ? formatDate(submittedPayment.submitted_at) : '—' }}</dd>
                </div>
                <div v-if="submittedPayment.receipt_file" class="col-span-2">
                  <dt class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Receipt / Teller</dt>
                  <a :href="submittedPayment.receipt_file" target="_blank"
                     class="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-colors"
                     style="background: rgba(2,132,199,0.06); border: 1px solid rgba(2,132,199,0.2); color: #0284c7">
                    <DocumentIcon class="w-4 h-4" />
                    View Receipt / Teller
                  </a>
                </div>
              </dl>
            </div>

            <!-- All Payment Records — hidden from naming committee -->
            <div v-if="!auth.isNamingCommittee" class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Payment Records</h2>
              </div>
              <div v-if="!payments.length" class="flex flex-col items-center py-10 gap-2">
                <CurrencyDollarIcon class="w-8 h-8 text-slate-300" />
                <p class="text-sm text-slate-500">No payment records yet.</p>
              </div>
              <ul v-else class="divide-y divide-slate-50">
                <li v-for="p in payments" :key="p.id" class="px-5 py-4">
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center gap-2 flex-wrap">
                        <p class="text-sm font-semibold text-slate-900 font-mono">{{ p.payment_reference || 'No reference' }}</p>
                        <span class="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full"
                              :class="paymentStatusClass(p.status)">{{ p.status }}</span>
                      </div>
                      <p class="text-xs text-slate-500 mt-1">
                        <span v-if="p.bank_name">{{ p.bank_name }}</span>
                        <span v-if="p.payment_date"> · {{ formatDate(p.payment_date) }}</span>
                        <span v-if="p.amount_submitted" class="font-semibold text-slate-700"> · ₦{{ formatAmount(p.amount_submitted) }}</span>
                      </p>
                      <p v-if="p.finance_remarks" class="text-xs text-slate-600 mt-1 italic">"{{ p.finance_remarks }}"</p>
                    </div>
                    <a v-if="p.receipt_file" :href="p.receipt_file" target="_blank"
                       class="text-xs font-semibold text-blue-600 hover:text-blue-700 flex-shrink-0">Receipt</a>
                  </div>
                </li>
              </ul>
            </div>

            <!-- Documents — hidden for finance, only naming committee and chairman need them -->
            <div v-if="!auth.isFinance" class="rounded-2xl overflow-hidden" style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Uploaded Documents</h2>
              </div>
              <div v-if="!documents.length" class="flex flex-col items-center py-10 gap-2">
                <DocumentIcon class="w-8 h-8 text-slate-300" />
                <p class="text-sm text-slate-500">No documents uploaded.</p>
              </div>
              <ul v-else class="divide-y divide-slate-50">
                <li v-for="doc in documents" :key="doc.id" class="flex items-start gap-4 px-5 py-3.5">
                  <div class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
                       :style="doc.is_verified
                         ? 'background: rgba(5,150,105,0.08); border: 1px solid rgba(5,150,105,0.18)'
                         : doc.is_rejected
                           ? 'background: rgba(220,38,38,0.06); border: 1px solid rgba(220,38,38,0.18)'
                           : 'background: #f8fafc; border: 1px solid #e2e8f0'">
                    <DocumentIcon class="w-4 h-4"
                      :style="doc.is_verified ? 'color: #059669' : doc.is_rejected ? 'color: #dc2626' : 'color: #94a3b8'" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-slate-900 truncate">{{ doc.document_type_display || doc.document_type }}</p>
                    <p class="text-xs mt-0.5"
                       :class="doc.is_verified ? 'text-emerald-600' : doc.is_rejected ? 'text-red-500' : 'text-slate-400'">
                      {{ doc.is_verified ? '✓ Verified' : doc.is_rejected ? '✗ Rejected' : 'Pending verification' }}
                    </p>
                    <p v-if="doc.is_rejected && doc.verification_note" class="text-xs text-red-400 mt-0.5 italic leading-snug">
                      "{{ doc.verification_note }}"
                    </p>
                  </div>
                  <div class="flex items-center gap-3 flex-shrink-0 mt-0.5">
                    <a v-if="doc.file_url || doc.file" :href="doc.file_url || doc.file" target="_blank"
                       class="text-xs font-semibold text-emerald-600 hover:text-emerald-700">View</a>
                    <button v-if="!doc.is_verified && !doc.is_rejected && auth.isNamingCommittee"
                            class="text-xs font-semibold text-blue-600 hover:text-blue-700"
                            @click="verifyDoc(doc.id)">
                      Verify
                    </button>
                    <button v-if="!doc.is_rejected && auth.isNamingCommittee"
                            class="text-xs font-semibold text-red-500 hover:text-red-600"
                            @click="openRejectModal(doc)">
                      Reject
                    </button>
                  </div>
                </li>
              </ul>
            </div>

          </div>

          <!-- Right: action panels + history -->
          <div class="space-y-4">

            <!-- Finance: confirm payment evidence -->
            <div v-if="auth.isFinance && FINANCE_CONFIRM_STATUSES.includes(application.status)"
                 class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Confirm Payment</h2>
                <p class="text-xs text-slate-500 mt-0.5">Confirming will forward the application to the naming committee</p>
              </div>
              <form @submit.prevent="handleConfirmPayment" class="p-5 space-y-4" novalidate>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Decision <span class="text-red-500">*</span></label>
                  <select v-model="financeForm.decision" required
                          class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
                    <option value="">Select…</option>
                    <option value="confirmed">✓ Confirm Payment</option>
                    <option value="rejected">✗ Reject Payment</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Remarks
                    <span v-if="financeForm.decision === 'rejected'" class="text-red-500">*</span>
                    <span v-else class="text-slate-400 font-normal text-xs">(optional)</span>
                  </label>
                  <textarea v-model="financeForm.finance_remarks" rows="3"
                            :placeholder="financeForm.decision === 'rejected' ? 'Reason for rejection…' : 'Optional remarks…'"
                            class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"/>
                </div>
                <button type="submit"
                        :disabled="actionLoading || !financeForm.decision || (financeForm.decision === 'rejected' && !financeForm.finance_remarks)"
                        class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                        :style="financeForm.decision === 'rejected'
                          ? 'background: linear-gradient(135deg, #dc2626, #b91c1c)'
                          : 'background: linear-gradient(135deg, #059669, #047857)'">
                  {{ actionLoading ? 'Processing…' : (financeForm.decision === 'rejected' ? 'Reject Payment' : 'Confirm Payment') }}
                </button>
              </form>
            </div>

            <!-- Naming committee: issue certificate -->
            <div v-if="auth.isNamingCommittee && application.status === 'stage_c_confirmed'"
                 class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Issue Certificate</h2>
              </div>
              <div class="p-5 space-y-4">
                <p class="text-sm text-slate-600">Stage C payment confirmed. Upload the certificate and issue it to the applicant.</p>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Certificate File <span class="text-red-500">*</span></label>
                  <input type="file" accept=".pdf,.jpg,.jpeg,.png"
                         @change="onCertFileChange"
                         class="block w-full text-sm text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100" />
                </div>
                <button :disabled="actionLoading || !certFile"
                        class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                        style="background: linear-gradient(135deg, #059669, #047857)"
                        @click="handleIssueCertificate">
                  {{ actionLoading ? 'Processing…' : 'Issue Certificate' }}
                </button>
              </div>
            </div>

            <!-- Naming committee: completion status after certificate issued -->
            <div v-if="auth.isNamingCommittee && application.status === 'certificate_issued'"
                 class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Completion Status</h2>
                <p class="text-xs text-slate-500 mt-0.5">Checking these notifies the applicant.</p>
              </div>
              <div class="p-5 space-y-3">
                <label class="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" :checked="application.google_map_uploaded"
                         @change="handleCompletionToggle('google_map_uploaded', ($event.target as HTMLInputElement).checked)"
                         class="w-4 h-4 rounded accent-emerald-600" />
                  <span class="text-sm text-slate-700 font-medium">Google Map Uploaded</span>
                </label>
                <label class="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" :checked="application.signpost_installed"
                         @change="handleCompletionToggle('signpost_installed', ($event.target as HTMLInputElement).checked)"
                         class="w-4 h-4 rounded accent-emerald-600" />
                  <span class="text-sm text-slate-700 font-medium">Sign Post Installed</span>
                </label>
              </div>
            </div>

            <!-- Naming committee review -->
            <div v-if="auth.isNamingCommittee && application.status === 'under_naming_committee_review'"
                 class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Committee Review</h2>
              </div>
              <form @submit.prevent="handleCommitteeReview" class="p-5 space-y-4" novalidate>
                <!-- Warning when trying to approve with unverified docs -->
                <div v-if="committeeForm.decision === 'approved' && !allDocsVerified"
                     class="flex items-start gap-2.5 rounded-xl px-3.5 py-3"
                     style="background: rgba(234,179,8,0.06); border: 1px solid rgba(234,179,8,0.3)">
                  <svg class="w-4 h-4 mt-0.5 flex-shrink-0" style="color: #b45309" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
                  </svg>
                  <p class="text-xs text-amber-700">All documents must be verified before approving. Verify or reject each document above first.</p>
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Decision <span class="text-red-500">*</span></label>
                  <select v-model="committeeForm.decision" required
                          class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
                    <option value="">Select…</option>
                    <option value="approved">Approve</option>
                    <option value="rejected">Reject</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Remarks <span class="text-red-500">*</span></label>
                  <textarea v-model="committeeForm.remarks" rows="4" required placeholder="Provide your review remarks…"
                            class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"/>
                </div>
                <button type="submit"
                        :disabled="actionLoading || !committeeForm.decision || !committeeForm.remarks || (committeeForm.decision === 'approved' && !allDocsVerified)"
                        class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                        style="background: linear-gradient(135deg, #059669, #047857)">
                  {{ actionLoading ? 'Submitting…' : 'Submit Review' }}
                </button>
              </form>
            </div>

            <!-- Chairman approval -->
            <div v-if="auth.isChairman && application.status === 'awaiting_chairman_approval'"
                 class="rounded-2xl overflow-hidden"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Chairman Approval</h2>
              </div>
              <form @submit.prevent="handleChairmanApproval" class="p-5 space-y-4" novalidate>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Decision <span class="text-red-500">*</span></label>
                  <select v-model="chairmanForm.decision" required
                          class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
                    <option value="">Select…</option>
                    <option value="approved">Approve</option>
                    <option value="rejected">Reject</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-semibold text-slate-700 mb-1.5">Remarks</label>
                  <textarea v-model="chairmanForm.remarks" rows="4" placeholder="Optional remarks…"
                            class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"/>
                </div>
                <button type="submit" :disabled="actionLoading || !chairmanForm.decision"
                        class="w-full py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
                        style="background: linear-gradient(135deg, #059669, #047857)">
                  {{ actionLoading ? 'Submitting…' : 'Submit Decision' }}
                </button>
              </form>
            </div>

            <!-- Status timeline -->
            <div class="rounded-2xl overflow-hidden sticky top-4"
                 style="background: #fff; border: 1px solid #e2e8f0">
              <div class="px-5 py-4" style="border-bottom: 1px solid #f1f5f9">
                <h2 class="text-sm font-bold text-slate-900">Status History</h2>
              </div>
              <div v-if="!history.length" class="flex flex-col items-center py-10 gap-2">
                <ClockIcon class="w-8 h-8 text-slate-300" />
                <p class="text-xs text-slate-400">No history yet.</p>
              </div>
              <ol v-else class="p-5 space-y-4">
                <li v-for="(entry, i) in history" :key="i" class="flex gap-3">
                  <div class="flex flex-col items-center">
                    <div class="w-2.5 h-2.5 rounded-full flex-shrink-0 mt-1"
                         :style="i === 0 ? 'background: #059669' : 'background: #cbd5e1'"></div>
                    <div v-if="i < history.length - 1" class="w-px flex-1 mt-1" style="background: #e2e8f0; min-height: 20px"></div>
                  </div>
                  <div class="pb-2 min-w-0">
                    <StatusBadge :status="entry.new_status || entry.status || ''" />
                    <p class="text-xs text-slate-400 mt-1">{{ formatDate(entry.created_at || entry.timestamp || '') }}</p>
                    <p v-if="entry.remarks || entry.comment" class="text-xs text-slate-600 mt-1 italic leading-snug">
                      "{{ entry.remarks || entry.comment }}"
                    </p>
                  </div>
                </li>
              </ol>
            </div>

          </div>
        </div>
      </div>
    </template>

    <div v-else class="flex flex-col items-center justify-center py-32 gap-2">
      <p class="text-slate-500 text-sm">Application not found.</p>
      <RouterLink to="/staff/applications" class="text-xs font-semibold text-emerald-600">← Back to applications</RouterLink>
    </div>
  </div>

  <!-- Rejection modal -->
  <Teleport to="body">
    <div v-if="rejectModal.show"
         class="fixed inset-0 z-50 flex items-center justify-center px-4"
         style="background: rgba(0,0,0,0.5)">
      <div class="w-full max-w-md rounded-2xl overflow-hidden" style="background: #fff">
        <div class="px-6 py-5" style="border-bottom: 1px solid #f1f5f9">
          <h2 class="text-base font-bold text-slate-900">Reject Document</h2>
          <p class="text-sm text-slate-500 mt-1">
            Rejecting <span class="font-semibold text-slate-700">{{ rejectModal.docTypeName }}</span>
            will ask the applicant to re-upload this document.
          </p>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-semibold text-slate-700 mb-1.5">
              Reason for rejection <span class="text-red-500">*</span>
            </label>
            <textarea
              v-model="rejectModal.note"
              rows="4"
              :placeholder="`Explain why the ${rejectModal.docTypeName} was rejected…`"
              class="block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-red-400 focus:border-transparent"
            />
          </div>
          <div class="flex gap-3">
            <button
              class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all"
              style="background: #f1f5f9; color: #475569"
              @click="rejectModal.show = false"
            >
              Cancel
            </button>
            <button
              :disabled="actionLoading || !rejectModal.note.trim()"
              class="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-60"
              style="background: linear-gradient(135deg, #dc2626, #b91c1c)"
              @click="submitRejectDoc"
            >
              {{ actionLoading ? 'Rejecting…' : 'Reject Document' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { DocumentIcon, ChevronRightIcon, ClockIcon, CurrencyDollarIcon, BanknotesIcon, MapPinIcon } from '@heroicons/vue/24/outline'
import { applicationApi, documentApi, paymentApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'
import ApplicationMap from '@/components/ApplicationMap.vue'

interface Applicant { id: string; email: string; full_name: string; phone?: string }
interface Application {
  id: string
  reference_number?: string
  proposed_street_name: string
  street_type?: string
  street_type_name?: string
  ward_display?: string
  lga_area?: string
  location_description: string
  status: string
  created_at: string
  updated_at?: string
  applicant?: Applicant
  certificate_file?: string | null
  google_map_uploaded?: boolean
  signpost_installed?: boolean
}

interface Doc { id: string; document_type: string; document_type_display?: string; file?: string; file_url?: string; is_verified?: boolean; is_rejected?: boolean; verification_note?: string }
interface Payment {
  id: string
  payment_reference?: string
  bank_name?: string
  payment_date?: string
  submitted_at?: string
  status: string
  stage?: string
  amount_submitted?: number
  amount_expected?: number
  receipt_file?: string
  finance_remarks?: string
}
interface HistoryEntry { new_status?: string; status?: string; created_at?: string; timestamp?: string; remarks?: string; comment?: string }

// Finance sees action panel for these application statuses
const FINANCE_CONFIRM_STATUSES = [
  'awaiting_stage_a_payment_confirmation',
  'awaiting_stage_c_payment_confirmation',
  'awaiting_renewal_payment',
]

const route = useRoute()
const auth = useAuthStore()
const application = ref<Application | null>(null)
const documents = ref<Doc[]>([])
const payments = ref<Payment[]>([])
const history = ref<HistoryEntry[]>([])
const loading = ref(false)
const actionLoading = ref(false)
const actionError = ref('')
const actionSuccess = ref('')

const financeForm = ref({ decision: '', finance_remarks: '' })
const committeeForm = ref({ decision: '', remarks: '' })
const chairmanForm = ref({ decision: '', remarks: '' })
const certFile = ref<File | null>(null)

function onCertFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  certFile.value = input.files?.[0] ?? null
}

const rejectModal = ref<{ show: boolean; docId: string; docTypeName: string; note: string }>({
  show: false, docId: '', docTypeName: '', note: '',
})

// The payment the applicant has submitted evidence for (status = 'submitted')
const submittedPayment = computed(() =>
  payments.value.find(p => p.status === 'submitted') ?? null
)

const allDocsVerified = computed(() =>
  documents.value.length > 0 && documents.value.every(d => d.is_verified)
)

function formatDate(d: string) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('en-NG', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatAmount(n?: number | string) {
  if (!n) return '0.00'
  return new Intl.NumberFormat('en-NG', { minimumFractionDigits: 2 }).format(Number(n))
}

function paymentStatusClass(status: string) {
  const m: Record<string, string> = {
    pending: 'bg-amber-100 text-amber-700',
    submitted: 'bg-blue-100 text-blue-700',
    confirmed: 'bg-emerald-100 text-emerald-700',
    rejected: 'bg-red-100 text-red-700',
  }
  return m[status] ?? 'bg-slate-100 text-slate-600'
}

async function load() {
  loading.value = true
  try {
    const [appRes, docRes, payRes, histRes] = await Promise.all([
      applicationApi.get(route.params.id as string),
      documentApi.list(route.params.id as string).catch(() => ({ data: [] })),
      paymentApi.listForApplication(route.params.id as string).catch(() => ({ data: [] })),
      applicationApi.getHistory(route.params.id as string).catch(() => ({ data: [] })),
    ])
    application.value = appRes.data
    documents.value = Array.isArray(docRes.data) ? docRes.data : docRes.data.results ?? []
    payments.value = Array.isArray(payRes.data) ? payRes.data : payRes.data.results ?? []
    history.value = Array.isArray(histRes.data) ? histRes.data : histRes.data.results ?? []
  } finally {
    loading.value = false
  }
}

async function handleConfirmPayment() {
  actionError.value = ''
  actionSuccess.value = ''
  actionLoading.value = true
  try {
    // Look for the payment that has been submitted by the applicant
    const payment = payments.value.find(p => p.status === 'submitted')
    if (!payment) throw new Error('No submitted payment found. The applicant may not have provided payment evidence yet.')
    await paymentApi.confirmPayment(payment.id, {
      status: financeForm.value.decision,
      finance_remarks: financeForm.value.finance_remarks,
    })
    actionSuccess.value = financeForm.value.decision === 'confirmed'
      ? 'Payment confirmed. Application forwarded to naming committee.'
      : 'Payment rejected. Applicant has been notified.'
    financeForm.value = { decision: '', finance_remarks: '' }
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    actionError.value = e.response?.data?.detail || e.message || 'Failed.'
  } finally {
    actionLoading.value = false
  }
}

async function handleIssueCertificate() {
  if (!certFile.value) return
  actionError.value = ''
  actionLoading.value = true
  try {
    const formData = new FormData()
    formData.append('certificate_file', certFile.value)
    await applicationApi.issueCertificate(application.value!.id, formData)
    actionSuccess.value = 'Certificate issued and applicant notified.'
    certFile.value = null
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to issue certificate.'
  } finally {
    actionLoading.value = false
  }
}

async function handleCompletionToggle(field: 'google_map_uploaded' | 'signpost_installed', value: boolean) {
  actionError.value = ''
  try {
    await applicationApi.updateCompletion(application.value!.id, { [field]: value })
    actionSuccess.value = value
      ? (field === 'google_map_uploaded' ? 'Google Map marked as uploaded.' : 'Sign Post marked as installed.')
      : 'Status updated.'
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to update completion status.'
  }
}

async function handleCommitteeReview() {
  actionError.value = ''
  actionSuccess.value = ''
  actionLoading.value = true
  try {
    await applicationApi.committeeReview(application.value!.id, {
      decision: committeeForm.value.decision,
      remarks: committeeForm.value.remarks,
    })
    actionSuccess.value = 'Review submitted.'
    committeeForm.value = { decision: '', remarks: '' }
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to submit review.'
  } finally {
    actionLoading.value = false
  }
}

async function handleChairmanApproval() {
  actionError.value = ''
  actionSuccess.value = ''
  actionLoading.value = true
  try {
    await applicationApi.chairmanApproval(application.value!.id, {
      decision: chairmanForm.value.decision,
      remarks: chairmanForm.value.remarks,
    })
    actionSuccess.value = 'Decision recorded.'
    chairmanForm.value = { decision: '', remarks: '' }
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } }
    actionError.value = e.response?.data?.detail || 'Failed to submit decision.'
  } finally {
    actionLoading.value = false
  }
}

async function verifyDoc(docId: string) {
  try {
    await documentApi.verify(docId, { is_verified: true })
    actionSuccess.value = 'Document verified.'
    await load()
  } catch {
    actionError.value = 'Failed to verify document.'
  }
}

function openRejectModal(doc: Doc) {
  rejectModal.value = {
    show: true,
    docId: doc.id,
    docTypeName: doc.document_type_display || doc.document_type,
    note: '',
  }
}

async function submitRejectDoc() {
  if (!rejectModal.value.note.trim()) return
  actionError.value = ''
  actionLoading.value = true
  try {
    await documentApi.reject(rejectModal.value.docId, {
      rejection_note: rejectModal.value.note,
    })
    rejectModal.value = { show: false, docId: '', docTypeName: '', note: '' }
    actionSuccess.value = 'Document rejected. Applicant has been asked to re-upload.'
    await load()
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string; rejection_note?: string[] } } }
    actionError.value = e.response?.data?.detail || e.response?.data?.rejection_note?.[0] || 'Failed to reject document.'
  } finally {
    actionLoading.value = false
  }
}

onMounted(load)
</script>
