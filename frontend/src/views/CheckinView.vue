<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { verifyCheckin } from '../api/index.js'

const fileList = ref([])
const previewUrl = ref('')
const gateId = ref('')
const loading = ref(false)
const result = ref(null)

function beforeUpload() { return false }

function handleChange(file) {
  if (!file.raw.type.startsWith('image/')) {
    ElMessage.error('请上传图片文件')
    return false
  }
  const reader = new FileReader()
  reader.onload = e => { previewUrl.value = e.target.result }
  reader.readAsDataURL(file.raw)
  fileList.value = [file]
  result.value = null
}

async function handleVerify() {
  if (!fileList.value.length) {
    ElMessage.warning('请先上传人脸照片')
    return
  }
  loading.value = true
  result.value = null
  try {
    const fd = new FormData()
    fd.append('face_image', fileList.value[0].raw)
    if (gateId.value) fd.append('gate_id', gateId.value)
    const { data } = await verifyCheckin(fd)
    result.value = data
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '核销请求失败')
  } finally {
    loading.value = false
  }
}

const reasonMap = {
  no_face: '图片中未检测到人脸，请重新上传清晰正面照',
  no_match: '未找到匹配的游客，请先完成注册',
  no_valid_ticket: '该游客今日无有效门票',
  already_used: '该游客今日门票已核销，请勿重复入园',
}
</script>

<template>
  <el-row :gutter="24">
    <!-- 操作区 -->
    <el-col :span="12">
      <el-card>
        <template #header><span>上传人脸照片</span></template>
        <el-upload
          drag
          :file-list="fileList"
          :before-upload="beforeUpload"
          :on-change="handleChange"
          :limit="1"
          accept="image/*"
          style="margin-bottom: 16px"
        >
          <el-icon size="48" style="color: #c0c4cc"><UploadFilled /></el-icon>
          <div style="font-size: 16px; margin-top: 8px">拖拽或点击上传照片</div>
          <template #tip>
            <div class="el-upload__tip">支持 jpg / png 格式</div>
          </template>
        </el-upload>

        <el-input
          v-model="gateId"
          placeholder="闸机编号（可选，如 GATE-01）"
          clearable
          style="margin-bottom: 16px"
        >
          <template #prepend>闸机</template>
        </el-input>

        <el-button
          type="primary"
          size="large"
          style="width: 100%"
          :loading="loading"
          @click="handleVerify"
        >
          开始核销
        </el-button>
      </el-card>
    </el-col>

    <!-- 预览 & 结果 -->
    <el-col :span="12">
      <el-card v-if="previewUrl" style="margin-bottom: 16px">
        <template #header><span>照片预览</span></template>
        <img :src="previewUrl" style="width: 100%; max-height: 260px; object-fit: contain; border-radius: 4px" />
      </el-card>

      <el-card v-if="result">
        <template #header><span>核销结果</span></template>
        <div v-if="result.success" class="success-card">
          <el-icon size="56" color="#67c23a"><CircleCheckFilled /></el-icon>
          <h3 style="font-size: 22px; margin: 12px 0 4px">核销成功</h3>
          <p class="info-row"><span>游客姓名</span><strong>{{ result.visitor_name }}</strong></p>
          <p class="info-row"><span>门票编号</span><strong>#{{ result.ticket_id }}</strong></p>
          <p class="info-row"><span>匹配度</span><strong>{{ (result.score * 100).toFixed(1) }}%</strong></p>
          <p class="info-row"><span>核销时间</span><strong>{{ result.checked_at?.replace('T', ' ') }}</strong></p>
        </div>
        <div v-else class="fail-card">
          <el-icon size="56" color="#f56c6c"><CircleCloseFilled /></el-icon>
          <h3 style="font-size: 20px; margin: 12px 0 4px">核销失败</h3>
          <p style="color: #909399">{{ reasonMap[result.reason] || result.reason }}</p>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<style scoped>
.success-card, .fail-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  text-align: center;
}
.info-row {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin: 6px 0;
  font-size: 15px;
  color: #606266;
}
.info-row strong { color: #303133; }
</style>
