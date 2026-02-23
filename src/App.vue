<template>
  <n-config-provider :theme="theme" :hljs="hljs">
    <div class="flex flex-col h-screen overflow-hidden">
      <n-layout-header bordered class="flex items-center justify-between px-6 h-12 flex-shrink-0">
        <div class="text-xl font-bold">Bena Protractor</div>
        <div class="flex items-center gap-4">
          <a href="https://github.com/TeamTorappu/BenaProtractor" target="_blank"
            class="hover:opacity-70 transition-opacity flex items-center">
            <n-icon size="24" :color="isDark ? '#e0e0e0' : '#1a1a1a'">
              <LogoGithub />
            </n-icon>
          </a>
          <n-switch v-model:value="isDark" :rail-style="railStyle" />
        </div>
      </n-layout-header>

      <n-layout has-sider class="flex-grow">

        <n-layout-content content-style="display: flex; height: 100%; padding: 12px; gap: 12px;">

          <div class="w-72 flex-shrink-0 flex flex-col h-full">
            <n-card title="Buff 列表" size="small" class="h-full flex flex-col overflow-hidden"
              :segmented="{ content: true }">
              <template #header-extra>
                <n-badge :value="filteredKeys.length" color="#18a058" />
              </template>
              <div class="mb-3">
                <n-input v-model:value="searchQuery" placeholder="搜索 Buff..." clearable>
                  <template #prefix><n-icon>
                      <Search />
                    </n-icon></template>
                </n-input>
              </div>
              <div class="flex-grow overflow-hidden">
                <n-virtual-list :items="filteredKeys" :item-size="34" class="h-full">
                  <template #default="{ item }">
                    <div
                      :class="['px-3 py-1.5 my-0.5 rounded cursor-pointer transition-colors',
                        selectedKey === item.key ? 'bg-blue-500/20 text-blue-500' : 'hover:bg-gray-100 dark:hover:bg-gray-800']"
                      @click="selectKey(item.key)">
                      {{ item.label }}
                    </div>
                  </template>
                </n-virtual-list>
              </div>
            </n-card>
          </div>

          <div class="flex-grow min-w-0 h-full">
            <n-card title="数据结构" size="small" class="h-full overflow-hidden" :segmented="{ content: true }">
              <template #header-extra>
                <n-switch v-model:value="showAll" size="small" @update:value="refreshTree">
                  <template #checked>全部</template>
                  <template #unchecked>精简</template>
                </n-switch>
              </template>
              <div class="h-full overflow-auto">
                <n-tree :data="treeData" block-line selectable expand-on-click
                  @update:selected-keys="handleSelectNode" />
              </div>
            </n-card>
          </div>

        </n-layout-content>

        <n-layout-sider :width="450" collapse-mode="width" :collapsed-width="0" show-trigger="arrow-circle" bordered
          :native-scrollbar="false" class="h-full">
          <n-card title="JSON" size="small" :bordered="false" class="h-full ">
            <div class="h-full overflow-auto">
              <div v-if="isJsonEmpty" class="text-gray-400 text-sm flex items-center justify-center h-full">
                No JSON
              </div>
              <n-code v-else :code="codeContent" language="json" show-line-numbers word-wrap />
            </div>
          </n-card>
        </n-layout-sider>

      </n-layout>
    </div>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NConfigProvider,
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NLayoutSider,
  NCard,
  NSwitch,
  NInput,
  NTree,
  NCode,
  NIcon,
  NVirtualList,
  NBadge,
  darkTheme,
  type TreeOption
} from 'naive-ui'
import { LogoGithub, Search } from '@vicons/carbon'
import hljs from 'highlight.js/lib/core'
import json from 'highlight.js/lib/languages/json'
import { loadPublicJSON } from '@/composables/usePublic'
import { parseBuffsToTree } from '@/parser/buff';

hljs.registerLanguage('json', json)

const isDark = ref(false)
const theme = computed(() => (isDark.value ? darkTheme : null))
const railStyle = ({ checked }: { focused: boolean; checked: boolean }) => ({
  background: checked ? '#18a058' : '#ddd'
})

const allBuffdata = ref<Record<string, Record<string, any>>>({})
loadPublicJSON('gamedata/battle/buff_template_data.json')
  .then((d) => {
    allBuffdata.value = d as Record<string, Record<string, any>>
  })
  .catch(() => {
    allBuffdata.value = {}
  })

const searchQuery = ref('')

const treeData = ref<TreeOption[]>([])

const codeContent = ref('')
const isJsonEmpty = computed(() => !codeContent.value || codeContent.value.trim() === '{}' )

const showAll = ref(false)

const selectedKey = ref<string | null>(null)

const filteredKeys = computed(() => {
  const keys = Object.keys(allBuffdata.value || {})
  const q = searchQuery.value.trim()
  const filtered = !q ? keys : keys.filter(k => k.includes(q))
  return filtered.map(k => ({ label: k, key: k }))
})

const selectKey = async (key: string) => {
  selectedKey.value = key
  treeData.value = []
  const obj = allBuffdata.value ? allBuffdata.value[key] : undefined
  codeContent.value = obj ? JSON.stringify(obj, null, 2) : '{}'
  treeData.value = await parseBuffsToTree(obj, showAll.value)
  console.log(treeData.value)
}

const refreshTree = async () => {
  if (!selectedKey.value) return
  const obj = allBuffdata.value ? allBuffdata.value[selectedKey.value] : undefined
  treeData.value = await parseBuffsToTree(obj, showAll.value)
}



const handleSelectNode = (keys: Array<string | number>) => {
  if (keys.length > 0) {
    console.log('Selected:', keys[0])
  }
}

</script>
<style scoped></style>