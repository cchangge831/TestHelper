<template>
  <el-dialog
    :title="`${version} — ${fileKey}.properties`"
    v-model="dialogVisible"
    width="850px"
    top="3vh"
    @close="handleClose"
    destroy-on-close
    class="props-dialog"
  >
    <!-- 文件不存在提示（db.properties 特有） -->
    <el-alert
      v-if="fileNotFound"
      :title="notFoundMessage"
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
    />

    <!-- 参数列表表格 -->
    <el-table v-else :data="propsList" stripe :max-height="tableMaxHeight" style="width: 100%">
      <el-table-column label="Key" min-width="200">
        <template #default="{ row }">
          <el-input
            v-if="row.editing"
            v-model="row.key"
            size="small"
            placeholder="参数名称"
          />
          <span v-else>{{ row.key }}</span>
        </template>
      </el-table-column>
      <el-table-column label="Value" min-width="280">
        <template #default="{ row }">
          <el-input
            v-if="row.editing"
            v-model="row.value"
            size="small"
            placeholder="参数值"
          />
          <span v-else>{{ row.value }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="!row.editing"
            size="small"
            link
            @click="startEdit(row)"
          >
            编辑
          </el-button>
          <el-button
            v-if="row.editing"
            size="small"
            link
            type="primary"
            @click="confirmEdit(row)"
          >
            确定
          </el-button>
          <el-popconfirm
            title="确定删除该参数？"
            @confirm="handleDelete($index)"
          >
            <template #reference>
              <el-button size="small" link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 操作按钮 -->
    <div style="margin-top: 16px; display: flex; gap: 12px" v-if="!fileNotFound">
      <el-button @click="addRow" :icon="Plus">新增参数</el-button>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">
        保存所有修改
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getProps, batchSaveProps, deleteProp } from '../api/index.js'

const props = defineProps({
  visible: Boolean,
  version: String,
  fileKey: String,
})
const emit = defineEmits(['close', 'saved'])

const dialogVisible = ref(false)
const propsList = ref([])
const saving = ref(false)
const fileNotFound = ref(false)
const notFoundMessage = ref('')
/** 表格高度：自适应对话框剩余空间 */
const tableMaxHeight = ref('calc(90vh - 180px)')

watch(() => props.visible, async (val) => {
  dialogVisible.value = val
  if (val) {
    await loadProps()
  }
}, { immediate: true })

/** 加载 properties 文件内容 */
async function loadProps() {
  try {
    const res = await getProps(props.version, props.fileKey)
    fileNotFound.value = false
    propsList.value = Object.entries(res.data).map(([key, value]) => ({
      key,
      value,
      editing: false,
      _originalKey: key,
      _originalValue: value,
    }))
  } catch (err) {
    if (err.response?.data?.error === 'need_start') {
      fileNotFound.value = true
      notFoundMessage.value = err.response.data.message || '需要启动系统来创建此文件'
      propsList.value = []
    }
  }
}

/** 开始编辑行 */
function startEdit(row) {
  row.editing = true
}

/** 确认单行编辑 */
function confirmEdit(row) {
  row.editing = false
}

/** 新增空行 */
function addRow() {
  propsList.value.push({
    key: '',
    value: '',
    editing: true,
    _originalKey: '',
    _originalValue: '',
  })
}

/** 删除行 */
async function handleDelete(index) {
  const item = propsList.value[index]
  if (item.key) {
    try {
      await deleteProp(props.version, props.fileKey, item._originalKey)
      ElMessage.success('已删除')
    } catch {
      return
    }
  }
  propsList.value.splice(index, 1)
}

/** 保存所有修改（全量覆盖，触发一次备份） */
async function handleSave() {
  saving.value = true
  try {
    const data = {}
    for (const item of propsList.value) {
      if (item.key) {
        data[item.key] = item.value
      }
    }
    await batchSaveProps(props.version, props.fileKey, data)
    ElMessage.success('保存成功，已备份原文件')
    emit('saved')
    dialogVisible.value = false
  } catch {
    // 错误已在 axios 拦截器中处理
  } finally {
    saving.value = false
  }
}

function handleClose() {
  dialogVisible.value = false
  emit('close')
}
</script>

<style scoped>
/* 表格内文字换行 */
:deep(.el-table__body) td {
  word-break: break-all;
}
</style>

<style>
/* 对话框高度 90vh，body 区域隐藏溢出让表格自行滚动 */
.props-dialog {
  max-height: 90vh !important;
  display: flex;
  flex-direction: column;
}
.props-dialog .el-dialog__body {
  overflow: hidden !important;
  padding-top: 12px;
  padding-bottom: 12px;
  flex: 1;
}
</style>
