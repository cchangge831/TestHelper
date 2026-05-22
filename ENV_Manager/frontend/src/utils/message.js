/**
 * 消息提示工具 — 统一操作成功/失败的反馈。
 */
import { ElMessage, ElMessageBox } from 'element-plus'

export function showSuccess(msg) {
  ElMessage.success(msg)
}

export function showError(msg) {
  ElMessage.error(msg)
}

/**
 * 确认对话框，返回 Promise<boolean>。
 * 用于删除等危险操作前的二次确认。
 */
export function confirmAction(message, title = '确认操作') {
  return ElMessageBox.confirm(message, title, {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => true)
    .catch(() => false)
}
