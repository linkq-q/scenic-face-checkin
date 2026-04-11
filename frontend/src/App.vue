<script setup>
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<template>
  <el-container style="height: 100vh">
    <!-- 侧边栏 -->
    <el-aside width="220px" style="background: #001529; overflow: hidden">
      <div class="logo">
        <el-icon size="22"><Camera /></el-icon>
        <span>景区核销系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#001529"
        text-color="#ffffffa0"
        active-text-color="#ffffff"
        router
      >
        <el-menu-item index="/register">
          <el-icon><UserFilled /></el-icon>
          <span>游客注册</span>
        </el-menu-item>
        <el-menu-item index="/tickets">
          <el-icon><Ticket /></el-icon>
          <span>门票管理</span>
        </el-menu-item>
        <el-menu-item index="/checkin">
          <el-icon><Scan /></el-icon>
          <span>入园核销</span>
        </el-menu-item>
        <el-menu-item index="/stats">
          <el-icon><DataLine /></el-icon>
          <span>客流统计</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container direction="vertical">
      <el-header style="background: #fff; border-bottom: 1px solid #e6e6e6; display: flex; align-items: center; padding: 0 24px">
        <h2 style="font-size: 18px; font-weight: 600; color: #303133">
          {{ route.meta.title || '景区核销系统' }}
        </h2>
      </el-header>
      <el-main style="padding: 24px; overflow-y: auto">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #ffffff15;
}
</style>
