<template>
  <el-dialog
    :title="`${version} — 调试端口`"
    v-model="dialogVisible"
    width="420px"
    @close="handleClose"
    destroy-on-close
  >
    <!-- 已有调试端口 -->
    <template v-if="hasPort">
      <el-form label-width="120px">
        <el-form-item label="Debug Port">
          <el-input-number
            v-model="debugPort"
            :min="1024"
            :max="65535"
          />
        </el-form-item>
      </el-form>
      <div style="margin-top: 8px;">
        <el-popconfirm
          title="确定删除调试端口配置？"
          @confirm="handleDelete"
        >
          <template #reference>
            <el-button type="danger" link :icon="Delete">删除调试端口</el-button>
          </template>
        </el-popconfirm>
      </div>
    </template>

    <!-- 无调试端口 -->
    <template v-else>
      <el-alert
        title="当前无调试端口"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom: 16px"
      />
      <el-form label-width="120px">
        <el-form-item label="新 Debug Port">
          <el-input-number v-model="debugPort" :min="1024" :max="65535" />
        </el-form-item>
      </el-form>
    </template>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">
        {{ hasPort ? '保存修改' : '添加' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getDebugPort, upsertDebugPort, deleteDebugPort } from '../api/index.js'

const props = defineProps({
  visible: Boolean,
  version: String,
})
const emit = defineEmits(['close', 'saved'])

const dialogVisible = ref(false)
const debugPort = ref(null)
const hasPort = ref(false)
const saving = ref(false)

watch(() => props.visible, async (val) => {
  dialogVisible.value = val
  if (val) {
    const res = await getDebugPort(props.version)
    hasPort.value = res.data.debug_port !== null
    debugPort.value = res.data.debug_port || 8000
  }
}, { immediate: true })

async function handleSave() {
  saving.value = true
  try {
    await upsertDebugPort(props.version, debugPort.value)
    ElMessage.success(hasPort.value ? '调试端口已更新' : '调试端口已添加')
    emit('saved')
    dialogVisible.value = false
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  try {
    await deleteDebugPort(props.version)
    ElMessage.success('调试端口已删除')
    emit('saved')
    dialogVisible.value = false
  } catch {
    // 错误已在拦截器中处理
  }
}

function handleClose() {
  dialogVisible.value = false
  emit('close')
}
</script>
