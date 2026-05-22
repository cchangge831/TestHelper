<template>
  <div id="app-container">
    <!-- 页面标题栏 -->
    <div class="header">
      <h1>
        <el-icon :size="28"><Monitor /></el-icon>
        系统管理
      </h1>
      <el-button :icon="Refresh" @click="refreshEnvs" :loading="loading">
        刷新
      </el-button>
    </div>

    <!-- 环境列表表格 -->
    <el-card shadow="never">
      <el-table :data="envs" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="version" label="Version" width="140" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'running' ? 'success' : 'info'" size="small">
              <el-icon style="margin-right: 4px;">
                <CircleCheckFilled v-if="row.status === 'running'" />
                <CircleCloseFilled v-else />
              </el-icon>
              {{ row.status === 'running' ? '运行中' : '已停止' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="访问端口" width="120">
          <template #default="{ row }">
            <el-button
              v-if="row.connector_port"
              link
              type="primary"
              size="small"
              @click="handleCopyEnvInfo(row)"
            >
              {{ row.connector_port }}
            </el-button>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="340">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                size="small"
                type="primary"
                @click="handleStart(row)"
                :disabled="row.status === 'running'"
                :icon="VideoPlay"
              >
                启动
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="handleStop(row)"
                :disabled="row.status === 'stopped'"
                :icon="VideoPause"
              >
                停止
              </el-button>
              <el-button
                size="small"
                @click="handleAccess(row)"
                :icon="Link"
                :disabled="row.status !== 'running'"
              >
                访问
              </el-button>
              <el-button
                size="small"
                @click="handleOpenJar(row)"
                :icon="FolderOpened"
              >
                Jar
              </el-button>
              <el-button
                size="small"
                @click="handleOpenLog(row)"
                :icon="FolderOpened"
              >
                Log
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
        <el-table-column label="配置文件" min-width="280">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="openPropsEditor(row, 'db')">db</el-button>
              <el-button size="small" @click="openPropsEditor(row, 'bi')">bi</el-button>
              <el-button size="small" @click="openPortEditor(row)">端口</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 配置编辑弹窗 -->
    <PropsEditor
      v-if="propsEditor.visible"
      :visible="propsEditor.visible"
      :version="propsEditor.version"
      :file-key="propsEditor.fileKey"
      @close="propsEditor.visible = false"
      @saved="refreshEnvs"
    />
    <PortEditor
      v-if="portEditor.visible"
      :visible="portEditor.visible"
      :version="portEditor.version"
      @close="portEditor.visible = false"
      @saved="refreshEnvs"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  Monitor, Refresh, CircleCheckFilled, CircleCloseFilled,
  VideoPlay, VideoPause, Link, FolderOpened,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getEnvs, startEnv, stopEnv, getAccessUrl, openJarFolder, openLogFolder, getDebugPort,
} from './api/index.js'
import PropsEditor from './components/PropsEditor.vue'
import PortEditor from './components/PortEditor.vue'

const CACHE_KEY = 'testhelper_envs'

const envs = ref([])
const loading = ref(false)

/** 从 sessionStorage 加载缓存的环境数据 */
function loadCachedEnvs() {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY)
    if (raw) {
      envs.value = JSON.parse(raw)
    }
  } catch {
    // 缓存读取失败不影响正常请求
  }
}

/** 缓存环境数据到 sessionStorage */
function saveEnvsToCache(data) {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(data))
  } catch {
    // 存储失败不阻塞
  }
}

/** 刷新环境列表 */
async function refreshEnvs() {
  loading.value = true
  try {
    const res = await getEnvs()
    envs.value = res.data
    saveEnvsToCache(res.data)
  } finally {
    loading.value = false
  }
}

/** 启动环境 */
async function handleStart(row) {
  const res = await startEnv(row.version)
  ElMessage.success(res.data.message)
  setTimeout(refreshEnvs, 3000)
}

/** 停止环境（需用户确认） */
async function handleStop(row) {
  try {
    await ElMessageBox.confirm(
      `确定要停止 ${row.version} 环境吗？`,
      '停止确认',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )
    const res = await stopEnv(row.version)
    ElMessage.success(res.data.message)
    setTimeout(refreshEnvs, 3000)
  } catch {
    // 用户取消，不处理
  }
}

/** 访问环境 */
async function handleAccess(row) {
  const res = await getAccessUrl(row.version)
  window.open(res.data.url, '_blank')
}

/** 打开 Jar 目录（在 Windows 资源管理器中打开） */
async function handleOpenJar(row) {
  await openJarFolder(row.version)
}

/** 打开日志目录（在 Windows 资源管理器中打开） */
async function handleOpenLog(row) {
  await openLogFolder(row.version)
}

/** 点击端口号复制环境信息 */
async function handleCopyEnvInfo(row) {
  let debugPort = '-'
  try {
    const res = await getDebugPort(row.version)
    debugPort = res.data.debug_port ?? '-'
  } catch {}
  const accessUrl = `http://192.168.151.77:${row.connector_port}/bi/Viewer`
  const text = `环境：${row.version}  访问地址：${accessUrl}  调试端口：${debugPort}`
  await navigator.clipboard.writeText(text)
  ElMessage.success('环境信息已复制到剪贴板')
}

// ===================== 弹窗控制 =====================
const propsEditor = ref({ visible: false, version: '', fileKey: 'db' })
const portEditor = ref({ visible: false, version: '' })

function openPropsEditor(row, fileKey) {
  propsEditor.value = { visible: true, version: row.version, fileKey }
}
function openPortEditor(row) {
  portEditor.value = { visible: true, version: row.version }
}

onMounted(() => {
  // 先展示缓存数据，再在后台拉取最新数据
  loadCachedEnvs()
  refreshEnvs()
})
</script>

<style>
#app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header h1 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 24px;
  margin: 0;
}
.mono {
  font-family: 'Courier New', monospace;
}
.text-muted {
  color: #999;
}
</style>
