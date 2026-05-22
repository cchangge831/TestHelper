/**
 * API 封装层 — 集中管理所有后端接口调用。
 * 新增接口只需在此文件添加方法，组件内部不直接调用 axios。
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 响应拦截器：统一处理错误提示
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.message || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

/** 环境管理 */
export const getEnvs = () => api.get('/envs')
export const startEnv = (version) => api.post(`/envs/${version}/start`)
export const stopEnv = (version) => api.post(`/envs/${version}/stop`)
export const getAccessUrl = (version) => api.get(`/envs/${version}/access-url`)
export const getJarPath = (version) => api.get(`/envs/${version}/jar-path`)
export const openJarFolder = (version) => api.post(`/envs/${version}/open-jar`)
export const openLogFolder = (version) => api.post(`/envs/${version}/open-log`)

/** Properties CRUD */
export const getProps = (version, file) => api.get(`/envs/${version}/props/${file}`)
export const batchSaveProps = (version, file, data) =>
  api.put(`/envs/${version}/props/${file}`, data)
export const updateProp = (version, file, key, value) =>
  api.put(`/envs/${version}/props/${file}/${key}`, { value })
export const deleteProp = (version, file, key) =>
  api.delete(`/envs/${version}/props/${file}/${key}`)

/** server.xml 端口 */
export const getServerPorts = (version) => api.get(`/envs/${version}/server-ports`)
export const updateServerPorts = (version, data) =>
  api.put(`/envs/${version}/server-ports`, data)

/** 调试端口 */
export const getDebugPort = (version) => api.get(`/envs/${version}/debug-port`)
export const upsertDebugPort = (version, port) =>
  api.put(`/envs/${version}/debug-port`, { debug_port: port })
export const deleteDebugPort = (version) =>
  api.delete(`/envs/${version}/debug-port`)
