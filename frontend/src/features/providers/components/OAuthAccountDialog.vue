<template>
  <Dialog
    :model-value="isOpen"
    title="添加账号"
    :icon="UserPlus"
    size="md"
    @update:model-value="handleDialogUpdate"
  >
    <!-- 鍙充笂瑙掍唬鐞嗘寜閽?-->
    <template #header-actions>
      <Popover
        :open="proxyPopoverOpen"
        @update:open="(v: boolean) => { proxyPopoverOpen = v; if (v) proxyNodesStore.ensureLoaded() }"
      >
        <PopoverTrigger as-child>
          <button
            class="flex items-center justify-center w-8 h-8 rounded-md transition-colors shrink-0"
            :class="selectedProxyNodeId
              ? 'text-blue-500 bg-blue-500/10 hover:bg-blue-500/20'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'"
            :title="selectedProxyNodeId ? `代理: ${getSelectedNodeLabel()}` : '设置代理节点'"
          >
            <Globe class="w-4 h-4" />
          </button>
        </PopoverTrigger>
        <PopoverContent
          class="w-72 p-3 z-[80]"
          side="bottom"
          align="end"
        >
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1.5">
                <span class="text-xs font-medium">代理节点</span>
                <span
                  v-if="!proxyNodesStore.loading && proxyNodesStore.onlineNodes.length === 0"
                  class="text-[10px] text-muted-foreground"
                >· 前往「模块管理 · 代理节点」添加</span>
              </div>
              <button
                v-if="selectedProxyNodeId"
                class="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                @click="selectedProxyNodeId = ''; proxyPopoverOpen = false"
              >
                清除
              </button>
            </div>
            <ProxyNodeSelect
              :model-value="selectedProxyNodeId"
              trigger-class="h-8"
              @update:model-value="(v: string) => { selectedProxyNodeId = v; proxyPopoverOpen = false }"
            />
            <p class="text-[10px] text-muted-foreground">
              {{ selectedProxyNodeId ? '授权、刷新、额度查询均走此代理' : '未设置，依次回退到提供商代理 -> 系统代理' }}
            </p>
          </div>
        </PopoverContent>
      </Popover>
    </template>

    <div class="space-y-4">
      <!-- Tab 鍒囨崲 -->
      <div class="flex rounded-lg border border-border p-0.5 bg-muted/30">
        <button
          class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-all"
          :class="[
            mode === 'oauth'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground',
          ]"
          @click="switchMode('oauth')"
        >
          {{ isKiroProvider ? '设备授权' : '获取授权' }}
        </button>
        <button
          class="flex-1 px-3 py-1.5 text-xs font-medium rounded-md transition-all"
          :class="mode === 'import'
            ? 'bg-background text-foreground shadow-sm'
            : 'text-muted-foreground hover:text-foreground'"
          @click="switchMode('import')"
        >
          导入授权
        </button>
      </div>

      <!-- Tab 鍐呭锛歡rid 鍙犳斁锛岄珮搴﹀彇杈冮珮鑰?-->
      <div class="grid [&>*]:col-start-1 [&>*]:row-start-1">
        <!-- ===== 鑾峰彇鎺堟潈 / 璁惧鎺堟潈 ===== -->
        <div
          class="space-y-4 transition-opacity duration-150"
          :class="mode === 'oauth' ? 'opacity-100' : 'opacity-0 pointer-events-none'"
        >
          <!-- Kiro: 璁惧鎺堟潈妯″紡 -->
          <template v-if="isKiroProvider">
            <!-- 鍒濆鐘舵€侊細閫夋嫨鎺堟潈绫诲瀷 + 寮€濮?-->
            <div
              v-if="!device.session_id && !device.starting"
              class="space-y-3"
            >
              <!-- Builder ID / Identity Center 鍒囨崲 -->
              <div class="grid grid-cols-2 gap-1.5">
                <button
                  v-for="opt in ([
                    { key: 'builder_id', label: 'Builder ID' },
                    { key: 'identity_center', label: 'Identity Center' },
                  ] as const)"
                  :key="opt.key"
                  class="h-8 text-xs font-medium rounded-md border transition-colors"
                  :class="device.auth_type === opt.key
                    ? 'border-primary bg-primary/5 text-foreground'
                    : 'border-border text-muted-foreground hover:text-foreground hover:border-foreground/20'"
                  @click="device.auth_type = opt.key"
                >
                  {{ opt.label }}
                </button>
              </div>

              <!-- grid 鍙犳斁淇濇寔楂樺害绋冲畾 -->
              <div class="grid [&>*]:col-start-1 [&>*]:row-start-1">
                <!-- Builder ID: 璇存槑鏂囧瓧 -->
                <div
                  class="flex items-center justify-center transition-opacity duration-150"
                  :class="device.auth_type === 'builder_id' ? 'opacity-100' : 'opacity-0 pointer-events-none'"
                >
                  <p class="text-xs text-muted-foreground">
                    浣跨敤涓汉 AWS Builder ID 杩涜璁惧鎺堟潈锛屾棤闇€棰濆閰嶇疆銆?                  </p>
                </div>

                <!-- Identity Center: Start URL + Region -->
                <div
                  class="space-y-3 transition-opacity duration-150"
                  :class="device.auth_type === 'identity_center' ? 'opacity-100' : 'opacity-0 pointer-events-none'"
                >
                  <div class="space-y-1.5">
                    <label class="text-xs font-medium">Start URL</label>
                    <input
                      v-model="device.start_url"
                      type="text"
                      placeholder="https://your-org.awsapps.com/start"
                      class="w-full h-8 px-2 text-xs rounded-md border border-border bg-background font-mono"
                      spellcheck="false"
                    >
                  </div>
                  <div class="space-y-1.5">
                    <label class="text-xs font-medium">Region</label>
                    <div class="grid grid-cols-2 gap-1.5">
                      <button
                        v-for="r in (['eu-north-1', 'us-east-1'] as const)"
                        :key="r"
                        class="h-8 text-xs font-medium font-mono rounded-md border transition-colors"
                        :class="device.region === r
                          ? 'border-primary bg-primary/5 text-foreground'
                          : 'border-border text-muted-foreground hover:text-foreground hover:border-foreground/20'"
                        @click="device.region = r"
                      >
                        {{ r }}
                      </button>
                    </div>
                  </div>
                  <div class="space-y-1.5">
                    <label class="text-xs font-medium text-muted-foreground">TOTP Secret (鍙€?</label>
                    <input
                      v-model="device.totp_secret"
                      type="text"
                      placeholder="Base32 secret, 濡?JBSWY3DPEHPK3PXP"
                      class="w-full h-8 px-2 text-xs rounded-md border border-border bg-background font-mono"
                      spellcheck="false"
                    >
                  </div>
                </div>
              </div>

              <Button
                class="w-full"
                :disabled="device.auth_type === 'identity_center' && !device.start_url.trim()"
                @click="startDeviceAuth"
              >
                寮€濮嬫巿鏉?              </Button>
            </div>

            <!-- 鍙戣捣涓?-->
            <div
              v-else-if="device.starting"
              class="flex items-center justify-center py-12"
            >
              <div class="text-center">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto mb-3" />
                <p class="text-xs text-muted-foreground">
                  姝ｅ湪娉ㄥ唽璁惧...
                </p>
              </div>
            </div>

            <!-- 绛夊緟鐢ㄦ埛鎺堟潈 -->
            <template v-else-if="device.session_id && device.status === 'pending'">
              <div class="rounded-xl border border-border bg-muted/20 p-5">
                <div class="flex flex-col items-center text-center space-y-4">
                  <!-- 鑴夊啿鍔ㄧ敾鍥炬爣 -->
                  <div class="relative">
                    <div class="absolute inset-0 rounded-full bg-primary/20 animate-ping" />
                    <div class="relative w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <ExternalLink class="w-5 h-5 text-primary" />
                    </div>
                  </div>

                  <!-- 鎻愮ず鏂囧瓧 -->
                  <div class="space-y-1">
                    <p class="text-sm font-medium">
                      鍦ㄦ祻瑙堝櫒涓畬鎴愭巿鏉?                    </p>
                    <p class="text-xs text-muted-foreground">
                      鎺堟潈瀹屾垚鍚庢椤甸潰灏嗚嚜鍔ㄦ洿鏂?                    </p>
                  </div>

                  <!-- 鍊掕鏃?-->
                  <div class="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <div class="animate-spin rounded-full h-3 w-3 border-[1.5px] border-primary/30 border-t-primary" />
                    <span>鍓╀綑 {{ deviceCountdownFormatted }}</span>
                  </div>

                  <!-- TOTP 楠岃瘉鐮?-->
                  <div
                    v-if="totp.code.value"
                    class="w-full rounded-lg border border-border bg-background p-3"
                  >
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <ShieldCheck class="w-3.5 h-3.5 text-primary" />
                        <span class="text-[10px] text-muted-foreground">MFA 楠岃瘉鐮?/span>
                      </div>
                      <div class="flex items-center gap-1.5">
                        <span
                          class="text-lg font-mono font-bold tracking-[0.25em]"
                        >{{ totp.code.value }}</span>
                        <button
                          class="p-1 rounded hover:bg-muted transition-colors"
                          title="澶嶅埗楠岃瘉鐮?
                          @click="copyToClipboard(totp.code.value)"
                        >
                          <Copy class="w-3 h-3 text-muted-foreground" />
                        </button>
                      </div>
                    </div>
                    <div class="mt-2 flex items-center gap-2">
                      <div class="flex-1 h-1 rounded-full bg-muted overflow-hidden">
                        <div
                          class="h-full rounded-full transition-all duration-1000 ease-linear"
                          :class="totp.remaining.value <= 5 ? 'bg-red-500' : 'bg-primary'"
                          :style="{ width: `${(totp.remaining.value / 30) * 100}%` }"
                        />
                      </div>
                      <span
                        class="text-[10px] font-mono tabular-nums shrink-0"
                        :class="totp.remaining.value <= 5 ? 'text-red-500' : 'text-muted-foreground'"
                      >{{ totp.remaining.value }}s</span>
                    </div>
                  </div>

                  <!-- 鎿嶄綔鎸夐挳 -->
                  <div class="flex gap-2 w-full">
                    <Button
                      class="flex-1"
                      size="sm"
                      @click="openDeviceVerificationUrl"
                    >
                      <ExternalLink class="w-3.5 h-3.5 mr-1.5" />
                      鎵撳紑鎺堟潈椤甸潰
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      @click="copyToClipboard(device.verification_uri_complete)"
                    >
                      <Copy class="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              </div>
            </template>

            <!-- 閿欒/杩囨湡 -->
            <div
              v-else-if="device.status === 'error' || device.status === 'expired'"
            >
              <div class="rounded-xl border border-destructive/20 bg-destructive/5 p-5">
                <div class="flex flex-col items-center text-center space-y-3">
                  <div class="w-10 h-10 rounded-full bg-destructive/10 flex items-center justify-center">
                    <AlertCircle class="w-5 h-5 text-destructive" />
                  </div>
                  <div class="space-y-1">
                    <p class="text-sm font-medium text-destructive">
                      {{ device.status === 'expired' ? '鎺堟潈宸茶繃鏈? : '鎺堟潈澶辫触' }}
                    </p>
                    <p class="text-xs text-muted-foreground">
                      {{ device.error || '璇烽噸璇? }}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    @click="resetDevice"
                  >
                    閲嶆柊寮€濮?                  </Button>
                </div>
              </div>
            </div>
          </template>

          <!-- 闈?Kiro: 鍘熸湁 OAuth 娴佺▼ -->
          <template v-else>
            <div
              v-if="oauth.starting && !oauth.authorization_url"
              class="flex items-center justify-center py-12"
            >
              <div class="text-center">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto mb-3" />
                <p class="text-xs text-muted-foreground">
                  姝ｅ湪鍑嗗鎺堟潈...
                </p>
              </div>
            </div>

            <template v-else-if="oauth.authorization_url">
              <div class="space-y-2">
                <div class="flex items-center gap-2">
                  <span class="flex items-center justify-center w-4 h-4 rounded-full bg-primary/10 text-primary text-[10px] font-semibold shrink-0">1</span>
                  <span class="text-xs font-medium">鍓嶅線鎺堟潈</span>
                </div>
                <div class="flex gap-2 pl-6">
                  <Button
                    size="sm"
                    :disabled="oauthBusy"
                    @click="openAuthorizationUrl"
                  >
                    <ExternalLink class="w-3 h-3 mr-1" />
                    鎵撳紑
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    :disabled="oauthBusy"
                    @click="copyToClipboard(oauth.authorization_url)"
                  >
                    <Copy class="w-3 h-3 mr-1" />
                    澶嶅埗
                  </Button>
                </div>
              </div>

              <div class="space-y-2">
                <div class="flex items-center gap-2">
                  <span class="flex items-center justify-center w-4 h-4 rounded-full bg-primary/10 text-primary text-[10px] font-semibold shrink-0">2</span>
                  <span class="text-xs font-medium">绮樿创鍥炶皟 URL</span>
                </div>
                <div class="pl-6">
                  <Textarea
                    v-model="oauth.callback_url"
                    :disabled="oauthBusy"
                    placeholder="http://localhost:xxx/callback?code=..."
                    class="min-h-[120px] text-xs font-mono break-all !rounded-xl"
                    spellcheck="false"
                  />
                </div>
              </div>
            </template>
          </template>
        </div>

        <!-- ===== 导入授权 ===== -->
        <div
          class="flex flex-col gap-3 transition-opacity duration-150"
          :class="mode === 'import' ? 'opacity-100' : 'opacity-0 pointer-events-none'"
        >
          <input
            ref="fileInputRef"
            type="file"
            accept=".json,.txt,application/json,text/plain"
            class="hidden"
            @change="handleFileSelect"
          >

          <!-- 涓诲尯鍩燂細鎷栨嫿 鎴?绮樿创杈撳叆妗嗭紙鍚屼竴浣嶇疆鍒囨崲锛?-->
          <div
            v-if="!importText"
            class="mt-3"
          >
            <!-- 鎷栨嫿妯″紡 -->
            <div
              v-if="!showManualInput"
              class="rounded-xl border-2 border-dashed transition-colors cursor-pointer"
              :class="isDragging
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-muted-foreground/40'"
              @click="fileInputRef?.click()"
              @dragover.prevent="isDragging = true"
              @dragleave.prevent="isDragging = false"
              @drop.prevent="handleFileDrop"
            >
              <div class="flex flex-col items-center justify-center py-10 gap-2">
                <div class="w-8 h-8 rounded-full bg-muted/60 flex items-center justify-center">
                  <Upload class="w-4 h-4 text-muted-foreground" />
                </div>
                <div class="text-center">
                  <p class="text-xs font-medium">
                    拖入授权文件或点击选择
                  </p>
                  <p class="text-[10px] text-muted-foreground mt-0.5">
                    支持 .json / .txt 格式
                  </p>
                </div>
              </div>
            </div>

            <!-- 绮樿创妯″紡 -->
            <Textarea
              v-else
              v-model="manualPasteText"
              :disabled="importing"
              placeholder="粘贴 Refresh Token 或 JSON 内容"
              class="min-h-[168px] text-xs font-mono break-all !rounded-xl"
              spellcheck="false"
            />
          </div>

          <!-- 搴曢儴鍒囨崲閾炬帴锛氬崰婊″墿浣欑┖闂村眳涓?-->
          <div
            v-if="!importText"
            class="flex-1 flex items-center justify-center"
          >
            <button
              v-if="!showManualInput"
              class="text-xs text-muted-foreground hover:text-foreground transition-colors"
              @click="showManualInput = true"
            >
              或手动粘贴 Refresh Token
            </button>
            <button
              v-else
              class="text-xs text-muted-foreground hover:text-foreground transition-colors"
              @click="showManualInput = false"
            >
              或选择 JSON / TXT 文件导入
            </button>
          </div>

          <!-- 宸叉湁鍐呭锛堟枃浠跺鍏ュ悗锛夛細鏄剧ず鏂囨湰妗?-->
          <div
            v-if="importText"
            class="space-y-2"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs text-muted-foreground">{{ importFileName || '已粘贴内容' }}</span>
              <button
                class="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                :disabled="importing"
                @click="clearImport"
              >
                清除
              </button>
            </div>
            <Textarea
              v-model="importText"
              :disabled="importing"
              class="min-h-[160px] text-xs font-mono break-all !rounded-xl"
              spellcheck="false"
            />
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <Button
        variant="outline"
        @click="handleClose"
      >
        取消
      </Button>
      <Button
        v-if="mode === 'oauth' && !isKiroProvider"
        :disabled="!canCompleteOAuth"
        @click="handleCompleteOAuth"
      >
        {{ oauth.completing ? '验证中...' : '验证' }}
      </Button>
      <Button
        v-if="mode === 'import'"
        :disabled="!canImport"
        @click="handleImport"
      >
        {{ importing ? '导入中...' : '导入' }}
      </Button>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { Dialog, Button, Textarea, Popover, PopoverTrigger, PopoverContent } from '@/components/ui'
import { UserPlus, Copy, ExternalLink, Upload, Globe, AlertCircle, ShieldCheck } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'
import { useClipboard } from '@/composables/useClipboard'
import { useTotp } from '@/composables/useTotp'
import { parseApiError } from '@/utils/errorParser'
import {
  startProviderLevelOAuth,
  completeProviderLevelOAuth,
  importProviderRefreshToken,
  batchImportOAuth,
  startDeviceAuthorize,
  pollDeviceAuthorize,
} from '@/api/endpoints'
import ProxyNodeSelect from './ProxyNodeSelect.vue'
import { useProxyNodesStore } from '@/stores/proxy-nodes'

const props = defineProps<{
  open: boolean
  providerId: string | null
  providerType: string | null
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

const { success, error: showError } = useToast()
const { copyToClipboard } = useClipboard()
const proxyNodesStore = useProxyNodesStore()
const totp = useTotp()

// 浠ｇ悊鑺傜偣閫夋嫨
const proxyPopoverOpen = ref(false)
const selectedProxyNodeId = ref('')

/** 鑾峰彇宸查€変唬鐞嗚妭鐐圭殑鏄剧ず鍚嶇О */
function getSelectedNodeLabel(): string {
  if (!selectedProxyNodeId.value) return ''
  const node = proxyNodesStore.nodes.find(n => n.id === selectedProxyNodeId.value)
  return node ? node.name : `${selectedProxyNodeId.value.slice(0, 8)  }...`
}

// 妯″紡
type DialogMode = 'oauth' | 'import'
const mode = ref<DialogMode>('oauth')

// OAuth 鐘舵€?interface OAuthState {
  authorization_url: string
  redirect_uri: string
  instructions: string
  provider_type: string
  callback_url: string
  starting: boolean
  completing: boolean
}

function createInitialOAuthState(): OAuthState {
  return {
    authorization_url: '',
    redirect_uri: '',
    instructions: '',
    provider_type: '',
    callback_url: '',
    starting: false,
    completing: false,
  }
}

const oauth = ref<OAuthState>(createInitialOAuthState())

// 璁惧鎺堟潈鐘舵€?type DeviceAuthType = 'builder_id' | 'identity_center'

interface DeviceAuthState {
  auth_type: DeviceAuthType
  start_url: string
  region: string
  totp_secret: string
  starting: boolean
  session_id: string
  user_code: string
  verification_uri: string
  verification_uri_complete: string
  expires_at: number  // unix timestamp (ms)
  interval: number    // 杞闂撮殧 (绉?
  status: 'idle' | 'pending' | 'authorized' | 'expired' | 'error'
  error: string
}

const BUILDER_ID_START_URL = 'https://view.awsapps.com/start'
const BUILDER_ID_REGION = 'us-east-1'

function createInitialDeviceState(): DeviceAuthState {
  return {
    auth_type: 'builder_id',
    start_url: '',
    region: 'eu-north-1',
    totp_secret: '',
    starting: false,
    session_id: '',
    user_code: '',
    verification_uri: '',
    verification_uri_complete: '',
    expires_at: 0,
    interval: 5,
    status: 'idle',
    error: '',
  }
}

const device = ref<DeviceAuthState>(createInitialDeviceState())
let devicePollTimer: ReturnType<typeof setTimeout> | null = null
const deviceCountdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null

// 瀵煎叆鐘舵€?const importText = ref('')
const importFileName = ref('')
const manualPasteText = ref('')
const importing = ref(false)
const isDragging = ref(false)
const showManualInput = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

const isOpen = computed(() => props.open)

const isKiroProvider = computed(() => (props.providerType || '').toLowerCase() === 'kiro')

const deviceCountdownFormatted = computed(() => {
  const s = deviceCountdown.value
  const min = Math.floor(s / 60)
  const sec = s % 60
  return `${min}:${String(sec).padStart(2, '0')}`
})

const oauthBusy = computed(() =>
  oauth.value.starting || oauth.value.completing
)

const canCompleteOAuth = computed(() => {
  if (!oauth.value.authorization_url) return false
  if (!oauth.value.callback_url.trim()) return false
  return !oauthBusy.value
})

const canImport = computed(() => {
  const text = importText.value || manualPasteText.value
  return text.trim().length > 0 && !importing.value
})

function stopDevicePolling() {
  if (devicePollTimer) {
    clearTimeout(devicePollTimer)
    devicePollTimer = null
  }
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function resetDevice() {
  stopDevicePolling()
  totp.stop()
  const { auth_type, start_url, region, totp_secret } = device.value
  device.value = createInitialDeviceState()
  device.value.auth_type = auth_type
  device.value.start_url = start_url
  device.value.region = region
  device.value.totp_secret = totp_secret
}

function resetForm() {
  oauth.value = createInitialOAuthState()
  stopDevicePolling()
  totp.stop()
  device.value = createInitialDeviceState()
  importText.value = ''
  importFileName.value = ''
  manualPasteText.value = ''
  importing.value = false
  isDragging.value = false
  showManualInput.value = false
  proxyPopoverOpen.value = false
  selectedProxyNodeId.value = ''
  mode.value = 'oauth'
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function clearImport() {
  importText.value = ''
  importFileName.value = ''
  manualPasteText.value = ''
  showManualInput.value = false
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

function switchMode(newMode: DialogMode) {
  if (mode.value === newMode) return

  mode.value = newMode
  if (newMode === 'oauth' && !isKiroProvider.value && !oauth.value.authorization_url && !oauth.value.starting) {
    initOAuth()
  }
}

function handleDialogUpdate(value: boolean) {
  if (!value) {
    handleClose()
  }
}

function handleClose() {
  resetForm()
  emit('close')
}

function openAuthorizationUrl() {
  const url = oauth.value.authorization_url
  if (!url) return
  window.open(url, '_blank', 'noopener,noreferrer')
}

async function initOAuth() {
  if (!props.providerId) return
  if (isKiroProvider.value) return


  oauth.value.starting = true
  try {
    const resp = await startProviderLevelOAuth(props.providerId)
    oauth.value.authorization_url = resp.authorization_url
    oauth.value.redirect_uri = resp.redirect_uri
    oauth.value.instructions = resp.instructions
    oauth.value.provider_type = resp.provider_type
  } catch (err: unknown) {
    const errorMessage = parseApiError(err, '鍒濆鍖栨巿鏉冨け璐?)
    showError(errorMessage, '閿欒')
    mode.value = 'import'
  } finally {
    oauth.value.starting = false
  }
}

async function handleCompleteOAuth() {
  if (!canCompleteOAuth.value || !props.providerId) return
  oauth.value.completing = true
  try {
    await completeProviderLevelOAuth(props.providerId, {
      callback_url: oauth.value.callback_url.trim(),
      proxy_node_id: selectedProxyNodeId.value || undefined,
    })
    success('鎺堟潈鎴愬姛锛岃处鍙峰凡娣诲姞')
    emit('saved')
    handleClose()
  } catch (err: unknown) {
    const errorMessage = parseApiError(err, '瀹屾垚鎺堟潈澶辫触')
    showError(errorMessage, '閿欒')
  } finally {
    oauth.value.completing = false
  }
}

// 妫€娴嬫槸鍚︿负鎵归噺瀵煎叆鏍煎紡
function isBatchImport(text: string): boolean {
  const trimmed = text.trim()
  // JSON 鏁扮粍
  if (trimmed.startsWith('[')) {
    try {
      const parsed = JSON.parse(trimmed)
      return Array.isArray(parsed) && parsed.length > 0
    } catch {
      return false
    }
  }
  // 鍗曚釜 JSON 瀵硅薄锛堝彲鑳芥槸 pretty-printed 澶氳锛変笉绠楁壒閲忓鍏?  if (trimmed.startsWith('{')) {
    try {
      JSON.parse(trimmed)
      return false // 鍙В鏋愮殑鍗曚釜 JSON 瀵硅薄锛岃蛋鍗曟潯瀵煎叆
    } catch {
      // 瑙ｆ瀽澶辫触锛氬彲鑳芥槸澶氫釜 JSON 瀵硅薄锛圝SON Lines 鏍煎紡锛夛紝缁х画妫€鏌?    }
  }
  // 澶氳鏂囨湰锛堢函 Token 涓€琛屼竴涓級
  const lines = trimmed.split('\n').filter(line => line.trim() && !line.trim().startsWith('#'))
  return lines.length > 1
}

function extractRefreshTokenFromObject(obj: Record<string, unknown>): string | null {
  const directToken = (typeof obj.refresh_token === 'string' && obj.refresh_token.trim())
    ? obj.refresh_token.trim()
    : (typeof obj.refreshToken === 'string' && obj.refreshToken.trim())
      ? obj.refreshToken.trim()
      : ''
  if (directToken) return directToken

  const nested = obj.auth_config ?? obj.authConfig
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
    const nestedObj = nested as Record<string, unknown>
    const nestedToken = (typeof nestedObj.refresh_token === 'string' && nestedObj.refresh_token.trim())
      ? nestedObj.refresh_token.trim()
      : (typeof nestedObj.refreshToken === 'string' && nestedObj.refreshToken.trim())
        ? nestedObj.refreshToken.trim()
        : ''
    if (nestedToken) return nestedToken
  }

  return null
}

function parseImportText(text: string): { refresh_token: string; name?: string } | null {
  const trimmed = text.trim()
  if (!trimmed) return null

  // Kiro: keep full JSON so backend can extract auth_method/region/client_id, etc.
  if (isKiroProvider.value) {
    return { refresh_token: trimmed }
  }

  try {
    const parsed: unknown = JSON.parse(trimmed)
    if (typeof parsed === 'object' && parsed !== null && !Array.isArray(parsed)) {
      const obj = parsed as Record<string, unknown>
      const refreshToken = extractRefreshTokenFromObject(obj)
      if (refreshToken) {
        return {
          refresh_token: refreshToken,
          name: (typeof obj.name === 'string' ? obj.name : undefined)
            || (typeof obj.oauth_email === 'string' ? obj.oauth_email : undefined)
            || (typeof obj.email === 'string' ? obj.email : undefined),
        }
      }
      return null
    }
  } catch {
    // Not JSON: treat as raw token.
  }

  return { refresh_token: trimmed }
}

function readFile(file: File) {
  if (!file.name.endsWith('.json') && !file.name.endsWith('.txt') && file.type !== 'application/json' && file.type !== 'text/plain') {
    showError('仅支持 .json 或 .txt 文件', '格式错误')
    return
  }
  importFileName.value = file.name
  const reader = new FileReader()
  reader.onload = (e) => {
    const content = e.target?.result
    if (typeof content === 'string') {
      importText.value = content
    }
  }
  reader.readAsText(file)
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) readFile(file)
}

function handleFileDrop(event: DragEvent) {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) readFile(file)
}

async function handleImport() {
  if (!canImport.value || !props.providerId) return

  const inputText = (importText.value || manualPasteText.value).trim()
  if (!inputText) {
    showError('请输入凭据数据', '格式错误')
    return
  }

  importing.value = true
  try {
    const proxyNodeId = selectedProxyNodeId.value || undefined
    if (isBatchImport(inputText)) {
      const result = await batchImportOAuth(props.providerId, inputText, proxyNodeId)
      if (result.success > 0) {
        if (result.failed > 0) {
          success(`批量导入完成：成功 ${result.success} 个，失败 ${result.failed} 个`)
        } else {
          success(`批量导入成功：${result.success} 个账号已添加`)
        }
        emit('saved')
        handleClose()
      } else {
        const firstError = result.results.find(r => r.status === 'error')
        showError(firstError?.error || '批量导入失败', '导入失败')
      }
    } else {
      const parsed = parseImportText(inputText)
      if (!parsed) {
        showError('无法解析输入内容，请检查格式', '格式错误')
        return
      }
      await importProviderRefreshToken(props.providerId, {
        ...parsed,
        proxy_node_id: proxyNodeId,
      })
      success('导入成功，账号已添加')
      emit('saved')
      handleClose()
    }
  } catch (err: unknown) {
    const errorMessage = parseApiError(err, '导入失败')
    showError(errorMessage, '错误')
  } finally {
    importing.value = false
  }
}
// ==== 璁惧鎺堟潈 ====

function openDeviceVerificationUrl() {
  const url = device.value.verification_uri_complete || device.value.verification_uri
  if (url) window.open(url, '_blank', 'noopener,noreferrer')
}

function startCountdown() {
  if (countdownTimer) clearInterval(countdownTimer)
  deviceCountdown.value = Math.max(0, Math.round((device.value.expires_at - Date.now()) / 1000))
  countdownTimer = setInterval(() => {
    deviceCountdown.value = Math.max(0, Math.round((device.value.expires_at - Date.now()) / 1000))
    if (deviceCountdown.value <= 0 && countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

async function startDeviceAuth() {
  if (!props.providerId) return
  device.value.starting = true
  device.value.error = ''
  try {
    const isBuilderID = device.value.auth_type === 'builder_id'
    const resp = await startDeviceAuthorize(props.providerId, {
      start_url: isBuilderID ? BUILDER_ID_START_URL : (device.value.start_url.trim() || undefined),
      region: isBuilderID ? BUILDER_ID_REGION : (device.value.region.trim() || undefined),
      proxy_node_id: selectedProxyNodeId.value || undefined,
    })
    device.value.session_id = resp.session_id
    device.value.user_code = resp.user_code
    device.value.verification_uri = resp.verification_uri
    device.value.verification_uri_complete = resp.verification_uri_complete
    device.value.expires_at = Date.now() + resp.expires_in * 1000
    device.value.interval = resp.interval || 5
    device.value.status = 'pending'
    startCountdown()
    scheduleDevicePoll()
    // 濡傛灉閰嶇疆浜?TOTP secret锛屽惎鍔ㄩ獙璇佺爜鐢熸垚
    if (device.value.totp_secret.trim()) {
      totp.start(device.value.totp_secret.trim())
    }
  } catch (err: unknown) {
    const errorMessage = parseApiError(err, '鍙戣捣璁惧鎺堟潈澶辫触')
    showError(errorMessage, '閿欒')
    device.value.status = 'error'
    device.value.error = errorMessage
  } finally {
    device.value.starting = false
  }
}

function scheduleDevicePoll() {
  if (devicePollTimer) clearTimeout(devicePollTimer)
  devicePollTimer = setTimeout(() => pollDevice(), device.value.interval * 1000)
}

async function pollDevice() {
  if (!props.providerId || !device.value.session_id || device.value.status !== 'pending') return

  try {
    const result = await pollDeviceAuthorize(props.providerId, {
      session_id: device.value.session_id,
    })

    switch (result.status) {
      case 'authorized':
        stopDevicePolling()
        totp.stop()
        device.value.status = 'authorized'
        success(result.email ? `鎺堟潈鎴愬姛: ${result.email}` : '鎺堟潈鎴愬姛锛岃处鍙峰凡娣诲姞')
        emit('saved')
        handleClose()
        return
      case 'pending':
        scheduleDevicePoll()
        return
      case 'slow_down':
        device.value.interval = Math.min(device.value.interval + 5, 30)
        scheduleDevicePoll()
        return
      case 'expired':
        stopDevicePolling()
        device.value.status = 'expired'
        device.value.error = result.error || '璁惧鐮佸凡杩囨湡'
        return
      case 'error':
        stopDevicePolling()
        device.value.status = 'error'
        device.value.error = result.error || '鎺堟潈澶辫触'
        return
    }
  } catch {
    // 缃戠粶閿欒绛夛紝缁х画杞
    scheduleDevicePoll()
  }
}

onBeforeUnmount(() => {
  stopDevicePolling()
})

watch(() => props.open, (newOpen) => {
  if (newOpen) {
    proxyNodesStore.ensureLoaded()
    if (!isKiroProvider.value) {
      initOAuth()
    }
  } else {
    resetForm()
  }
})
</script>
