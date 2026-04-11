<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { registerVisitor } from '../api/index.js'

const form = reactive({ name: '', phone: '' })
const fileList = ref([])
const previewUrl = ref('')
const loading = ref(false)
const result = ref(null)

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
}

const formRef = ref(null)

// 本地预览
function handleChange(file) {
  const isImage = file.raw.type.startsWith('image/')
  const isLt5M = file.raw.size / 1024 / 1024 < 5
  if (!isImage) { ElMessage.error('只能上传图片文件'); return false }
  if (!isLt5M) { ElMessage.error('图片大小不能超过 5MB'); return false }
  const reader = new FileReader()
  reader.onload = e => { previewUrl.value = e.target.result }
  reader.readAsDataURL(file.raw)
  fileList.value = [file]
}

function beforeUpload() {
  return false // 阻止 el-upload 自动上传，手动提交
}

async function handleSubmit() {
  await formRef.value.validate()
  if (!fileList.value.length) {
    ElMessage.warning('请上传人脸照片')
    return
  }
  loading.value = true
  result.value = null
  try {
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('phone', form.phone)
    fd.append('face_image', fileList.value[0].raw)
    const { data } = await registerVisitor(fd)
    result.value = { success: true, ...data }
    ElMessage.success('注册成功')
    formRef.value.resetFields()
    fileList.value = []
    previewUrl.value = ''
  } catch (err) {
    const detail = err.response?.data?.detail || '注册失败，请重试'
    result.value = { success: false, message: detail }
    ElMessage.error(detail)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-row :gutter="24">
    <!-- 表单区 -->
    <el-col :span="14">
      <el-card>
        <template #header>
          <span>游客信息录入</span>
        </template>
        <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
          <el-form-item label="姓名" prop="name">
            <el-input v-model="form.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="人脸照片">
            <el-upload
              :file-list="fileList"
              :before-upload="beforeUpload"
              :on-change="handleChange"
              :limit="1"
              accept="image/jpeg,image/png"
              list-type="picture-card"
            >
              <el-icon><Plus /></el-icon>
              <template #tip>
                <div class="el-upload__tip">仅支持 jpg/png，不超过 5MB</div>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="handleSubmit">
              提交注册
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>

    <!-- 预览 & 结果区 -->
    <el-col :span="10">
      <el-card v-if="previewUrl" style="margin-bottom: 16px">
        <template #header><span>照片预览</span></template>
        <img :src="previewUrl" style="width: 100%; max-height: 280px; object-fit: contain; border-radius: 4px" />
      </el-card>

      <el-card v-if="result">
        <template #header><span>注册结果</span></template>
        <el-result
          v-if="result.success"
          icon="success"
          title="注册成功"
          :sub-title="`游客 ID：${result.visitor_id}　姓名：${result.name}`"
        />
        <el-result
          v-else
          icon="error"
          title="注册失败"
          :sub-title="result.message"
        />
      </el-card>
    </el-col>
  </el-row>
</template>
