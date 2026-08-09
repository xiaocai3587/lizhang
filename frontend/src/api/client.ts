// axios 实例
import axios from 'axios';
import { ElMessage } from 'element-plus';

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 响应拦截器
client.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = '请求失败';
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;
      if (data && data.detail) {
        message = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      } else {
        if (status === 404) message = '资源不存在';
        else if (status === 422) message = '数据验证失败';
        else if (status >= 500) message = '服务器错误';
        else message = `请求错误 (${status})`;
      }
    } else if (error.request) {
      message = '无法连接服务器，请检查后端是否启动';
    } else {
      message = error.message;
    }
    ElMessage.error(message);
    return Promise.reject(error);
  }
);

export default client;
