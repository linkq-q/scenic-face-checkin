<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { createTicket, listTickets } from '../api/index.js'

const createForm = reactive({ visitor_id: '', scenic_name: '', visit_date: '' })
const createRules = {
  visitor_id: [{ required: true, message: '请输入游客ID', trigger: 'blur' }],
  scenic_name: [{ required: true, message: '请输入景区名称', trigger: 'blur' }],
  visit_date: [{ required: true, message: '请选择游览日期', trigger: 'change' }],
}
const createFormRef = ref(null)
const creating = ref(false)

const filterForm = reactive({ visitor_id: '', status: '' })
const tickets = ref([])
const tableLoading = ref(false)

async function handleCreate() {
  await createFormRef.value.validate()
  creating.value = true
  try {
    await createTicket({
      visitor_id: Number(createForm.visitor_id),
      scenic_name: createForm.scenic_name,
      visit_date: createForm.visit_date,
    })
    ElMessage.success('门票创建成功')
    createFormRef.value.resetFields()
    loadTickets()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function loadTickets() {
  tableLoading.value = true
  try {
    const params = {}
    if (filterForm.visitor_id) params.visitor_id = Number(filterForm.visitor_id)
    if (filterForm.status) params.status = filterForm.status
    const { data } = await listTickets(params)
    tickets.value = data
  } catch {
    ElMessage.error('查询失败')
  } finally {
    tableLoading.value = false
  }
}

const statusMap = { unused: '未使用', used: '已使用', expired: '已过期' }
const statusType = { unused: 'success', used: 'info', expired: 'danger' }

onMounted(loadTickets)
</script>

<template>
  <el-row :gutter="24">
    <!-- 创建表单 -->
    <el-col :span="10">
      <el-card>
        <template #header><span>创建门票</span></template>
        <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="90px">
          <el-form-item label="游客 ID" prop="visitor_id">
            <el-input v-model="createForm.visitor_id" placeholder="注册后的游客 ID" />
          </el-form-item>
          <el-form-item label="景区名称" prop="scenic_name">
            <el-input v-model="createForm.scenic_name" placeholder="如：黄山风景区" />
          </el-form-item>
          <el-form-item label="游览日期" prop="visit_date">
            <el-date-picker
              v-model="createForm.visit_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择日期"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="handleCreate">
              创建
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>

    <!-- 门票列表 -->
    <el-col :span="14">
      <el-card>
        <template #header>
          <div style="display: flex; align-items: center; gap: 12px">
            <span>门票列表</span>
            <el-input v-model="filterForm.visitor_id" placeholder="游客ID筛选" style="width: 130px" clearable />
            <el-select v-model="filterForm.status" placeholder="状态" style="width: 110px" clearable>
              <el-option label="未使用" value="unused" />
              <el-option label="已使用" value="used" />
              <el-option label="已过期" value="expired" />
            </el-select>
            <el-button type="primary" plain @click="loadTickets">查询</el-button>
          </div>
        </template>
        <el-table :data="tickets" v-loading="tableLoading" stripe>
          <el-table-column label="ID" prop="ticket_id" width="70" />
          <el-table-column label="游客ID" prop="visitor_id" width="80" />
          <el-table-column label="景区" prop="scenic_name" min-width="120" show-overflow-tooltip />
          <el-table-column label="游览日期" prop="visit_date" width="115" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusType[row.status]" size="small">
                {{ statusMap[row.status] }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!tickets.length && !tableLoading" description="暂无数据" />
      </el-card>
    </el-col>
  </el-row>
</template>
