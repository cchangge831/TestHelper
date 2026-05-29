<template>
  <el-dialog
    :title="`${version} — 端口配置`"
    v-model="dialogVisible"
    width="480px"
    @close="handleClose"
    destroy-on-close
    class="port-dialog"
  >
    <el-form label-width="130px" label-suffix="：" v-if="ports">
      <!-- Tomcat 端口 -->
      <el-divider content-position="left">Tomcat 端口</el-divider>
      <el-form-item label="Shutdown Port">
        <el-input v-model.number="ports.shutdown_port" type="number" min="1024" max="65535" />
      </el-form-item>
      <el-form-item label="Connector Port">
        <el-input v-model.number="ports.connector_port" type="number" min="1024" max="65535" />
      </el-form-item>

      <!-- 调试端口 -->
      <el-divider content-position="left">调试端口</el-divider>
      <el-form-item label="Debug Port">
        <el-input v-model.number="debugPort" type="number" min="1024" max="65535" placeholder="空值表示无调试端口" />
      </el-form-item>
      <el-form-item v-if="hasPort">
        <el-popconfirm title="确定删除调试端口配置？" @confirm="handleDeleteDebug">
          <template #reference>
            <el-button type="danger" link size="small">删除调试端口</el-button>
          </template>
        </el-popconfirm>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getServerPorts, updateServerPorts, getDebugPort, upsertDebugPort, deleteDebugPort } from '../api/index.js'

const props = defineProps({
  visible: Boolean,
  version: String,
})
const emit = defineEmits(['close', 'saved'])

const dialogVisible = ref(false)
const ports = ref(null)
const debugPort = ref(null)
const hasPort = ref(false)
const saving = ref(false)

watch(() => props.visible, async (val) => {
  dialogVisible.value = val
  if (val) {
    await Promise.all([
      loadServerPorts(),
      loadDebugPort(),
    ])
  }
}, { immediate: true })

async function loadServerPorts() {
  const res = await getServerPorts(props.version)
  ports.value = res.data
}

async function loadDebugPort() {
  const res = await getDebugPort(props.version)
  hasPort.value = res.data.debug_port !== null
  debugPort.value = res.data.debug_port || null
}

/** 保存所有端口 + 调试端口 */
async function handleSave() {
  saving.value = true
  try {
    // 保存 server.xml 端口
    await updateServerPorts(props.version, {
      shutdown_port: String(ports.value.shutdown_port),
      connector_port: String(ports.value.connector_port),
    })

    // 保存或删除调试端口（server.xml 已写入，这里失败不影响端口保存结果）
    try {
      if (debugPort.value) {
        await upsertDebugPort(props.version, Number(debugPort.value))
      } else {
        await deleteDebugPort(props.version)
      }
    } catch {
      ElMessage.warning('端口已保存，但调试端口更新失败，请重试')
    }

    ElMessage.success('端口配置已更新')
    emit('saved')
    dialogVisible.value = false
  } finally {
    saving.value = false
  }
}

async function handleDeleteDebug() {
  await deleteDebugPort(props.version)
  debugPort.value = null
  hasPort.value = false
  ElMessage.success('调试端口已删除')
}

function handleClose() {
  dialogVisible.value = false
  emit('close')
}
</script>

<style>
.port-dialog .el-dialog__footer {
  border-top: 1px solid #f0f0f0;
  padding: 12px 20px;
}
</style>
