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
      <el-col :span="24">
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
      </el-col>
    </el-row>

    <el-row :gutter="20" class="detail-row align-stretch">
      <el-col :lg="16" :md="24" class="left-column">
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

      <el-col :lg="8" :md="24" class="right-column">
        <el-card class="meta-card config-card full-height-card" shadow="never">
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
      </el-col>
    </el-row>

    <el-row v-if="isTaskActive || executionSteps.length" :gutter="20" class="detail-row align-stretch">
      <el-col :lg="16" :md="24" class="left-column">
        <el-card class="meta-card execution-card full-height-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>执行链路</span>
            </div>
          </template>

          <div class="graph-section">
            <div class="graph-label">实际提交分析师</div>
            <div v-if="submittedAnalystNames.length" class="submitted-analysts">
              <el-tag
                v-for="name in submittedAnalystNames"
                :key="name"
                size="small"
                type="info"
                effect="plain"
              >
                {{ name }}
              </el-tag>
            </div>
            <div v-else class="graph-empty">未记录</div>
          </div>

          <div class="graph-section">
            <div class="graph-label">完整执行顺序</div>
            <div v-if="executionSteps.length" class="execution-flow horizontal">
              <div
                v-for="(step, index) in executionSteps"
                :key="`${step.title}-${index}`"
                :class="['flow-step', step.status]"
              >
                <div class="flow-title">{{ step.title }}</div>
                <div class="flow-desc">{{ step.description }}</div>
                <div
                  v-if="index < executionSteps.length - 1"
                  :class="['flow-connector', 'horizontal', step.status]"
                >
                  <span class="flow-connector-line"></span>
                  <span class="flow-arrow horizontal">→</span>
                </div>
              </div>
            </div>
            <div v-else class="graph-empty">暂无链路信息</div>
          </div>
        </el-card>
      </el-col>

      <el-col :lg="8" :md="24" class="right-column">
        <el-card class="meta-card status-card full-height-card" shadow="never">
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

const submittedAnalystIds = computed<string[]>(() => {
  const parameters = taskData.value?.parameters || {}
  if (Array.isArray(parameters.selected_analysts)) {
    return parameters.selected_analysts
  }
  if (Array.isArray(taskData.value?.analysts)) {
    return taskData.value.analysts
  }
  return []
})

const submittedAnalystNames = computed(() => convertAnalystIdsToNames(submittedAnalystIds.value))

const getDebateRounds = (researchDepth: string) => {
  if (['快速', '基础', '标准'].includes(researchDepth)) return 1
  if (researchDepth === '深度') return 2
  if (researchDepth === '全面') return 3
  return 1
}

const buildDerivedExecutionSteps = () => {
  const parameters = taskData.value?.parameters || {}
  const researchDepth = parameters.research_depth || taskData.value?.research_depth || '标准'
  const includeRisk = parameters.include_risk !== false
  const analystStepMap: Record<string, { title: string; description: string }> = {
    market: {
      title: '📊 市场分析师',
      description: '分析股价走势、量价结构与技术指标'
    },
    fundamentals: {
      title: '💼 基本面分析师',
      description: '分析财务质量、估值水平与经营基本面'
    },
    news: {
      title: '📰 新闻分析师',
      description: '分析新闻、公告与行业事件影响'
    },
    social: {
      title: '💬 社交媒体分析师',
      description: '分析股吧、舆情与市场情绪变化'
    }
  }

  const steps: Array<{ title: string; description: string }> = [
    {
      title: '📋 准备阶段',
      description: '验证股票代码并初始化分析引擎'
    }
  ]

  submittedAnalystIds.value.forEach((analystId) => {
    const step = analystStepMap[analystId]
    if (step) {
      steps.push(step)
    }
  })

  steps.push(
    {
      title: '🐂 看涨研究员',
      description: '基于分析师报告构建看多论据'
    },
    {
      title: '🐻 看跌研究员',
      description: '识别潜在风险并构建看空论据'
    }
  )

  for (let index = 0; index < getDebateRounds(researchDepth); index += 1) {
    steps.push({
      title: `🎯 研究辩论 第${index + 1}轮`,
      description: '多空研究员围绕核心观点进行辩论'
    })
  }

  steps.push(
    {
      title: '👔 研究经理',
      description: '整合研究结论，形成团队共识'
    },
    {
      title: '💼 交易员决策',
      description: '根据研究结论制定交易策略'
    }
  )

  if (includeRisk) {
    steps.push(
      {
        title: '🔥 激进风险评估',
        description: '从激进视角评估风险与收益弹性'
      },
      {
        title: '🛡️ 保守风险评估',
        description: '从保守视角评估下行保护与风险暴露'
      },
      {
        title: '⚖️ 中性风险评估',
        description: '从平衡视角评估风险收益配比'
      },
      {
        title: '🎯 风险经理',
        description: '汇总风险辩论并给出最终风控意见'
      }
    )
  }

  steps.push(
    {
      title: '📡 信号处理',
      description: '汇总多智能体输出并生成最终信号'
    },
    {
      title: '📊 生成报告',
      description: '整理结论并生成完整分析报告'
    }
  )

  return steps
}

const normalizeStepTitle = (value: string) =>
  String(value || '')
    .replace(/正在分析|构建论据|识别风险|形成共识|制定策略/g, '')
    .trim()

const executionSteps = computed(() => {
  const rawSteps = Array.isArray(taskData.value?.steps) && taskData.value.steps.length
    ? taskData.value.steps.map((step: any) => ({
        title: step.name || step.title || '',
        description: step.description || '',
        rawStatus: step.status || 'pending'
      }))
    : buildDerivedExecutionSteps().map((step) => ({
        ...step,
        rawStatus: 'pending'
      }))

  const currentStepName = normalizeStepTitle(
    taskData.value?.current_step_name ||
    taskData.value?.current_step ||
    taskData.value?.message ||
    ''
  )

  return rawSteps.map((step) => {
    const normalizedTitle = normalizeStepTitle(step.title)
    let status = 'pending'

    if (step.rawStatus === 'completed') {
      status = 'completed'
    } else if (['in_progress', 'current', 'active'].includes(step.rawStatus)) {
      status = 'current'
    }

    if (
      currentStepName &&
      (normalizedTitle === currentStepName || currentStepName.includes(normalizedTitle))
    ) {
      status = 'current'
    }

    return {
      title: step.title,
      description: step.description,
      status
    }
  })
})

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

  .summary-card {
    margin-bottom: 20px;
  }

  .left-column,
  .right-column {
    display: flex;
    flex-direction: column;
  }

  .align-stretch {
    align-items: stretch;
  }

  .full-height-card {
    height: 100%;
  }

  .detail-row {
    margin-bottom: 12px;
  }

  .detail-row > .el-col > :deep(*) {
    margin-bottom: 0 !important;
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

  .graph-section + .graph-section {
    margin-top: 16px;
  }

  .graph-label {
    margin-bottom: 8px;
    color: var(--el-text-color-secondary);
    font-size: 13px;
    font-weight: 600;
  }

  .submitted-analysts {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .graph-empty {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }

  .execution-flow {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .execution-flow.horizontal {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    align-items: stretch;
    gap: 10px;
    overflow: visible;
    padding-bottom: 0;
  }

  .flow-step {
    display: flex;
    flex-direction: column;
    padding: 10px 12px;
    border: 1px solid #ebeef5;
    border-radius: 12px;
    background: #fff;
  }

  .execution-flow.horizontal .flow-step {
    position: relative;
    min-height: 90px;
  }

  .flow-step.completed {
    border-color: #b7eb8f;
    background: #f6ffed;
  }

  .flow-step.current {
    border-color: #91caff;
    background: #e6f4ff;
    box-shadow: 0 0 0 1px rgba(24, 144, 255, 0.12);
  }

  .flow-title {
    color: var(--el-text-color-primary);
    font-size: 14px;
    font-weight: 600;
  }

  .flow-desc {
    margin-top: 4px;
    color: var(--el-text-color-secondary);
    font-size: 12px;
    line-height: 1.45;
  }

  .flow-connector {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: auto;
    padding-top: 10px;
  }

  .flow-connector-line {
    flex: 1;
    height: 2px;
    border-radius: 999px;
    background: #dcdfe6;
  }

  .flow-connector.completed .flow-connector-line {
    background: #95de64;
  }

  .flow-connector.current .flow-connector-line {
    background: #409eff;
  }

  .flow-arrow {
    text-align: center;
    color: var(--el-text-color-secondary);
    font-size: 16px;
  }

  .flow-arrow.horizontal {
    display: inline-flex;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: 1px solid #e5e7eb;
    border-radius: 999px;
    background: #fff;
    color: var(--el-text-color-secondary);
    line-height: 1;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
  }

  .flow-connector.completed .flow-arrow.horizontal {
    border-color: #95de64;
    color: #52c41a;
    background: #f6ffed;
  }

  .flow-connector.current .flow-arrow.horizontal {
    border-color: #409eff;
    color: #1677ff;
    background: #e6f4ff;
    box-shadow: 0 4px 12px rgba(22, 119, 255, 0.18);
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

    .execution-flow.horizontal {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }

  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
    }

    .summary-grid {
      grid-template-columns: 1fr;
    }

    .execution-flow.horizontal {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .full-height-card {
      height: auto;
    }
  }

  @media (max-width: 520px) {
    .execution-flow.horizontal {
      grid-template-columns: 1fr;
    }
  }
}
</style>
