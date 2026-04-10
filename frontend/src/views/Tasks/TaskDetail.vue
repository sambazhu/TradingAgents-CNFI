<template>
  <div class="task-detail">
    <div class="page-header">
      <div>
        <h1 class="page-title">任务详情</h1>
        <p class="page-description">
          {{ taskTitle }}
        </p>
      </div>
      <div class="header-actions">
        <el-button @click="goBack">返回任务中心</el-button>
        <el-button type="primary" :loading="loading" @click="refreshTask">刷新</el-button>
        <el-button
          v-if="normalizedStatus === 'completed'"
          type="success"
          @click="openReport"
        >
          查看报告
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :lg="16" :md="24">
        <el-card class="summary-card" shadow="never">
          <div class="summary-grid">
            <div class="summary-item">
              <div class="summary-label">任务ID</div>
              <div class="summary-value mono">{{ taskId }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">状态</div>
              <div class="summary-value">
                <el-tag :type="getStatusType(normalizedStatus)">{{ getStatusText(normalizedStatus) }}</el-tag>
              </div>
            </div>
            <div class="summary-item">
              <div class="summary-label">股票</div>
              <div class="summary-value">{{ stockDisplay }}</div>
            </div>
            <div class="summary-item">
              <div class="summary-label">开始时间</div>
              <div class="summary-value">{{ formatTime(taskData?.start_time || taskData?.created_at) }}</div>
            </div>
          </div>
        </el-card>

        <AnalysisProgressPanel
          v-if="isTaskActive"
          :progress-info="progressInfo"
          :status="normalizedStatus"
          :task-id="taskId"
          :show-task-id="false"
          title="分析进行中..."
          class="progress-panel"
        />

        <el-alert
          v-else-if="normalizedStatus === 'failed'"
          type="error"
          :closable="false"
          show-icon
          class="detail-alert"
        >
          <template #title>任务执行失败</template>
          <div class="alert-text">{{ taskErrorMessage }}</div>
        </el-alert>

        <el-card
          v-else-if="normalizedStatus === 'completed'"
          class="result-card"
          shadow="never"
        >
          <template #header>
            <div class="card-header">
              <span>完成结果</span>
              <el-tag type="success">已完成</el-tag>
            </div>
          </template>

          <div v-if="resultDecision" class="decision-card">
            <div class="decision-row">
              <span class="decision-label">最终倾向</span>
              <el-tag :type="getDecisionType(resultDecision.action)" size="large">
                {{ resultDecision.action || '未给出' }}
              </el-tag>
            </div>
            <div class="decision-row" v-if="resultDecision.reasoning">
              <span class="decision-label">核心理由</span>
              <div class="decision-text">{{ resultDecision.reasoning }}</div>
            </div>
          </div>

          <div class="result-section" v-if="resultSummary">
            <h3>分析摘要</h3>
            <p>{{ resultSummary }}</p>
          </div>

          <div class="result-section" v-if="resultRecommendation">
            <h3>投资建议</h3>
            <p>{{ resultRecommendation }}</p>
          </div>
        </el-card>
      </el-col>

      <el-col :lg="8" :md="24">
        <el-card class="meta-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>任务配置</span>
            </div>
          </template>

          <div class="meta-list">
            <div v-for="item in parameterItems" :key="item.label" class="meta-item">
              <div class="meta-label">{{ item.label }}</div>
              <div class="meta-value">{{ item.value }}</div>
            </div>
          </div>
        </el-card>

        <el-card class="meta-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>实时状态</span>
            </div>
          </template>

          <div class="meta-list">
            <div class="meta-item">
              <div class="meta-label">当前节点</div>
              <div class="meta-value">{{ progressInfo.currentStep || '-' }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">节点描述</div>
              <div class="meta-value">{{ progressInfo.currentStepDescription || progressInfo.message || '-' }}</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">进度</div>
              <div class="meta-value">{{ Math.round(progressInfo.progress || 0) }}%</div>
            </div>
            <div class="meta-item">
              <div class="meta-label">最后更新</div>
              <div class="meta-value">{{ formatTime(taskData?.last_update || taskData?.updated_at) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { analysisApi } from '@/api/analysis'
import AnalysisProgressPanel from '@/components/Analysis/AnalysisProgressPanel.vue'
import { convertAnalystIdsToNames } from '@/constants/analysts'
import { formatDateTime } from '@/utils/datetime'

const route = useRoute()
const router = useRouter()

const taskId = computed(() => String(route.params.taskId || ''))
const loading = ref(false)
const taskData = ref<any>(null)
const taskResult = ref<any>(null)
let pollingTimer: ReturnType<typeof setInterval> | null = null

const normalizedStatus = computed(() => {
  const status = taskData.value?.status || 'pending'
  return status === 'processing' ? 'running' : status
})

const isTaskActive = computed(() => ['running', 'pending'].includes(normalizedStatus.value))

const progressInfo = computed(() => ({
  progress: Number(taskData.value?.progress || 0),
  currentStep: taskData.value?.current_step_name || taskData.value?.current_step || '',
  currentStepDescription: taskData.value?.current_step_description || '',
  message: taskData.value?.message || '',
  elapsedTime: Number(taskData.value?.elapsed_time || 0),
  remainingTime: Number(taskData.value?.remaining_time || 0),
  totalTime: Number(taskData.value?.estimated_total_time || 0)
}))

const stockDisplay = computed(() => {
  const code = taskData.value?.stock_code || taskData.value?.stock_symbol || '-'
  const name = taskData.value?.stock_name
  return name ? `${name} (${code})` : code
})

const taskTitle = computed(() => {
  if (taskData.value?.stock_name || taskData.value?.stock_code) {
    return `${stockDisplay.value} 的分析进度与执行记录`
  }
  return `任务 ${taskId.value} 的分析进度与执行记录`
})

const taskErrorMessage = computed(() => {
  return taskData.value?.error_message || taskData.value?.message || '任务执行失败'
})

const resultPayload = computed(() => taskResult.value || taskData.value?.result_data || {})
const resultDecision = computed(() => resultPayload.value?.decision || null)
const resultSummary = computed(() => resultPayload.value?.summary || '')
const resultRecommendation = computed(() => resultPayload.value?.recommendation || '')

const parameterItems = computed(() => {
  const parameters = taskData.value?.parameters || {}
  const selectedAnalysts = Array.isArray(parameters.selected_analysts)
    ? convertAnalystIdsToNames(parameters.selected_analysts)
    : []

  return [
    { label: '市场', value: parameters.market_type || '-' },
    { label: '分析日期', value: parameters.analysis_date || '-' },
    { label: '分析深度', value: parameters.research_depth || '-' },
    { label: '分析师团队', value: selectedAnalysts.length ? selectedAnalysts.join('、') : '-' },
    { label: '风险评估', value: parameters.include_risk ? '开启' : '关闭' },
    { label: '快速模型', value: parameters.quick_analysis_model || '-' },
    { label: '深度模型', value: parameters.deep_analysis_model || '-' }
  ]
})

const getStatusType = (status: string): 'success' | 'info' | 'warning' | 'danger' => {
  const map: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => ({
  pending: '等待中',
  running: '进行中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消'
} as Record<string, string>)[status] || status

const getDecisionType = (action?: string): 'success' | 'warning' | 'danger' | 'info' => {
  if (action === '买入' || action === '增持') return 'success'
  if (action === '持有' || action === '观望') return 'warning'
  if (action === '卖出' || action === '减持') return 'danger'
  return 'info'
}

const formatTime = (value: string | number | null | undefined) => formatDateTime(value)

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

const startPolling = () => {
  stopPolling()
  if (!isTaskActive.value) return

  pollingTimer = setInterval(async () => {
    await loadTaskStatus(false)
  }, 5000)
}

const loadTaskResult = async () => {
  if (!taskId.value) return

  try {
    const res = await analysisApi.getTaskResult(taskId.value)
    taskResult.value = (res as any)?.data?.data || (res as any)?.data || taskResult.value
  } catch (error) {
    console.warn('获取任务结果失败，使用状态接口中的结果兜底:', error)
  }
}

const loadTaskStatus = async (showError = true) => {
  if (!taskId.value) return

  loading.value = true
  try {
    const res = await analysisApi.getTaskStatus(taskId.value)
    taskData.value = res.data

    if (normalizedStatus.value === 'completed') {
      stopPolling()
      await loadTaskResult()
    } else if (!isTaskActive.value) {
      stopPolling()
    }
  } catch (error: any) {
    if (showError) {
      ElMessage.error(error?.message || '加载任务详情失败')
    }
  } finally {
    loading.value = false
  }
}

const refreshTask = async () => {
  await loadTaskStatus(true)
  startPolling()
}

const openReport = () => {
  router.push({ name: 'ReportDetail', params: { id: taskId.value } })
}

const goBack = () => {
  router.push({ name: 'TaskCenterHome' })
}

onMounted(async () => {
  await loadTaskStatus(true)
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
.task-detail {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 20px;
  }

  .page-title {
    margin: 0 0 8px;
    font-size: 28px;
    font-weight: 700;
  }

  .page-description {
    margin: 0;
    color: var(--el-text-color-secondary);
  }

  .header-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .summary-card,
  .meta-card,
  .result-card,
  .progress-panel,
  .detail-alert {
    margin-bottom: 20px;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
  }

  .summary-item,
  .meta-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .summary-label,
  .meta-label {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }

  .summary-value,
  .meta-value {
    color: var(--el-text-color-primary);
    line-height: 1.7;
    word-break: break-word;
  }

  .mono {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .meta-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .decision-card {
    padding: 18px;
    border-radius: 14px;
    background: linear-gradient(180deg, #f8fbff 0%, #f2f7ff 100%);
    border: 1px solid rgba(64, 158, 255, 0.18);
    margin-bottom: 18px;
  }

  .decision-row {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .decision-row + .decision-row {
    margin-top: 16px;
  }

  .decision-label {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }

  .decision-text,
  .alert-text,
  .result-section p {
    white-space: pre-wrap;
    line-height: 1.8;
    margin: 0;
  }

  .result-section + .result-section {
    margin-top: 18px;
  }

  .result-section h3 {
    margin: 0 0 10px;
    font-size: 16px;
  }

  @media (max-width: 1200px) {
    .summary-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
    }

    .summary-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style>
