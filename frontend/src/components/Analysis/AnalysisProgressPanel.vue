<template>
  <el-card class="progress-card" shadow="hover">
    <template #header>
      <div class="progress-header">
        <h4>
          <el-icon class="rotating-icon">
            <Loading />
          </el-icon>
          {{ title }}
        </h4>
        <el-tag v-if="showTaskId && taskId" type="info" effect="plain">{{ taskId }}</el-tag>
      </div>
    </template>

    <div class="progress-content">
      <div class="overall-progress-info">
        <div class="progress-stats">
          <div class="stat-item">
            <div class="stat-label">已用时间</div>
            <div class="stat-value">{{ formatDuration(progressInfo.elapsedTime) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">预计剩余</div>
            <div class="stat-value">{{ formatDuration(progressInfo.remainingTime) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">预计总时长</div>
            <div class="stat-value">{{ formatDuration(progressInfo.totalTime) }}</div>
          </div>
        </div>
      </div>

      <div class="progress-bar-section">
        <el-progress
          :percentage="Math.round(progressInfo.progress || 0)"
          :stroke-width="12"
          :show-text="true"
          :status="progressStatus"
          class="main-progress-bar"
        />
      </div>

      <div class="current-task-info">
        <div class="task-title">
          <el-icon class="task-icon">
            <Loading />
          </el-icon>
          {{ progressInfo.currentStep || '正在初始化分析引擎...' }}
        </div>
        <div class="task-description">
          {{ progressInfo.currentStepDescription || progressInfo.message || fallbackMessage }}
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loading } from '@element-plus/icons-vue'

interface ProgressInfo {
  progress: number
  currentStep: string
  currentStepDescription: string
  message: string
  elapsedTime: number
  remainingTime: number
  totalTime: number
}

const props = withDefaults(defineProps<{
  progressInfo: ProgressInfo
  status?: string
  title?: string
  taskId?: string
  showTaskId?: boolean
  fallbackMessage?: string
}>(), {
  status: 'running',
  title: '分析进行中...',
  taskId: '',
  showTaskId: false,
  fallbackMessage: 'AI正在根据您的要求重点分析相关内容'
})

const progressStatus = computed(() => {
  if (props.status === 'completed') return 'success'
  if (props.status === 'failed') return 'exception'
  return ''
})

const formatDuration = (seconds: number) => {
  if (!seconds || seconds <= 0) return '计算中...'
  if (seconds < 60) return `${Math.floor(seconds)}秒`
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remain = Math.floor(seconds % 60)
    return remain > 0 ? `${minutes}分${remain}秒` : `${minutes}分钟`
  }

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}小时${minutes}分钟`
}
</script>

<style scoped lang="scss">
.progress-card {
  .progress-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;

    h4 {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 0;
      font-size: 18px;
      font-weight: 700;
    }
  }

  .progress-content {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .progress-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
  }

  .stat-item {
    padding: 20px;
    border-radius: 16px;
    border: 1px solid var(--el-border-color-light);
    background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
    text-align: center;
  }

  .stat-label {
    color: var(--el-text-color-secondary);
    font-size: 14px;
    margin-bottom: 10px;
  }

  .stat-value {
    color: var(--el-text-color-primary);
    font-size: 18px;
    font-weight: 700;
  }

  .current-task-info {
    padding: 24px;
    border-radius: 18px;
    border: 1px solid rgba(64, 158, 255, 0.4);
    background: linear-gradient(180deg, rgba(64, 158, 255, 0.06) 0%, rgba(64, 158, 255, 0.02) 100%);
  }

  .task-title {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #2457d6;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 12px;
  }

  .task-description {
    white-space: pre-wrap;
    line-height: 1.7;
    color: var(--el-text-color-regular);
  }

  .rotating-icon {
    animation: rotate 1.2s linear infinite;
  }

  @media (max-width: 900px) {
    .progress-stats {
      grid-template-columns: 1fr;
    }
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
