<template>
  <div class="min-h-screen" style="background:#f1f5f9">
    <div style="background:#0f172a">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <p class="text-emerald-400 text-xs font-bold tracking-widest uppercase mb-1.5">Street Naming Committee</p>
        <h1 class="text-white text-2xl font-bold tracking-tight">Committee Review Console</h1>
        <p class="text-slate-400 text-sm mt-1">Sign in as your committee member to review and comment.</p>
      </div>
    </div>

    <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <!-- Second-tier member sign-in -->
      <div v-if="!member" class="rounded-2xl bg-white border border-slate-200 p-6 max-w-md">
        <p class="text-sm font-bold text-slate-900 mb-3">Verify as a committee member</p>
        <label class="block text-xs font-semibold text-slate-600 mb-1">Member</label>
        <select v-model="selNumber" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm mb-3">
          <option :value="0" disabled>Select member…</option>
          <option v-for="m in members" :key="m.number" :value="m.number">
            Member {{ m.number }} — {{ m.name }}{{ m.is_chairman ? ' (Chairman)' : '' }}
          </option>
        </select>
        <label class="block text-xs font-semibold text-slate-600 mb-1">PIN</label>
        <input v-model="pin" type="password" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm mb-3" placeholder="Your member PIN" />
        <p v-if="signinError" class="text-xs text-red-500 mb-2">{{ signinError }}</p>
        <button @click="signIn" :disabled="!selNumber || !pin || busy"
                class="w-full rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60" style="background:#059669">
          {{ busy ? 'Verifying…' : 'Verify' }}
        </button>
      </div>

      <template v-else>
        <div class="flex items-center justify-between rounded-xl bg-white border border-slate-200 px-4 py-3">
          <p class="text-sm text-slate-700">Signed in as <strong>Member {{ member.number }} — {{ member.name }}</strong>
            <span v-if="member.is_chairman" class="ml-2 text-[10px] font-semibold px-1.5 py-0.5 rounded" style="background:#dcfce7;color:#059669">Committee Chairman</span>
          </p>
          <div class="flex items-center gap-3">
            <RouterLink to="/admin/applications-database" class="text-xs font-semibold text-emerald-600 hover:text-emerald-700">Applications database →</RouterLink>
            <button @click="signOut" class="text-xs text-slate-500 hover:text-slate-700">Switch member</button>
          </div>
        </div>

        <!-- Applications under review -->
        <div v-if="!activeApp" class="rounded-2xl bg-white border border-slate-200">
          <div class="px-4 py-3 border-b border-slate-100"><p class="text-sm font-bold text-slate-900">Applications under committee review ({{ apps.length }})</p></div>
          <button v-for="a in apps" :key="a.id" @click="openApp(a)"
                  class="w-full text-left px-4 py-3 border-b border-slate-50 last:border-0 hover:bg-slate-50 flex items-center justify-between">
            <span><span class="font-medium text-slate-800">{{ a.proposed_street_name }}</span>
              <span class="text-xs text-slate-400 ml-2">{{ a.reference_number }}</span></span>
            <span class="text-xs text-emerald-600 font-semibold">Review →</span>
          </button>
          <p v-if="apps.length === 0" class="text-sm text-slate-400 text-center py-8">No applications awaiting committee review.</p>
        </div>

        <!-- Certificate issuance moved to the LG Chairman. The committee only
             reviews and forwards its recommendation. -->

        <!-- Review a single application -->
        <div v-else class="space-y-4">
          <button @click="activeApp = null; review = null" class="text-xs text-slate-500 hover:text-slate-700">← Back to list</button>
          <div class="rounded-2xl bg-white border border-slate-200 p-5">
            <p class="text-lg font-bold text-slate-900">{{ activeApp?.proposed_street_name }}</p>
            <p class="text-xs text-slate-400">{{ activeApp?.reference_number }} · {{ activeApp?.locality }}</p>

            <!-- Quorum bar -->
            <div v-if="review" class="mt-4 flex flex-wrap gap-2">
              <span v-for="m in review.members" :key="m.number"
                    class="text-[11px] px-2 py-1 rounded-full border"
                    :style="m.responded ? 'background:#dcfce7;border-color:#86efac;color:#059669' : 'background:#f8fafc;border-color:#e2e8f0;color:#94a3b8'">
                {{ m.number }}. {{ m.name.split(' ').slice(-1)[0] }}{{ m.is_chairman ? '★' : '' }} {{ m.responded ? '✓' : '' }}
              </span>
            </div>
            <p v-if="review" class="text-xs mt-2" :style="review.quorum_met ? 'color:#059669' : 'color:#b45309'">
              {{ review.quorum_met ? '✓ At least 3 members have commented — the chairman can now compile the overall position.' : `Needs 3 committee members to comment (${review.others_responded || 0} so far).` }}
            </p>
          </div>

          <!-- Applicant submissions — must be reviewed before commenting (#11) -->
          <div class="rounded-2xl bg-white border border-slate-200 p-5">
            <p class="text-sm font-bold text-slate-900 mb-3">Applicant submission</p>

            <!-- Application details the committee reviews -->
            <div v-if="appDetail" class="grid grid-cols-2 gap-x-4 gap-y-2 mb-4 text-sm">
              <div><span class="text-xs text-slate-400 block">Proposed name</span><span class="text-slate-800 font-medium">{{ appDetail.proposed_street_name }}</span></div>
              <div><span class="text-xs text-slate-400 block">Street type</span><span class="text-slate-800">{{ appDetail.street_type_name || '—' }}</span></div>
              <div><span class="text-xs text-slate-400 block">Ward</span><span class="text-slate-800">{{ appDetail.ward_display || appDetail.ward || '—' }}</span></div>
              <div><span class="text-xs text-slate-400 block">Locality</span><span class="text-slate-800">{{ appDetail.locality || '—' }}</span></div>
              <div class="col-span-2"><span class="text-xs text-slate-400 block">Location description</span><span class="text-slate-800">{{ appDetail.location_description || '—' }}</span></div>
              <div v-if="appDetail.is_legacy" class="col-span-2"><span class="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">Validation of an existing street</span></div>
            </div>

            <!-- Street location — shown to every committee member -->
            <div v-if="appDetail" class="mb-4">
              <p class="text-xs font-semibold text-slate-600 mb-1.5">Street location</p>
              <ApplicationMap
                :key="activeApp?.id"
                :location-description="appDetail.location_description"
                :street-name="appDetail.proposed_street_name"
                :proposed-street-name="appDetail.proposed_street_name"
                hide-other-buildings
                show-street-picture />
            </div>

            <p class="text-xs font-semibold text-slate-600 mb-1.5">Uploaded documents</p>
            <ul v-if="docs.length || review?.legacy_certificate" class="space-y-1.5 mb-3">
              <li v-for="d in docs" :key="d?.id" class="flex items-center justify-between text-sm">
                <span class="text-slate-600">{{ d.title || d.document_type_display || d.document_type }}</span>
                <a v-if="d.file_url || d.file" :href="d.file_url || d.file" target="_blank"
                   class="text-xs font-semibold text-emerald-600 hover:text-emerald-700">View</a>
              </li>
              <li v-if="review?.legacy_certificate" class="flex items-center justify-between text-sm">
                <span class="text-slate-600">{{ review?.is_legacy ? 'Existing document (for validation)' : 'Existing certificate' }}</span>
                <a :href="review.legacy_certificate" target="_blank"
                   class="text-xs font-semibold text-emerald-600 hover:text-emerald-700">View</a>
              </li>
            </ul>
            <p v-else class="text-xs text-slate-400 mb-3">No supporting documents were uploaded — review the application details and location above.</p>
            <button v-if="!review?.my_viewed" @click="markViewed"
                    class="rounded-lg px-3 py-2 text-xs font-semibold text-white" style="background:#0f172a">
              I have reviewed all submissions
            </button>
            <p v-else class="text-xs font-semibold text-emerald-600">✓ You have reviewed the submissions.</p>
          </div>

          <!-- Complete document repository — all records on file for this applicant -->
          <DocumentRepository v-if="activeApp" :application-id="activeApp.id" />

          <!-- My comment -->
          <div class="rounded-2xl bg-white border border-slate-200 p-5" :class="review?.my_viewed ? '' : 'opacity-50 pointer-events-none'">
            <p class="text-sm font-bold text-slate-900 mb-1">Your comment / recommendation to the Committee Chairman</p>
            <p class="text-xs text-slate-400 mb-3">Private — other members cannot see this. The Committee Chairman and the Local Government Chairman can.</p>
            <p v-if="!review?.my_viewed" class="text-xs text-amber-600 mb-2">Review the submissions above to unlock commenting.</p>
            <textarea v-model="myComment" rows="3" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm mb-2" placeholder="Your assessment of the proposed street name…"></textarea>
            <div class="flex flex-wrap gap-3 items-center">
              <select v-model="myRec" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                <option value="recommend">Recommend</option>
                <option value="not_recommend">Do not recommend</option>
                <option value="abstain">Abstain</option>
              </select>
              <input v-model="mySignature" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm flex-1 min-w-[160px]" placeholder="Sign (type your name)" />
              <button @click="saveComment" :disabled="!myComment || !mySignature || busy"
                      class="rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" style="background:#059669">Save my comment</button>
            </div>
            <p v-if="savedNote" class="text-xs text-emerald-600 mt-2">{{ savedNote }}</p>
          </div>

          <!-- Committee Chairman only: individual comments + overall position (#10b/#12) -->
          <div v-if="member.is_chairman && review" class="rounded-2xl bg-white border border-amber-200 p-5">
            <p class="text-sm font-bold text-slate-900 mb-3">Individual member comments ({{ (review.all_comments || []).length }})</p>
            <p class="text-xs text-slate-400 mb-2">Only you (Committee Chairman) and the Local Government Chairman see these.</p>
            <div v-for="cmt in review.all_comments" :key="cmt.member_number" class="border-b border-slate-50 py-2 last:border-0">
              <p class="text-xs font-semibold text-slate-700">Member {{ cmt.member_number }} ({{ cmt.member_name }}) — <span class="text-slate-500 font-normal">{{ cmt.recommendation }}</span></p>
              <p class="text-sm text-slate-600">{{ cmt.comment }}</p>
              <p class="text-[11px] text-slate-400 italic">— signed {{ cmt.signature }}</p>
            </div>

            <div v-if="review.decision_summary" class="mt-3 rounded-lg bg-slate-50 border border-slate-100 px-3 py-2 text-xs text-slate-600">
              <span class="font-semibold text-slate-700">Members' decisions:</span>
              {{ review.decision_summary.recommend }} recommend · {{ review.decision_summary.reject }} reject · {{ review.decision_summary.abstain }} abstain
              (of {{ review.decision_summary.total }}). This summary is forwarded to the LG Chairman with your decision.
            </div>

            <div class="mt-4 pt-4 border-t border-slate-100 space-y-2" :class="review.quorum_met ? '' : 'opacity-50 pointer-events-none'">
              <p class="text-sm font-bold text-slate-900">Overall committee position</p>
              <label class="block text-xs font-semibold text-slate-600">Recommendation to the Local Government Chairman
                <span class="font-normal text-slate-400">(seen by the LG Chairman and committee members)</span></label>
              <textarea v-model="overallRec" rows="2" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm" placeholder="Overall committee recommendation to the LG Chairman…"></textarea>
              <label class="block text-xs font-semibold text-slate-600">Comment to the applicant
                <span class="font-normal text-slate-400">(seen by the applicant, LG Chairman and committee members)</span></label>
              <textarea v-model="generalComment" rows="2" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm" placeholder="Comment to the applicant on behalf of the committee…"></textarea>
              <div class="flex gap-2 items-center">
                <select v-model="finalDecision" class="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  <option value="recommend">Recommend approval</option>
                  <option value="not_recommend">Reject</option>
                </select>
                <button @click="forward" :disabled="!review.quorum_met || busy"
                        class="rounded-lg px-4 py-2 text-sm font-semibold text-white disabled:opacity-60" style="background:#d97706">
                  {{ busy ? 'Forwarding…' : 'Forward to LG Chairman' }}
                </button>
              </div>
              <p v-if="!review.quorum_met" class="text-xs text-amber-600">Available once at least 3 members have commented.</p>
              <p v-if="forwardNote" class="text-xs text-emerald-600">{{ forwardNote }}</p>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { committeeApi, applicationApi, documentApi, configApi } from '@/services/api'
import ApplicationMap from '@/components/ApplicationMap.vue'
import DocumentRepository from '@/components/DocumentRepository.vue'

interface Member { number: number; name: string; is_chairman: boolean; responded?: boolean }
interface AppRow { id: string; proposed_street_name: string; reference_number: string; locality: string }
interface AppDetail { proposed_street_name: string; street_type_name?: string; ward?: string; ward_display?: string; locality?: string; location_description?: string; latitude?: number | string | null; longitude?: number | string | null; is_legacy?: boolean }
interface DocRow { id: string; document_type: string; document_type_display?: string; title?: string; file?: string; file_url?: string }
interface Review {
  members: Member[]; responded_count: number; others_responded: number; quorum_met: boolean; my_viewed: boolean
  is_legacy?: boolean; legacy_certificate?: string | null
  my_comment: { comment: string; signature: string; recommendation: string } | null
  all_comments: { member_number: number; member_name: string; comment: string; signature: string; recommendation: string }[] | null
  decision_summary?: { recommend: number; reject: number; abstain: number; total: number
    members: { member_number: number; member_name: string; recommendation: string }[] } | null
}

const members = ref<Member[]>([])
const selNumber = ref(0)
const pin = ref('')
const busy = ref(false)
const signinError = ref('')
const member = ref<Member | null>(null)
let token = ''

const apps = ref<AppRow[]>([])
const activeApp = ref<AppRow | null>(null)
const appDetail = ref<AppDetail | null>(null)
const docs = ref<DocRow[]>([])
const review = ref<Review | null>(null)



const myComment = ref(''); const mySignature = ref(''); const myRec = ref('recommend'); const savedNote = ref('')
const overallRec = ref(''); const generalComment = ref(''); const finalDecision = ref('recommend'); const forwardNote = ref('')

onMounted(async () => {
  try { members.value = (await committeeApi.members()).data } catch { /* not committee */ }
})

async function signIn() {
  busy.value = true; signinError.value = ''
  try {
    const { data } = await committeeApi.verifyMember(selNumber.value, pin.value)
    token = data.token; member.value = data.member
    await loadApps()
  } catch { signinError.value = 'Invalid member number or PIN.' }
  finally { busy.value = false }
}
function signOut() { member.value = null; token = ""; pin.value = ""; activeApp.value = null; review.value = null }

async function loadApps() {
  try {
    const { data } = await applicationApi.list({ status: 'under_naming_committee_review' })
    apps.value = (data.results ?? data) as AppRow[]
  } catch { apps.value = [] }
}

async function openApp(a: AppRow) {
  activeApp.value = a
  appDetail.value = null
  applicationApi.get(a.id).then(r => { appDetail.value = r.data as AppDetail }).catch(() => {})
  await Promise.all([loadReview(), loadDocs()])
  const mine = review.value?.my_comment
  if (mine) { myComment.value = mine.comment; mySignature.value = mine.signature; myRec.value = mine.recommendation }
  else { myComment.value = ''; mySignature.value = ''; myRec.value = 'recommend' }
}
async function loadDocs() {
  if (!activeApp.value) return
  try {
    // The endpoint answers with a paginated envelope, not a bare array. Assigning
    // the envelope made the list below iterate its VALUES — count, next, previous,
    // results — and reading .id off `next: null` threw inside the render function,
    // blanking the whole review panel. It only ever showed on validate
    // applications, because those are the only ones that render this list.
    const { data } = await documentApi.list(activeApp.value.id)
    docs.value = (Array.isArray(data) ? data : data.results ?? []) as DocRow[]
  } catch { docs.value = [] }
}
async function markViewed() {
  if (!activeApp.value) return
  try { await committeeApi.markViewed(activeApp.value.id, token); await loadReview() }
  catch { savedNote.value = 'Could not record your review — please sign in as a member again.' }
}
async function loadReview() {
  if (!activeApp.value) return
  review.value = (await committeeApi.review(activeApp.value.id, token)).data
}
async function saveComment() {
  if (!activeApp.value) return
  busy.value = true; savedNote.value = ''
  try {
    await committeeApi.comment(activeApp.value.id, token, { comment: myComment.value, signature: mySignature.value, recommendation: myRec.value })
    savedNote.value = 'Comment saved.'
    await loadReview()
  } finally { busy.value = false }
}
async function forward() {
  if (!activeApp.value) return
  busy.value = true; forwardNote.value = ''
  try {
    await committeeApi.forward(activeApp.value.id, token, {
      overall_recommendation: overallRec.value, general_comment_to_applicant: generalComment.value, decision: finalDecision.value,
    })
    forwardNote.value = 'Recommendation forwarded to the Local Government Chairman.'
    await loadApps()
    activeApp.value = null; review.value = null
  } catch { forwardNote.value = 'Could not forward — is quorum met?' }
  finally { busy.value = false }
}
</script>
