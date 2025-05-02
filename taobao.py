from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import os
import time

class TaobaoScraper:
    def __init__(self, 
                 driver_path: str,
                 user_data_dir: str = r"C:\taobao_bot_profile",
                 cookie_file: str = "taobao_cookies.pkl"):
        """
        初始化爬虫实例
        
        :param driver_path: Edge驱动路径
        :param user_data_dir: 用户数据存储目录 (默认C:\taobao_bot_profile)
        :param cookie_file: Cookie存储文件名 (默认taobao_cookies.pkl)
        """
        self.driver = None
        self.driver_path = driver_path
        self.user_data_dir = user_data_dir
        self.cookie_file = cookie_file

    def __enter__(self):
        """上下文管理入口"""
        self.initialize_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理出口"""
        self.close()

    def initialize_driver(self):
        """初始化浏览器驱动"""
        options = webdriver.EdgeOptions()
        options.use_chromium = True
        
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
        options.add_argument(f"user-data-dir={self.user_data_dir}")
        
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = webdriver.Edge(
            service=Service(self.driver_path),
            options=options
        )

    def check_login_status(self) -> bool:
        """验证登录状态"""
        try:
            self.driver.get("https://www.taobao.com")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.LINK_TEXT, "我的淘宝"))
            )
            return True
        except Exception as e:
            print(f"🚨 登录状态检查失败: {str(e)}")
            return False

    def manual_login(self):
        """执行手动登录流程"""
        print("👉 请按以下步骤操作：")
        print("1️⃣ 访问 https://login.taobao.com")
        print("2️⃣ 使用手机淘宝扫码完成登录")
        print("3️⃣ 登录成功后保持页面不动")
        
        self.driver.get("https://login.taobao.com")
        input("🔄 完成登录后按回车继续...")
        
        if not self.check_login_status():
            raise RuntimeError("❌ 手动登录验证失败")
        
        with open(self.cookie_file, 'wb') as f:
            pickle.dump(self.driver.get_cookies(), f)
        print("✅ 登录凭证已存储")

    def load_cookies(self) -> bool:
        """加载持久化Cookie"""
        if os.path.exists(self.cookie_file):
            try:
                with open(self.cookie_file, 'rb') as f:
                    cookies = pickle.load(f)
                    self.driver.delete_all_cookies()
                    for cookie in cookies:
                        if 'expiry' in cookie:
                            del cookie['expiry']
                        self.driver.add_cookie(cookie)
                self.driver.refresh()
                print("🔑 历史Cookie加载完成")
                return True
            except Exception as e:
                print(f"❌ Cookie加载异常: {str(e)}")
                return False
        return False

    def ensure_login(self):
        """确保登录状态"""
        if not self.check_login_status():
            print("⚠️ 检测到登录状态失效，尝试恢复...")
            if not self.load_cookies() or not self.check_login_status():
                self.manual_login()

    def smart_scroll(self) -> bool:
        """智能滚动加载"""
        scroll_container = self.driver.execute_script("""
            return document.querySelector("body > div.Oo3vRXl7BS--leftDrawer--_7efaeec > div.Oo3vRXl7BS--content--e320bf32 > div > div.Oo3vRXl7BS--comments--_00182ac.beautify-scroll-bar") 
            || document.documentElement
        """)
        
        try:
            pre_count = len(self.driver.find_elements(By.CLASS_NAME, 'Oo3vRXl7BS--Comment--_0b4e753'))
            
            self.driver.execute_script("""
                arguments[0].scrollTop += arguments[0].clientHeight * 8.5;
            """, scroll_container)
            
            time.sleep(0.2)
            
            post_count = len(self.driver.find_elements(By.CLASS_NAME, 'Oo3vRXl7BS--Comment--_0b4e753'))
            print(f"🔄 滚动检测: {pre_count} → {post_count} 条评论")
            return post_count > pre_count
        except Exception as e:
            print(f"❌ 滚动异常: {str(e)}")
            return False

    def scrape_reviews(self, product_url: str, output_file: str, max_comments: int = 1000):
        """
        执行评价爬取
        
        :param product_url: 商品详情页URL
        :param output_file: 输出文件路径
        :param max_comments: 最大收集数量 (默认1000)
        """
        self.driver.get(product_url)
        time.sleep(3)
        
        try:
            review_btn = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'Oo3vRXl7BS--ShowButton--_15e2446'))
            )
            self.driver.execute_script("arguments[0].click();", review_btn)
            time.sleep(3)
        except Exception as e:
            raise RuntimeError(f"🚫 无法打开评价页面: {str(e)}")
        
        processed = set()
        retry_count = 0
        max_retries = 3
        collected_enough = False  # 收集完成状态标识

        with open(output_file, 'w', encoding='utf-8') as f:
            while retry_count < max_retries and not collected_enough:
                current_comments = self.driver.find_elements(By.CLASS_NAME, 'Oo3vRXl7BS--Comment--_0b4e753')
                new_added = 0
                
                # 处理当前页评论
                for comment in current_comments:
                    comment_id = comment.get_attribute('data-before-current-y')
                    if comment_id not in processed:
                        try:
                            content = comment.find_element(
                                By.CLASS_NAME, 'Oo3vRXl7BS--content--_8e6708c'
                            ).text.strip()
                            f.write(f"{content}\n")
                            processed.add(comment_id)
                            new_added += 1
                            
                            # 实时检查收集数量
                            if len(processed) >= max_comments:
                                collected_enough = True
                                break  # 跳出评论处理循环
                        except Exception as e:
                            print(f"⚠️ 评论解析异常: {str(e)}")
                            continue
                    # 快速退出检查
                    if collected_enough:
                        break

                # 达到数量后立即终止
                if collected_enough:
                    print(f"🎉 成功收集 {max_comments} 条评论，任务完成")
                    break
                
                # 滚动控制逻辑
                if new_added < 5:
                    if self.smart_scroll():
                        retry_count = max(0, retry_count - 2)
                
                # 重试机制
                if new_added == 0:
                    retry_count += 1
                    print(f"🔄 重试计数器: {retry_count}/{max_retries}")
                    if self.smart_scroll():
                        retry_count = max(0, retry_count - 1)
                else:
                    retry_count = 0
                    print(f"✅ 新增 {new_added} 条，总计 {len(processed)} 条")
                
                # 动态等待策略
                delay = 1.2 if new_added > 0 else 2.0
                time.sleep(delay)
                
                # 最终终止检查
                if retry_count >= max_retries:
                    print(f"⏹️ 达到最大重试次数 {max_retries}，停止采集")

    def close(self):
        """关闭浏览器实例"""
        if self.driver:
            self.driver.quit()
            print("🛑 浏览器实例已关闭")
            if os.path.exists(self.cookie_file):
                os.remove(self.cookie_file)
                print("🧹 临时Cookie文件已清理")

# 保留独立运行功能
if __name__ == "__main__":
    with TaobaoScraper(
        driver_path=r"E:\edgedriver_win64\msedgedriver.exe"
    ) as scraper:
        scraper.ensure_login()
        scraper.scrape_reviews(
            product_url=input("🛍️ 请输入商品详情页链接: ").strip(),
            output_file='D:\C_data\AIGC\全部评价.txt',
            max_comments=1000  # 可修改为其他数值
        )
