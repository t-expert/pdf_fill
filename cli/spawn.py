import os
import time

import requests

from .env import SandboxEnv, load_sandbox_env


def spawn_sandbox(args):
    env = load_sandbox_env(args)
    spawner = SandboxSpawner(env)
    return spawner.spawn(bool(args.long))


class SandboxSpawner:
    def __init__(self, env: SandboxEnv):
        self.env = env
        self.e2b_domain = env.get('E2B_DOMAIN')
        self.e2b_api_key = env.get('E2B_API_KEY')
        self.e2b_template_id = env.get('E2B_TEMPLATE_ID')

    def create_sandbox(self, long_last: bool):
        print(f'正在创建 sandbox (模板: {self.e2b_template_id})...')
        url: str = f'https://api.{self.e2b_domain}/sandboxes'
        headers = {'X-API-KEY': self.e2b_api_key, 'Content-Type': 'application/json'}
        timeout = 30 * 60 if long_last else 5 * 60
        data = {'templateID': self.e2b_template_id, 'timeout': timeout}

        start_time = time.time()
        response = requests.post(url, headers=headers, json=data)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f'创建接口耗时: {elapsed_time:.2f} 秒')

        if response.status_code == 200 or response.status_code == 201:
            sandbox_info = response.json()
            print('Sandbox 创建成功！', sandbox_info)
            return sandbox_info
        else:
            print(f'创建失败: {response.status_code}')
            print(response.text)
            return None

    def check_health(self, client_id, sandbox_id):
        health_url = f'https://8330-{sandbox_id}-{client_id}.{self.e2b_domain}/healthz'
        print(f'正在检查健康状态: {health_url}')

        max_attempts = 60
        start_time = time.time()
        for attempt in range(max_attempts):
            try:
                response = requests.get(health_url)
                # print('健康检查结果', response.status_code, response.text)
                if response.status_code == 200:
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print('健康检查通过！服务已经准备就绪。')
                    print(f'健康检查总耗时: {elapsed_time:.2f} 秒')
                    return True
                else:
                    print(f'第 {attempt + 1} 次检查: 状态码 {response.status_code}')
            except requests.exceptions.RequestException:
                print(f'第 {attempt + 1} 次检查: 连接失败')

            time.sleep(2)  # 每次检查间隔2秒

        print('健康检查失败，超过最大尝试次数。')
        return False

    def spawn(self, long_last: bool):
        # 创建 sandbox
        sandbox_info = self.create_sandbox(long_last)
        if not sandbox_info:
            return
        sbx_id = sandbox_info['sandboxID']
        client_id = sandbox_info['clientID']

        print('\n获取到的 Sandbox 信息:')
        print(f'Client ID: {client_id}')
        print(f'Sandbox ID: {sbx_id}')

        # 进行健康检查
        success = self.check_health(client_id, sbx_id)
        print('sandbox id:')
        print(f'{sbx_id}-{client_id}')
        return success
