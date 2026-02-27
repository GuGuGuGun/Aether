<template>
  <CardSection
    title="网络代理"
    description="配置提供商出站请求的默认代理，仅影响大模型 API、余额查询、OAuth 等提供商请求"
  >
    <template #actions>
      <Button
        size="sm"
        :disabled="loading || !hasChanges"
        @click="$emit('save')"
      >
        {{ loading ? '保存中...' : '保存' }}
      </Button>
    </template>
    <div class="max-w-md space-y-4">
      <div class="rounded-lg border border-border/60 bg-muted/20 p-3">
        <div class="flex items-start justify-between gap-3">
          <div>
            <Label
              for="enable-proxy-auto-fetch"
              class="text-sm cursor-pointer"
            >
              启用代理自动爬取
            </Label>
            <p class="mt-1 text-xs text-muted-foreground">
              开启后才允许在代理节点页面执行“爬取”，并启用后台定时自动同步。
            </p>
          </div>
          <Switch
            id="enable-proxy-auto-fetch"
            :model-value="enableProxyAutoFetch"
            @update:model-value="$emit('update:enableProxyAutoFetch', $event)"
          />
        </div>
      </div>

      <Label class="block text-sm font-medium mb-1">
        默认代理节点
      </Label>
      <Select
        :model-value="proxyNodeId || '__direct__'"
        @update:model-value="(v: string) => $emit('update:proxyNodeId', v === '__direct__' ? null : v)"
      >
        <SelectTrigger>
          <SelectValue placeholder="直连（不使用代理）" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__direct__">
            直连（不使用代理）
          </SelectItem>
          <SelectItem
            v-for="node in onlineNodes"
            :key="node.id"
            :value="node.id"
          >
            {{ node.name }}{{ node.region ? ` · ${node.region}` : '' }} ({{ node.ip }}:{{ node.port }})
          </SelectItem>
        </SelectContent>
      </Select>
      <p class="mt-1 text-xs text-muted-foreground">
        对未单独配置代理的提供商生效，覆盖大模型 API 请求、余额查询、OAuth 刷新等。不影响系统内部接口。
      </p>
    </div>
  </CardSection>
</template>

<script setup lang="ts">
import Button from '@/components/ui/button.vue'
import Label from '@/components/ui/label.vue'
import Switch from '@/components/ui/switch.vue'
import Select from '@/components/ui/select.vue'
import SelectTrigger from '@/components/ui/select-trigger.vue'
import SelectValue from '@/components/ui/select-value.vue'
import SelectContent from '@/components/ui/select-content.vue'
import SelectItem from '@/components/ui/select-item.vue'
import { CardSection } from '@/components/layout'

interface ProxyNode {
  id: string
  name: string
  region?: string | null
  ip: string
  port: number
}

defineProps<{
  proxyNodeId: string | null
  enableProxyAutoFetch: boolean
  onlineNodes: ProxyNode[]
  loading: boolean
  hasChanges: boolean
}>()

defineEmits<{
  save: []
  'update:proxyNodeId': [value: string | null]
  'update:enableProxyAutoFetch': [value: boolean]
}>()
</script>
