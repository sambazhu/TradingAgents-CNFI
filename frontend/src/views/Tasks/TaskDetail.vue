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
            <div class="graph-section-header">
              <div class="graph-label">真实 LangGraph 节点图</div>
              <div class="graph-helper">{{ actualGraphNodeCount }} 个节点，不含 START / END</div>
            </div>
            <div class="langgraph-board">
              <div class="graph-banner">
                <span class="graph-banner-chip">{{ langGraphBannerText }}</span>
                <span class="graph-banner-text">{{ langGraphBannerSubtext }}</span>
              </div>

              <div class="graph-lane">
                <div class="graph-lane-title">分析师主链</div>
                <div class="graph-node-row">
                  <span :class="getGraphNodeClasses('START', 'endpoint')">START</span>
                  <template v-for="node in actualGraphPrimaryFlow" :key="node.key">
                    <span class="graph-arrow">→</span>
                    <span :class="getGraphNodeClasses(node.nodeName, node.tone)">{{ node.label }}</span>
                  </template>
                </div>
              </div>

              <div v-if="actualGraphToolLoops.length" class="graph-lane">
                <div class="graph-lane-title">工具循环</div>
                <div class="graph-tool-grid">
                  <div v-for="item in actualGraphToolLoops" :key="item.key" class="graph-tool-item">
                    <span :class="getGraphNodeClasses(item.analystNode, 'analyst')">{{ item.analystNode }}</span>
                    <span class="graph-arrow loop">↔</span>
                    <span :class="getGraphNodeClasses(item.toolNode, 'tool')">{{ item.toolNode }}</span>
                  </div>
                </div>
              </div>

              <div class="graph-lane">
                <div class="graph-lane-title">研究辩论</div>
                <div class="graph-node-row">
                  <span :class="getGraphNodeClasses('Bull Researcher', 'research')">Bull Researcher</span>
                  <span class="graph-arrow loop">↔</span>
                  <span :class="getGraphNodeClasses('Bear Researcher', 'research')">Bear Researcher</span>
                  <span class="graph-arrow">→</span>
                  <span :class="getGraphNodeClasses('Research Manager', 'manager')">Research Manager</span>
                  <span class="graph-arrow">→</span>
                  <span :class="getGraphNodeClasses('Trader', 'manager')">Trader</span>
                </div>
                <div class="graph-note">条件边：Bull / Bear 会按辩论轮次在两者之间往返，满足条件后流向 Research Manager。</div>
              </div>

              <div v-if="includeRiskEnabled" class="graph-lane">
                <div class="graph-lane-title">风险控制</div>
                <div class="graph-node-row">
                  <span :class="getGraphNodeClasses('Trader', 'manager')">Trader</span>
                  <span class="graph-arrow">→</span>
                  <span :class="getGraphNodeClasses('Risky Analyst', 'risk')">Risky Analyst</span>
                  <span class="graph-arrow">→</span>
                  <span :class="getGraphNodeClasses('Safe Analyst', 'risk')">Safe Analyst</span>
                  <span class="graph-arrow">→</span>
                  <span :class="getGraphNodeClasses('Neutral Analyst', 'risk')">Neutral Analyst</span>
                  <span class="graph-arrow">→</span>
                  <span :class="getGraphNodeClasses('Risk Judge', 'manager')">Risk Judge</span>
                  <span class="graph-arrow">→</span>
                  <span :class="getGraphNodeClasses('END', 'endpoint')">END</span>
                </div>
                <div class="graph-note">条件边：Risky / Safe / Neutral 达到讨论上限后都可直接进入 Risk Judge；Neutral Analyst 也可回到 Risky Analyst 继续循环。</div>
              </div>

              <div v-else class="graph-lane">
                <div class="graph-lane-title">图终点</div>
                <div class="graph-node-row">
                  <span :class="getGraphNodeClasses('Trader', 'manager')">Trader</span>
                  <span class="graph-arrow">→</span>
                  <span :class="getGraphNodeClasses('END', 'endpoint')">END</span>
                </div>
              </div>
            </div>
          </div>

          <div class="graph-section">
            <div class="graph-section-header">
              <div class="graph-label">产品执行进度</div>
              <div class="graph-helper">{{ executionSteps.length }} 步，来自后端 Progress Tracker</div>
            </div>
            <div v-if="executionSteps.length" class="progress-chain-board">
              <div class="graph-banner">
                <span class="graph-banner-chip">{{ progressBannerText }}</span>
                <span class="graph-banner-text">{{ progressBannerSubtext }}</span>
              </div>

              <div class="progress-step-grid">
                <div
                  v-for="(step, index) in executionSteps"
                  :key="`${step.title}-${index}`"
                  :class="['progress-step-card', step.status]"
                >
                  <div class="progress-step-index">{{ index + 1 }}</div>
                  <div class="progress-step-title">{{ step.title }}</div>
                  <div class="progress-step-desc">{{ step.description }}</div>
                </div>
              </div>
            </div>
            <div v-else class="graph-empty">暂无进度步骤</div>
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

type StepStatus = 'pending' | 'completed' | 'current'
type ExecutionStep = {
  title: string
  description: string
  status: StepStatus
}
type RawExecutionStep = {
  title: string
  description: string
  rawStatus: string
}
type GraphTone = 'endpoint' | 'analyst' | 'tool' | 'system' | 'research' | 'manager' | 'risk'

const ANALYST_GRAPH_META: Record<string, { analyst: string; tool: string; clear: string }> = {
  market: {
    analyst: 'Market Analyst',
    tool: 'tools_market',
    clear: 'Msg Clear Market'
  },
  fundamentals: {
    analyst: 'Fundamentals Analyst',
    tool: 'tools_fundamentals',
    clear: 'Msg Clear Fundamentals'
  },
  news: {
    analyst: 'News Analyst',
    tool: 'tools_news',
    clear: 'Msg Clear News'
  },
  social: {
    analyst: 'Social Analyst',
    tool: 'tools_social',
    clear: 'Msg Clear Social'
  }
}

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
const includeRiskEnabled = computed(() => (taskData.value?.parameters || {}).include_risk !== false)

const getDebateRounds = (researchDepth: string) => {
  if (['快速', '基础', '标准'].includes(researchDepth)) return 1
  if (researchDepth === '深度') return 2
  if (researchDepth === '全面') return 3
  return 1
}

const buildDerivedExecutionSteps = (): Array<Omit<ExecutionStep, 'status'>> => {
  const parameters = taskData.value?.parameters || {}
  const researchDepth = parameters.research_depth || taskData.value?.research_depth || '标准'
  const includeRisk = parameters.include_risk !== false
  const analystStepMap: Record<string, { title: string; description: string }> = {
    market: {
      title: '📊 市场分析师',
      description: '分析股价走势、成交量、技术指标等市场表现'
    },
    fundamentals: {
      title: '💼 基本面分析师',
      description: '分析公司财务状况、盈利能力、成长性等基本面'
    },
    news: {
      title: '📰 新闻分析师',
      description: '分析相关新闻、公告、行业动态对股价的影响'
    },
    social: {
      title: '💬 社交媒体分析师',
      description: '分析社交媒体讨论、网络热度、散户情绪等'
    }
  }

  const steps: Array<Omit<ExecutionStep, 'status'>> = [
    { title: '📋 准备阶段', description: '验证股票代码，检查数据源可用性' },
    { title: '🔧 环境检查', description: '检查API密钥配置，确保数据获取正常' },
    { title: '💰 成本估算', description: '根据分析深度预估API调用成本' },
    { title: '⚙️ 参数设置', description: '配置分析参数和AI模型选择' },
    { title: '🚀 启动引擎', description: '初始化AI分析引擎，准备开始分析' }
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
      description: '基于分析师报告构建买入论据'
    },
    {
      title: '🐻 看跌研究员',
      description: '识别潜在风险和问题'
    }
  )

  for (let index = 0; index < getDebateRounds(researchDepth); index += 1) {
    steps.push({
      title: `🎯 研究辩论 第${index + 1}轮`,
      description: '多头空头研究员深度辩论'
    })
  }

  steps.push(
    {
      title: '👔 研究经理',
      description: '综合辩论结果，形成研究共识'
    },
    {
      title: '💼 交易员决策',
      description: '基于研究结果制定具体交易策略'
    }
  )

  if (includeRisk) {
    steps.push(
      {
        title: '🔥 激进风险评估',
        description: '从激进角度评估投资风险'
      },
      {
        title: '🛡️ 保守风险评估',
        description: '从保守角度评估投资风险'
      },
      {
        title: '⚖️ 中性风险评估',
        description: '从中性角度评估投资风险'
      },
      {
        title: '🎯 风险经理',
        description: '综合风险评估，制定风险控制策略'
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
  const rawSteps: RawExecutionStep[] = Array.isArray(taskData.value?.steps) && taskData.value.steps.length
    ? taskData.value.steps.map((step: any) => ({
        title: step.name || step.title || '',
        description: step.description || '',
        rawStatus: step.status || 'pending'
      }))
    : buildDerivedExecutionSteps().map((step): RawExecutionStep => ({
        ...step,
        rawStatus: 'pending'
      }))

  const currentStepName = normalizeStepTitle(
    taskData.value?.current_step_name ||
    taskData.value?.current_step ||
    taskData.value?.message ||
    ''
  )

  const explicitCurrentIndex = rawSteps.findIndex((step: RawExecutionStep) => {
    const normalizedTitle = normalizeStepTitle(step.title)
    if (!currentStepName || !normalizedTitle) return false
    return normalizedTitle === currentStepName || currentStepName.includes(normalizedTitle)
  })

  return rawSteps.map((step: RawExecutionStep, index: number): ExecutionStep => {
    let status: StepStatus = 'pending'

    if (normalizedStatus.value === 'completed' && step.rawStatus !== 'failed') {
      status = 'completed'
    } else if (explicitCurrentIndex >= 0) {
      if (index < explicitCurrentIndex) {
        status = 'completed'
      } else if (index === explicitCurrentIndex) {
        status = 'current'
      }
    } else if (step.rawStatus === 'completed') {
      status = 'completed'
    } else if (['in_progress', 'current', 'active'].includes(step.rawStatus)) {
      status = 'current'
    }

    return {
      title: step.title,
      description: step.description,
      status
    }
  })
})

const progressCurrentIndex = computed(() =>
  executionSteps.value.findIndex((step: ExecutionStep) => step.status === 'current')
)

const progressLastCompletedIndex = computed(() => {
  for (let index = executionSteps.value.length - 1; index >= 0; index -= 1) {
    if (executionSteps.value[index].status === 'completed') return index
  }
  return -1
})

const progressBannerText = computed(() => {
  if (progressCurrentIndex.value >= 0) {
    return `当前执行到第 ${progressCurrentIndex.value + 1} / ${executionSteps.value.length} 步`
  }
  if (normalizedStatus.value === 'completed') {
    return `已完成，共 ${executionSteps.value.length} 步`
  }
  if (progressLastCompletedIndex.value >= 0) {
    return `已执行到第 ${progressLastCompletedIndex.value + 1} / ${executionSteps.value.length} 步`
  }
  return '等待执行'
})

const progressBannerSubtext = computed(() => {
  if (progressCurrentIndex.value >= 0) {
    return `命中步骤：${executionSteps.value[progressCurrentIndex.value].title}`
  }
  if (normalizedStatus.value === 'completed' && executionSteps.value.length) {
    return `最后步骤：${executionSteps.value[executionSteps.value.length - 1].title}`
  }
  if (progressLastCompletedIndex.value >= 0) {
    return `最近完成：${executionSteps.value[progressLastCompletedIndex.value].title}`
  }
  return '命中步骤：尚未进入执行阶段'
})

const actualGraphAnalystItems = computed(() =>
  submittedAnalystIds.value
    .map((id) => {
      const meta = ANALYST_GRAPH_META[id]
      return meta
        ? {
            key: id,
            analystNode: meta.analyst,
            toolNode: meta.tool,
            clearNode: meta.clear
          }
        : null
    })
    .filter(Boolean) as Array<{ key: string; analystNode: string; toolNode: string; clearNode: string }>
)

const actualGraphPrimaryFlow = computed(() => {
  const items: Array<{ key: string; label: string; nodeName: string; tone: GraphTone }> = []

  actualGraphAnalystItems.value.forEach((item) => {
    items.push(
      {
        key: `${item.key}-analyst`,
        label: item.analystNode,
        nodeName: item.analystNode,
        tone: 'analyst'
      },
      {
        key: `${item.key}-clear`,
        label: item.clearNode,
        nodeName: item.clearNode,
        tone: 'system'
      }
    )
  })

  items.push({
    key: 'bull-entry',
    label: 'Bull Researcher',
    nodeName: 'Bull Researcher',
    tone: 'research'
  })

  return items
})

const actualGraphToolLoops = computed(() =>
  actualGraphAnalystItems.value.map((item) => ({
    key: `${item.key}-tool-loop`,
    analystNode: item.analystNode,
    toolNode: item.toolNode
  }))
)

const actualGraphNodeCount = computed(() => {
  const analystNodeCount = actualGraphAnalystItems.value.length * 3
  const baseNodeCount = 4
  const riskNodeCount = includeRiskEnabled.value ? 4 : 0
  return analystNodeCount + baseNodeCount + riskNodeCount
})

const getGraphNodesForProgressTitle = (title: string): string[] => {
  const value = normalizeStepTitle(title)

  if (['准备阶段', '环境检查', '成本估算', '参数设置', '启动引擎'].some((item) => value.includes(item))) {
    return ['START']
  }
  if (value.includes('市场分析师')) {
    const meta = ANALYST_GRAPH_META.market
    return [meta.analyst, meta.tool, meta.clear]
  }
  if (value.includes('基本面分析师')) {
    const meta = ANALYST_GRAPH_META.fundamentals
    return [meta.analyst, meta.tool, meta.clear]
  }
  if (value.includes('新闻分析师')) {
    const meta = ANALYST_GRAPH_META.news
    return [meta.analyst, meta.tool, meta.clear]
  }
  if (value.includes('社交媒体分析师')) {
    const meta = ANALYST_GRAPH_META.social
    return [meta.analyst, meta.tool, meta.clear]
  }
  if (value.includes('看涨研究员')) return ['Bull Researcher']
  if (value.includes('看跌研究员')) return ['Bear Researcher']
  if (value.includes('研究辩论')) return ['Bull Researcher', 'Bear Researcher']
  if (value.includes('研究经理')) return ['Research Manager']
  if (value.includes('交易员决策')) return ['Trader']
  if (value.includes('激进风险评估')) return ['Risky Analyst']
  if (value.includes('保守风险评估')) return ['Safe Analyst']
  if (value.includes('中性风险评估')) return ['Neutral Analyst']
  if (value.includes('风险经理')) return ['Risk Judge']
  if (['信号处理', '生成报告', '分析完成'].some((item) => value.includes(item))) return ['END']
  return []
}

const allLangGraphNodeNames = computed(() => {
  const names = new Set<string>(['START'])
  actualGraphAnalystItems.value.forEach((item) => {
    names.add(item.analystNode)
    names.add(item.toolNode)
    names.add(item.clearNode)
  })
  names.add('Bull Researcher')
  names.add('Bear Researcher')
  names.add('Research Manager')
  names.add('Trader')
  if (includeRiskEnabled.value) {
    names.add('Risky Analyst')
    names.add('Safe Analyst')
    names.add('Neutral Analyst')
    names.add('Risk Judge')
  }
  names.add('END')
  return Array.from(names)
})

const langGraphNodeStates = computed<Record<string, StepStatus>>(() => {
  const states = Object.fromEntries(
    allLangGraphNodeNames.value.map((name) => [name, 'pending' as StepStatus])
  )

  if (executionSteps.value.length || normalizedStatus.value !== 'pending') {
    states.START = 'completed'
  }

  executionSteps.value.forEach((step: ExecutionStep) => {
    const nodeNames = getGraphNodesForProgressTitle(step.title)
    nodeNames.forEach((nodeName) => {
      if (step.status === 'completed') {
        states[nodeName] = 'completed'
      } else if (step.status === 'current') {
        states[nodeName] = 'current'
      }
    })
  })

  if (normalizedStatus.value === 'completed') {
    allLangGraphNodeNames.value.forEach((name) => {
      states[name] = 'completed'
    })
    states.END = 'completed'
  }

  return states
})

const langGraphBannerText = computed(() => {
  return `真实节点 ${actualGraphNodeCount.value} 个，产品步骤 ${executionSteps.value.length} 步`
})

const langGraphBannerSubtext = computed(() => {
  if (normalizedStatus.value === 'completed') {
    return '当前任务已完成，所有真实 LangGraph 节点均已收口'
  }

  if (progressCurrentIndex.value >= 0) {
    const graphNodes = getGraphNodesForProgressTitle(executionSteps.value[progressCurrentIndex.value].title)
    return graphNodes.length
      ? `当前语义步骤映射到：${graphNodes.join(' / ')}`
      : '当前步骤属于图外收尾阶段（如信号处理/生成报告）'
  }

  return '上方显示真实 LangGraph 节点，下方显示后端 Progress Tracker 的产品步骤'
})

const getGraphNodeClasses = (nodeName: string, tone: GraphTone) => [
  'graph-node',
  `tone-${tone}`,
  `status-${langGraphNodeStates.value[nodeName] || 'pending'}`
]

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

  .graph-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
  }

  .graph-helper {
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }

  .langgraph-board,
  .progress-chain-board {
    padding: 16px;
    border: 1px solid #ebeef5;
    border-radius: 16px;
    background:
      radial-gradient(circle at 1px 1px, rgba(148, 163, 184, 0.18) 1px, transparent 0),
      linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    background-size: 18px 18px, auto;
  }

  .graph-banner {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 14px;
  }

  .graph-banner-chip,
  .graph-banner-text {
    display: inline-flex;
    align-items: center;
    min-height: 32px;
    padding: 0 12px;
    border-radius: 999px;
    border: 1px solid rgba(148, 163, 184, 0.2);
    background: rgba(255, 255, 255, 0.92);
    color: var(--el-text-color-primary);
    font-size: 12px;
    box-shadow: 0 4px 10px rgba(15, 23, 42, 0.04);
  }

  .graph-banner-chip {
    color: #1677ff;
    border-color: rgba(64, 158, 255, 0.28);
    background: rgba(230, 244, 255, 0.96);
    font-weight: 700;
  }

  .graph-lane + .graph-lane {
    margin-top: 14px;
  }

  .graph-lane-title {
    margin-bottom: 8px;
    color: #475569;
    font-size: 12px;
    font-weight: 700;
  }

  .graph-node-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .graph-tool-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .graph-tool-item {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    flex-wrap: wrap;
  }

  .graph-node {
    display: inline-flex;
    align-items: center;
    min-height: 34px;
    padding: 0 12px;
    border-radius: 12px;
    border: 1px solid #dbe4ee;
    background: rgba(255, 255, 255, 0.96);
    color: #334155;
    font-size: 12px;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
  }

  .graph-node.tone-endpoint,
  .graph-node.tone-system,
  .graph-node.tone-tool {
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 11px;
  }

  .graph-node.tone-tool {
    background: #f8fafc;
  }

  .graph-node.status-completed {
    border-color: #b7eb8f;
    background: #f6ffed;
    color: #3f8600;
  }

  .graph-node.status-current {
    border-color: #91caff;
    background: #e6f4ff;
    color: #0958d9;
    box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.18);
  }

  .graph-arrow {
    color: #94a3b8;
    font-size: 15px;
    font-weight: 700;
    line-height: 1;
  }

  .graph-arrow.loop {
    color: #64748b;
  }

  .graph-note {
    margin-top: 8px;
    color: #64748b;
    font-size: 12px;
    line-height: 1.5;
  }

  .progress-step-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
  }

  .progress-step-card {
    min-height: 112px;
    padding: 12px 13px;
    border: 1px solid #ebeef5;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
  }

  .progress-step-card.completed {
    border-color: #b7eb8f;
    background: #f6ffed;
  }

  .progress-step-card.current {
    border-color: #91caff;
    background: #e6f4ff;
    box-shadow:
      0 0 0 1px rgba(24, 144, 255, 0.12),
      0 10px 24px rgba(22, 119, 255, 0.12);
  }

  .progress-step-index {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 999px;
    background: #f1f5f9;
    color: #475569;
    font-size: 11px;
    font-weight: 700;
  }

  .progress-step-card.completed .progress-step-index {
    background: #dcfce7;
    color: #15803d;
  }

  .progress-step-card.current .progress-step-index {
    background: #dbeafe;
    color: #1d4ed8;
  }

  .progress-step-title {
    margin-top: 8px;
    color: var(--el-text-color-primary);
    font-size: 14px;
    font-weight: 600;
    line-height: 1.35;
  }

  .progress-step-desc {
    margin-top: 6px;
    color: var(--el-text-color-secondary);
    font-size: 12px;
    line-height: 1.5;
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

    .progress-step-grid {
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

    .graph-tool-grid {
      grid-template-columns: 1fr;
    }

    .progress-step-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .full-height-card {
      height: auto;
    }
  }

  @media (max-width: 520px) {
    .progress-step-grid {
      grid-template-columns: 1fr;
    }
  }
}
</style>
