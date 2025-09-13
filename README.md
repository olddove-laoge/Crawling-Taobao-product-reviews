# 淘宝商品评价采集工具文档

## 📌 概述
本工具基于Selenium实现，专门用于自动化采集淘宝商品详情页的用户评价数据。通过模拟浏览器操作实现安全登录、智能加载、反检测等机制，支持持久化登录状态和断点续采功能。

## 🚀 核心功能

### 1. 登录管理模块
- **混合认证模式**：支持扫码登录+Cookie持久化双重认证
- **状态智能检测**：自动验证登录状态有效性
- **凭证缓存机制**：`taobao_cookies.pkl`存储登录凭证

### 2. 数据采集模块
- **智能滚动加载**：自动触发评价内容的分页加载
- **动态元素定位**：使用CSS选择器精准定位评价元素
- **容错采集机制**：自动处理网络波动和元素加载异常

### 3. 防检测机制
- 用户数据目录隔离(`taobao_bot_profile`)
- 屏蔽自动化控制特征
- 模拟人类操作间隔

## ✨ 主要特点

- **跨会话状态保持**  
  通过`user-data-dir`保留浏览器指纹，维持长期登录状态

- **智能加载策略**  
  动态计算滚动距离，自动检测新内容加载状态

- **弹性重试机制**  
  三级容错策略：网络重连/元素重定位/滚动恢复

- **资源自动回收**  
  上下文管理器确保资源释放，自动清理临时文件

## 📋 使用方法

### 环境准备
1. 安装依赖库：
   ```bash
   pip install selenium pickle
   ```
2.下载浏览器对应版本的driver(本项目用的是edgedriver)
  下载电脑浏览器对应版本的driver后，将
  ```python
    def __init__(self, 
                 driver_path: str,
                 user_data_dir: str = r"C:\taobao_bot_profile",
                 cookie_file: str = "taobao_cookies.pkl"):
        self.driver = None
        self.driver_path = driver_path
        self.user_data_dir = user_data_dir
        self.cookie_file = cookie_file

  ```
  中的driver_path修改为自己的driver路径
