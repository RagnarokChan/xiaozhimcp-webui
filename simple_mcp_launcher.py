#!/usr/bin/env python3
"""
小智AI聊天机器人 - MCP WEBUI v1
专为小智MCP的WebSocket连接设计
基于原版mcp_pipe.py架构
"""

import json
import os
import subprocess
import signal
import threading
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from mcp_websocket_proxy import start_mcp_pipe

app = Flask(__name__)
app.secret_key = 'mcp-webui-v1-secret-key'

# 配置
CONFIG_FILE = 'mcp_config.json'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json'}

# 全局变量
current_config = {}
websocket_url = "wss://api.xiaozhi.me/mcp/"
mcp_services = {}  # 存储MCP服务线程
server_logs = {}  # 存储服务日志
websocket_connected = False  # WebSocket连接状态

# 依赖检查映射
DEPENDENCY_MAP = {
    'npx': {
        'check_cmd': 'npx --version',
        'description': 'Node.js包执行器'
    },
    'uvx': {
        'check_cmd': 'uvx --version', 
        'description': 'Python包执行器'
    },
    'python': {
        'check_cmd': 'python --version',
        'description': 'Python解释器'
    },
    'python3': {
        'check_cmd': 'python3 --version',
        'description': 'Python3解释器'
    },
    'node': {
        'check_cmd': 'node --version',
        'description': 'Node.js运行时'
    },
    'npm': {
        'check_cmd': 'npm --version',
        'description': 'Node.js包管理器'
    }
}

def load_config():
    """加载MCP配置"""
    global current_config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            current_config = json.load(f)
        if 'mcpServers' not in current_config:
            current_config = {"mcpServers": {}}
    else:
        current_config = {"mcpServers": {}}
        save_config()

def save_config():
    """保存MCP配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_config, f, indent=2, ensure_ascii=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_dependency(command):
    """检查依赖是否已安装"""
    if command in DEPENDENCY_MAP:
        try:
            result = subprocess.run(
                DEPENDENCY_MAP[command]['check_cmd'].split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    return False

def get_server_dependencies(config):
    """获取服务所需的依赖"""
    dependencies = []
    command = config.get('command', '')
    
    if command in DEPENDENCY_MAP:
        dependencies.append(command)
    
    if command == 'npx':
        dependencies.extend(['node', 'npm', 'npx'])
    elif command == 'uvx':
        dependencies.append('uvx')
    
    return dependencies

def start_mcp_service(name, config):
    """启动MCP服务"""
    try:
        if config.get('disabled', False):
            return False, "服务已禁用"
            
        # 启动MCP服务在单独线程中
        def run_service():
            start_mcp_pipe(
                command=config['command'],
                args=config.get('args', []),
                env=config.get('env', {}),
                endpoint_url=websocket_url
            )
        
        service_thread = threading.Thread(target=run_service, daemon=True)
        service_thread.start()
        
        mcp_services[name] = {
            'thread': service_thread,
            'config': config,
            'status': 'running',
            'start_time': time.time()
        }
        
        print(f"✅ 启动MCP服务: {name}")
        return True, f"MCP服务启动成功"
        
    except Exception as e:
        print(f"❌ 启动MCP服务失败 {name}: {e}")
        return False, f"启动失败: {str(e)}"

def stop_mcp_service(name):
    """停止MCP服务"""
    if name in mcp_services:
        try:
            # Note: 由于使用了原版架构，线程会在WebSocket断开时自然结束
            del mcp_services[name]
            print(f"🛑 停止MCP服务: {name}")
            return True, "MCP服务已停止"
            
        except Exception as e:
            print(f"❌ 停止MCP服务失败 {name}: {e}")
            return False, f"停止失败: {str(e)}"
    return False, "服务未运行"

def get_mcp_service_status(name):
    """获取MCP服务状态"""
    if name not in mcp_services:
        return 'stopped'
    
    service_info = mcp_services[name]
    thread = service_info['thread']
    
    if thread.is_alive():
        return 'running'
    else:
        # 线程已结束，清理
        del mcp_services[name]
        return 'stopped'

def get_mcp_service_info(name):
    """获取MCP服务详细信息"""
    if name not in mcp_services:
        return None
    
    service_info = mcp_services[name]
    return {
        'status': get_mcp_service_status(name),
        'start_time': service_info['start_time'],
        'uptime': time.time() - service_info['start_time'],
        'config': service_info['config']
    }

def get_system_info():
    """获取系统信息"""
    info = {
        'dependencies': {},
        'system': {
            'platform': os.name,
            'python_version': subprocess.getoutput('python3 --version'),
            'working_directory': os.getcwd()
        }
    }
    
    for dep, dep_info in DEPENDENCY_MAP.items():
        info['dependencies'][dep] = {
            'installed': check_dependency(dep),
            'description': dep_info['description']
        }
    
    return info

@app.route('/')
def index():
    """主页面"""
    servers = {}
    for name, config in current_config.get('mcpServers', {}).items():
        servers[name] = {
            'config': config,
            'status': get_mcp_service_status(name),
            'mode': 'websocket'
        }
    
    return render_template('launcher.html', 
                         servers=servers, 
                         websocket_url=websocket_url,
                         operation_mode="websocket",
                         system_info=get_system_info())

@app.route('/start/<server_name>', methods=['POST'])
def start_server(server_name):
    """启动服务"""
    if server_name in current_config.get('mcpServers', {}):
        config = current_config['mcpServers'][server_name]
        success, message = start_mcp_service(server_name, config)
        return jsonify({
            'success': success, 
            'message': message,
            'status': get_mcp_service_status(server_name),
            'mode': 'websocket'
        })
    return jsonify({'success': False, 'error': '服务不存在'})

@app.route('/stop/<server_name>', methods=['POST'])
def stop_server(server_name):
    """停止服务"""
    success, message = stop_mcp_service(server_name)
    return jsonify({
        'success': success, 
        'message': message,
        'status': get_mcp_service_status(server_name),
        'mode': 'websocket'
    })

@app.route('/restart/<server_name>', methods=['POST'])
def restart_server(server_name):
    """重启服务"""
    if server_name in current_config.get('mcpServers', {}):
        config = current_config['mcpServers'][server_name]
        
        # 先停止
        stop_success, stop_message = stop_mcp_service(server_name)
        time.sleep(1)  # 等待1秒
        
        # 再启动
        start_success, start_message = start_mcp_service(server_name, config)
        
        return jsonify({
            'success': start_success,
            'message': f"重启: {stop_message} -> {start_message}",
            'status': get_mcp_service_status(server_name),
            'mode': 'websocket'
        })
    return jsonify({'success': False, 'error': '服务不存在'})

@app.route('/start_all', methods=['POST'])
def start_all_servers():
    """启动所有服务 - 建议一次只启动一个服务避免冲突"""
    results = []
    active_services = [name for name in mcp_services.keys() if get_mcp_service_status(name) == 'running']
    
    if active_services:
        return jsonify({
            'results': [],
            'warning': f'检测到{len(active_services)}个服务正在运行，建议先停止所有服务再启动，避免WebSocket连接冲突'
        })
    
    for name, config in current_config.get('mcpServers', {}).items():
        if not config.get('disabled', False):
            success, message = start_mcp_service(name, config)
            results.append({'name': name, 'success': success, 'message': message, 'mode': 'websocket'})
            
            # 添加延迟避免同时连接
            time.sleep(1)
    
    return jsonify({'results': results})

@app.route('/stop_all', methods=['POST'])
def stop_all_servers():
    """停止所有服务"""
    results = []
    for name in list(mcp_services.keys()):
        success, message = stop_mcp_service(name)
        results.append({'name': name, 'success': success, 'message': message})
    
    return jsonify({'results': results})

@app.route('/toggle_server/<server_name>', methods=['POST'])
def toggle_server(server_name):
    """切换服务启用/禁用状态"""
    if server_name in current_config.get('mcpServers', {}):
        config = current_config['mcpServers'][server_name]
        config['disabled'] = not config.get('disabled', False)
        save_config()
        
        # 如果禁用了正在运行的服务，停止它
        if config['disabled'] and get_mcp_service_status(server_name) == 'running':
            stop_mcp_service(server_name)
        
        return jsonify({
            'success': True,
            'disabled': config['disabled'],
            'status': get_mcp_service_status(server_name),
            'mode': 'websocket'
        })
    return jsonify({'success': False, 'error': '服务不存在'})

@app.route('/upload_config', methods=['POST'])
def upload_config():
    """上传配置文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    if file and allowed_file(file.filename):
        try:
            # 停止所有服务
            for name in list(mcp_services.keys()):
                stop_mcp_service(name)
            
            # 解析新配置
            content = file.read().decode('utf-8')
            new_config = json.loads(content)
            
            # 验证配置格式
            if 'mcpServers' not in new_config:
                return jsonify({'success': False, 'error': '无效的配置文件格式'})
            
            # 更新配置
            global current_config
            current_config = new_config
            save_config()
            
            return jsonify({'success': True, 'message': '配置文件导入成功'})
            
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': '无效的JSON文件'})
        except Exception as e:
            return jsonify({'success': False, 'error': f'导入失败: {str(e)}'})
    
    return jsonify({'success': False, 'error': '不支持的文件类型'})

@app.route('/import_json_config', methods=['POST'])
def import_json_config():
    """从JSON编辑器导入配置"""
    try:
        # 停止所有服务
        for name in list(mcp_services.keys()):
            stop_mcp_service(name)
        
        # 获取JSON数据
        new_config = request.get_json()
        
        # 验证配置格式
        if not new_config or 'mcpServers' not in new_config:
            return jsonify({'success': False, 'error': '无效的配置格式，缺少mcpServers字段'})
        
        # 更新配置
        global current_config
        current_config = new_config
        save_config()
        
        return jsonify({'success': True, 'message': 'JSON配置导入成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'导入失败: {str(e)}'})

@app.route('/update_websocket', methods=['POST'])
def update_websocket():
    """更新WebSocket地址"""
    global websocket_url
    data = request.get_json()
    if 'url' in data:
        websocket_url = data['url']
        return jsonify({'success': True, 'message': 'WebSocket地址更新成功'})
    return jsonify({'success': False, 'error': '无效的URL'})

@app.route('/get_config')
def get_config():
    """获取当前配置"""
    return jsonify(current_config)

@app.route('/system_info')
def system_info():
    """获取系统信息"""
    return jsonify(get_system_info())

@app.route('/export_config')
def export_config():
    """导出配置文件"""
    from flask import Response
    config_json = json.dumps(current_config, indent=2, ensure_ascii=False)
    return Response(
        config_json,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=mcp_config.json'}
    )

@app.route('/save_settings', methods=['POST'])
def save_settings():
    """保存当前设置（WebSocket地址和MCP配置）"""
    try:
        data = request.get_json()
        
        # 创建设置文件
        settings = {
            'websocket_url': data.get('websocket_url', websocket_url),
            'mcp_config': current_config,
            'saved_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 保存到文件
        settings_file = 'saved_settings.json'
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True, 
            'message': '设置已保存到 saved_settings.json',
            'file': settings_file
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'保存失败: {str(e)}'})

@app.route('/load_settings', methods=['POST'])
def load_settings():
    """加载已保存的设置"""
    try:
        settings_file = 'saved_settings.json'
        if not os.path.exists(settings_file):
            return jsonify({'success': False, 'error': '未找到保存的设置文件'})
        
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # 更新全局变量
        global current_config, websocket_url
        current_config = settings.get('mcp_config', {})
        websocket_url = settings.get('websocket_url', websocket_url)
        
        # 保存配置
        save_config()
        
        return jsonify({
            'success': True,
            'message': f"设置已加载（保存于: {settings.get('saved_at', '未知时间')}）",
            'websocket_url': websocket_url,
            'config': current_config
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'加载失败: {str(e)}'})

@app.route('/export_settings')
def export_settings():
    """导出当前设置为文件下载"""
    from flask import Response
    
    settings = {
        'websocket_url': websocket_url,
        'mcp_config': current_config,
        'exported_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    settings_json = json.dumps(settings, indent=2, ensure_ascii=False)
    return Response(
        settings_json,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=xiaozhi_mcp_settings.json'}
    )

def cleanup_on_exit():
    """程序退出时清理"""
    print("🧹 清理MCP服务...")
    for name in list(mcp_services.keys()):
        stop_mcp_service(name)

def signal_handler(sig, frame):
    """信号处理"""
    cleanup_on_exit()
    exit(0)

@app.route('/websocket_status')
def websocket_status():
    """获取WebSocket连接状态"""
    global websocket_connected
    
    # 检查是否有活跃的MCP服务（间接表示WebSocket连接状态）
    running_services = []
    for name, service_info in mcp_services.items():
        if service_info and service_info.get('thread') and service_info['thread'].is_alive():
            running_services.append(name)
    
    # 如果有运行中的服务，假设WebSocket已连接
    websocket_connected = len(running_services) > 0
    
    return jsonify({
        'connected': websocket_connected,
        'running_services': running_services,
        'status_text': '已连接' if websocket_connected else '未连接'
    })

if __name__ == '__main__':
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建上传目录
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # 加载配置
    load_config()
    
    print("🚀 小智AI聊天机器人 - MCP WEBUI v1")
    print("🔗 专为小智MCP WebSocket连接设计")
    print("🌐 访问: http://localhost:5050")
    print("---")
    
    try:
        app.run(host='0.0.0.0', port=5050, debug=False)
    finally:
        cleanup_on_exit() 