<template>
  <div id="app-container">
    <!-- 渐变顶栏 -->
    <div class="app-header">
      <div class="header-row">
        <div class="header-left">
          <el-icon :size="22"><Monitor /></el-icon>
          <h1>系统管理</h1>
        </div>
        <el-button
          class="header-btn"
          :icon="Refresh"
          @click="refreshEnvs"
          :loading="loading"
          size="default"
        >
          刷新
        </el-button>
      </div>
      <p class="header-desc">管理和监控本地 BI 系统实例 · 共 {{ envs.length }} 个环境</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">总环境</div>
            <div class="stat-value total">{{ envs.length }}</div>
          </div>
          <div class="stat-icon total-bg">📦</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">运行中</div>
            <div class="stat-value running">{{ runningCount }}</div>
          </div>
          <div class="stat-icon running-bg">▶</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-info">
            <div class="stat-label">已停止</div>
            <div class="stat-value stopped">{{ stoppedCount }}</div>
          </div>
          <div class="stat-icon stopped-bg">⏹</div>
        </div>
      </el-col>
    </el-row>

    <!-- 环境列表卡片 -->
    <el-card class="env-table-card" shadow="never">
      <template #header>
        <span class="card-title">环境列表</span>
      </template>
      <el-table :data="envs" stripe style="width: 100%" v-loading="loading" class="env-table">
        <el-table-column label="Version" width="130">
          <template #default="{ row }">
            <el-button
              v-if="row.version"
              link
              type="primary"
              size="small"
              @click="handleCopyEnvInfo(row)"
              class="version-btn"
            >
              {{ row.version }}
            </el-button>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <span :class="['status-tag', row.status === 'running' ? 'status-running' : 'status-stopped']">
              <span :class="['status-dot', row.status === 'running' ? 'dot-running' : 'dot-stopped']" />
              {{ row.status === 'running' ? '运行中' : '已停止' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="访问端口" width="100">
          <template #default="{ row }">
            <el-button
              v-if="row.connector_port"
              link
              type="primary"
              size="small"
              @click="handleAccess(row)"
              class="port-btn"
            >
              {{ row.connector_port }}
            </el-button>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="320">
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
        <el-table-column label="配置文件" min-width="240">
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
import {
  Monitor, Refresh,
  VideoPlay, VideoPause, FolderOpened,
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

const runningCount = computed(() => envs.value.filter(e => e.status === 'running').length)
const stoppedCount = computed(() => envs.value.filter(e => e.status === 'stopped').length)

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
  } catch {
    // 错误已在 axios 拦截器中提示，保留现有列表
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

/** 标签页可见时自动刷新（用户切换回来时检测文件变动） */
function onVisibilityChange() {
  if (document.visibilityState === 'visible') {
    refreshEnvs()
  }
}

onMounted(() => {
  // 先展示缓存数据，再在后台拉取最新数据
  loadCachedEnvs()
  refreshEnvs()
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<style>
#app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f7fa;
  min-height: 100vh;
}

/* ---- 渐变色顶栏 ---- */
.app-header {
  background: linear-gradient(135deg, #409EFF 0%, #2b7ed6 100%);
  border-radius: 10px;
  padding: 18px 24px;
  margin-bottom: 20px;
  color: #fff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.25);
}
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-left h1 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #fff;
}
.header-btn {
  background: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: #fff !important;
}
.header-btn:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  border-color: rgba(255, 255, 255, 0.5) !important;
}
.header-desc {
  margin: 6px 0 0 0;
  font-size: 13px;
  opacity: 0.75;
}

/* ---- 统计卡片 ---- */
.stats-row {
  margin-bottom: 20px !important;
}
.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #f0f0f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s, transform 0.2s;
}
.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-value.total { color: #409EFF; }
.stat-value.running { color: #67C23A; }
.stat-value.stopped { color: #909399; }
.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.total-bg { background: linear-gradient(135deg, #ecf5ff, #d9ecff); }
.running-bg { background: linear-gradient(135deg, #f0f9eb, #e1f3d8); }
.stopped-bg { background: linear-gradient(135deg, #f4f4f5, #e9e9eb); }

/* ---- 环境列表卡片 ---- */
.env-table-card {
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.env-table-card :deep(.el-card__header) {
  padding: 14px 20px;
  border-bottom: 1px solid #f5f5f5;
}
.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.env-table {
  border-radius: 0 0 10px 10px;
}
.env-table :deep(.el-table__row) {
  transition: background-color 0.2s;
}

/* ---- 状态标签 ---- */
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.status-running {
  background: #f0f9eb;
  color: #67C23A;
}
.status-stopped {
  background: #f4f4f5;
  color: #909399;
}
.status-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.dot-running {
  background: #67C23A;
  animation: pulse 2s ease-in-out infinite;
}
.dot-stopped {
  background: #C0C4CC;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ---- 端口 / Version 按钮 ---- */
.port-btn {
  font-family: 'Courier New', monospace;
  font-weight: 600;
}
.version-btn {
  font-weight: 600;
}

/* ---- 辅助类 ---- */
.text-muted {
  color: #C0C4CC;
}
</style>
