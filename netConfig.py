import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import platform
import json
import os
import re
from typing import Dict, List



class NetworkConfigManager:
    def __init__(self, root):
        self.root = root
        self.root.title("网络配置管理器")
        self.root.geometry("500x500")
        self.center_window(self.root, 500, 500)
        self.root.resizable(False, False)  # 禁止窗口缩放

        self.interfaces_info = interfaces_info()

        # 配置文件路径
        self.config_file = "network_configs.json"

        # 网络配置列表
        self.configs = []
        

        # 当前选中的配置
        self.selected_config = None
        self.selected_index = None

        # 网卡配置字典
        self.adapter_configs = self.get_interfaces_info()

        self.setup_ui()
        self.load_configs()

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置列表框架
        list_frame = ttk.LabelFrame(main_frame, text="网络配置列表", padding="5")
        list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # 创建Treeview
        columns = ('IP地址', '子网掩码', '网关')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)

        # 设置列标题
        self.tree.heading('IP地址', text='IP地址')
        self.tree.heading('子网掩码', text='子网掩码')
        self.tree.heading('网关', text='网关')

        # 设置列宽
        self.tree.column('IP地址', width=150)
        self.tree.column('子网掩码', width=150)
        self.tree.column('网关', width=150)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        # 按钮框架
        button_frame = ttk.Frame(list_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))

        # 添加、编辑、删除按钮
        ttk.Button(button_frame, text="添加", command=self.add_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="编辑", command=self.edit_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="删除", command=self.delete_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="移动", command=self.toggle_move_buttons).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="保存", command=self.save_configs).pack(side=tk.LEFT)
        # ttk.Button(button_frame, text="加载", command=self.load_configs_from_file).pack(side=tk.LEFT)

        # 配置详情框架
        detail_frame = ttk.LabelFrame(main_frame, text="当前网卡配置", padding="5")
        detail_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # IP地址
        ttk.Label(detail_frame, text="IP地址:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ip_var = tk.StringVar()
        ttk.Entry(detail_frame, textvariable=self.ip_var, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2,
                                                                         padx=(5, 0))

        # 子网掩码
        ttk.Label(detail_frame, text="子网掩码:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.mask_var = tk.StringVar()
        ttk.Entry(detail_frame, textvariable=self.mask_var, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2,
                                                                           padx=(5, 0))

        # 网关
        ttk.Label(detail_frame, text="网关:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.gateway_var = tk.StringVar()
        ttk.Entry(detail_frame, textvariable=self.gateway_var, width=20).grid(row=2, column=1, sticky=(tk.W, tk.E),
                                                                         pady=2, padx=(5, 0))

        # DNS1
        ttk.Label(detail_frame, text="DNS1:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.dns1_var = tk.StringVar()
        ttk.Entry(detail_frame, textvariable=self.dns1_var, width=20).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))

        # DNS2
        ttk.Label(detail_frame, text="DNS2:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.dns2_var = tk.StringVar()
        ttk.Entry(detail_frame, textvariable=self.dns2_var, width=20).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))

        detail_frame.columnconfigure(1, weight=1)

        # 应用操作框架
        action_frame = ttk.LabelFrame(main_frame, text="应用网卡配置", padding="5")
        action_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=(0, 10))

        # 获取网卡列表
        self.network_adapters = self.get_network_adapters()
        self.adapter_var = tk.StringVar()

        ttk.Label(action_frame, text="选择网卡:").grid(row=0, column=0, sticky=tk.W, pady=0)
        self.adapter_combo = ttk.Combobox(action_frame, textvariable=self.adapter_var, values=self.network_adapters,
                                     width=25)
        self.adapter_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        if self.network_adapters:
            self.adapter_combo.current(0)

        # 刷新网卡按钮
        ttk.Button(action_frame, text="刷新网卡列表", command=self.refresh_adapters).grid(row=2, column=0, pady=2, sticky=(tk.W, tk.E))

        # 新建一个Frame用于并排放置按钮
        btn_row_frame = ttk.Frame(action_frame)
        btn_row_frame.grid(row=3, column=0, pady=0, sticky=(tk.W, tk.E))
        # 设置列权重，让按钮自动填满
        btn_row_frame.columnconfigure(0, weight=1)
        btn_row_frame.columnconfigure(1, weight=1)

        # 操作按钮
        ttk.Button(btn_row_frame, text="应用静态IP", command=self.apply_current_adapter_config).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(btn_row_frame, text="启用DHCP", command=self.enable_dhcp).grid(row=0, column=1, sticky=(tk.W, tk.E))
        # 禁用/启用网卡按钮
        self.toggle_adapter_btn = ttk.Button(action_frame, text="启用 / 禁用网卡", command=self.toggle_adapter_status)
        self.toggle_adapter_btn.grid(row=4, column=0, pady=2, sticky=(tk.W, tk.E))

        # 绑定双击事件
        self.tree.bind('<Double-1>', lambda event: self.apply_static_ip())

        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(1, weight=1)
        action_frame.columnconfigure(0, weight=1)

        # 加载初始数据
        self.refresh_tree()

        # 配置移动框架
        self.move_frame = ttk.LabelFrame(self.root, text="配置移动", padding="5")
        self.move_frame.place(relx=0.98, rely=0.5, anchor="e")
        self.move_frame.place_forget()  # 初始隐藏

        ttk.Button(self.move_frame, text="🔝 置顶", command=self.move_top).pack(fill=tk.X, pady=2)
        ttk.Button(self.move_frame, text="⬆️ 上移", command=self.move_up).pack(fill=tk.X, pady=2)
        ttk.Button(self.move_frame, text="⬇️ 下移", command=self.move_down).pack(fill=tk.X, pady=2)
        ttk.Button(self.move_frame, text="🔚 置底", command=self.move_bottom).pack(fill=tk.X, pady=2)

        # 添加切换按钮（建议放在button_frame最后）
        self.move_visible = False  # 控制显示状态
        # ttk.Button(button_frame, text="移动", command=self.toggle_move_buttons).pack(side=tk.LEFT, padx=(5, 0))

        # 绑定网卡下拉框选择事件
        self.adapter_combo.bind('<<ComboboxSelected>>', self.on_adapter_changed)
        
        # 默认选中第一个网卡并显示其配置
        if self.network_adapters:
            self.adapter_var.set(self.network_adapters[0])
            self.show_adapter_config(self.network_adapters[0])

    def get_interfaces_info(self):
        """获取所有网络接口信息"""
        return self.interfaces_info.get_all_interfaces_info()

    def center_window(self, window, width=None, height=None):
        """让窗口居中显示"""
        # window.update_idletasks()
        if width is None or height is None:
            width = window.winfo_width()
            height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def get_network_adapters(self):
        """获取网络适配器列表"""
        interfaces = []

        try:
            # 方法1: 使用 netsh interface show interface            
            # 执行netsh命令获取接口信息
            result = subprocess.run([
                'netsh', 'interface', 'show', 'interface'
            ], capture_output=True, text=True, shell=True, encoding='gbk')
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                
                # 解析输出，跳过表头
                for line in lines:
                    # 匹配包含"已连接"或"Connected"的行
                    if '已连接' in line or 'Connected' in line or '启用' in line or 'Enabled' in line:
                        # 提取接口名称（通常是最后一列）
                        parts = line.split()
                        if len(parts) >= 4:
                            # 接口名称通常是最后一部分
                            interface_name = ' '.join(parts[3:])
                            interfaces.append(interface_name)
                    elif len(line.strip().split()) >= 4 and not line.startswith('-'):
                        # 处理其他格式的输出
                        parts = line.strip().split(None, 3)  # 最多分割成4部分
                        if len(parts) == 4:
                            interface_name = parts[3]
                            # 过滤掉系统保留接口
                            if not any(skip in interface_name.lower() for skip in ['loopback', 'isatap', 'teredo']):
                                interfaces.append(interface_name)
            interfaces.remove('接口名称')
            if '以太网' in interfaces:
                interfaces.insert(0, interfaces.pop(interfaces.index('以太网')))

                        
        except Exception as e:
            print(f"获取网络接口失败: {e}")
            interfaces = ['以太网', 'WLAN', '本地连接']  # 默认网卡名

        return interfaces  # Windows默认网卡名

    def refresh_adapters(self):
        """刷新网卡列表并更新下拉框"""
        self.network_adapters = self.get_network_adapters()
        # 更新下拉框内容
        self.adapter_combo['values'] = self.network_adapters
        # if self.network_adapters:
        #     self.adapter_var.set(self.network_adapters[0])
        # else:
        #     self.adapter_var.set("")
        
        """重新获取网卡信息"""
        self.adapter_configs = self.get_interfaces_info()
        self.on_adapter_changed()  # 更新详情区显示

        self.status_var.set("网卡列表已刷新")

    def add_config(self):
        """添加新配置"""
        self.edit_window = tk.Toplevel(self.root)
        self.edit_window.title("添加配置")
        self.edit_window.transient(self.root)
        self.edit_window.grab_set()
        self.center_window(self.edit_window, 300, 150)

        # 编辑字段
        ttk.Label(self.edit_window, text="IP地址:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.edit_ip_var = tk.StringVar()
        ip_entry = ttk.Entry(self.edit_window, textvariable=self.edit_ip_var, width=20)
        ip_entry.grid(row=0, column=1, padx=5, pady=5)
        ip_entry.focus_set()  # 让IP输入框获得焦点

        ttk.Label(self.edit_window, text="子网掩码:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.edit_mask_var = tk.StringVar()
        ttk.Entry(self.edit_window, textvariable=self.edit_mask_var, width=20).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.edit_window, text="网关:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.edit_gateway_var = tk.StringVar()
        ttk.Entry(self.edit_window, textvariable=self.edit_gateway_var, width=20).grid(row=2, column=1, padx=5, pady=5)

        # 按钮
        button_frame = ttk.Frame(self.edit_window)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="确定", command=self.save_new_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.edit_window.destroy).pack(side=tk.LEFT, padx=5)

    def save_new_config(self):
        """保存新配置"""
        ip = self.edit_ip_var.get().strip()
        mask = self.edit_mask_var.get().strip()
        gateway = self.edit_gateway_var.get().strip()

        if ip and mask:
            self.configs.append({
                'ip': ip,
                'mask': mask,
                'gateway': gateway
            })
            self.refresh_tree()
            self.edit_window.destroy()
            self.status_var.set("配置已添加")
        else:
            messagebox.showerror("错误", "IP地址和子网掩码不能为空")

    def edit_config(self):
        """编辑选中的配置"""
        if self.selected_index is None:
            messagebox.showwarning("警告", "请先选择要编辑的配置")
            return

        config = self.configs[self.selected_index]

        # 创建编辑窗口
        self.edit_window = tk.Toplevel(self.root)
        self.edit_window.title("编辑配置")
        self.edit_window.geometry("300x150")
        self.edit_window.transient(self.root)
        self.edit_window.grab_set()
        self.center_window(self.edit_window, 300, 150)
        
        # 编辑字段
        ttk.Label(self.edit_window, text="IP地址:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.edit_ip_var = tk.StringVar(value=config['ip'])
        ttk.Entry(self.edit_window, textvariable=self.edit_ip_var, width=20).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.edit_window, text="子网掩码:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.edit_mask_var = tk.StringVar(value=config['mask'])
        ttk.Entry(self.edit_window, textvariable=self.edit_mask_var, width=20).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(self.edit_window, text="网关:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.edit_gateway_var = tk.StringVar(value=config.get('gateway', ''))
        ttk.Entry(self.edit_window, textvariable=self.edit_gateway_var, width=20).grid(row=2, column=1, padx=5, pady=5)

        # 按钮
        button_frame = ttk.Frame(self.edit_window)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="确定", command=lambda: self.save_edit_config(self.selected_index)).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.edit_window.destroy).pack(side=tk.LEFT, padx=5)

    def save_edit_config(self, index):
        """保存编辑的配置"""
        ip = self.edit_ip_var.get().strip()
        mask = self.edit_mask_var.get().strip()
        gateway = self.edit_gateway_var.get().strip()

        if ip and mask:
            self.configs[index] = {
                'ip': ip,
                'mask': mask,
                'gateway': gateway
            }
            self.refresh_tree()
            self.edit_window.destroy()
            self.status_var.set("配置已更新")
        else:
            messagebox.showerror("错误", "IP地址和子网掩码不能为空")

    def delete_config(self):
        """删除选中的配置"""
        if self.selected_index is None:
            messagebox.showwarning("警告", "请先选择要删除的配置")
            return

        if messagebox.askyesno("确认", "确定要删除选中的配置吗？"):
            del self.configs[self.selected_index]
            self.refresh_tree()
            self.selected_index = None
            self.selected_config = None
            self.clear_detail_fields()
            self.status_var.set("配置已删除")

    def on_select(self, event):
        """选择配置项时的处理"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            self.selected_index = self.tree.index(selection[0])
            self.selected_config = self.configs[self.selected_index]

            # # 更新详情显示
            # self.ip_var.set(values[0])
            # self.mask_var.set(values[1])
            # self.gateway_var.set(values[2] if len(values) > 2 else "")

    # def refresh_tree(self):
    #     """刷新配置列表"""
    #     # 清空现有项目
    #     for item in self.tree.get_children():
    #         self.tree.delete(item)

    #     # 添加配置项目
    #     for config in self.configs:
    #         self.tree.insert('', tk.END, values=(
    #             config['ip'],
    #             config['mask'],
    #             config.get('gateway', '')
    #         ))

    #     # 默认选中第一行
    #     children = self.tree.get_children()
    #     if children:
    #         self.tree.selection_set(children[0])
    #         self.tree.focus(children[0])
    #         self.on_select(None)
    def refresh_tree(self):
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 添加配置项目
        for config in self.configs:
            self.tree.insert('', tk.END, values=(
                config['ip'],
                config['mask'],
                config.get('gateway', '')
            ))

        # 保持当前选中项
        children = self.tree.get_children()
        if children:
            # 如果selected_index有效，则选中对应行，否则选中第一行
            if self.selected_index is not None and 0 <= self.selected_index < len(children):
                self.tree.selection_set(children[self.selected_index])
                self.tree.focus(children[self.selected_index])
                self.on_select(None)
            else:
                self.tree.selection_set(children[0])
                self.tree.focus(children[0])
                self.selected_index = 0
                self.on_select(None)

    def clear_detail_fields(self):
        """清空详情字段"""
        self.ip_var.set("")
        self.mask_var.set("")
        self.gateway_var.set("")

    def save_configs(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, ensure_ascii=False, indent=2)
            self.status_var.set("配置已保存到文件")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")

    def load_configs(self):
        """从文件加载配置 - 修复编码问题"""
        try:
            if os.path.exists(self.config_file):
                # 尝试多种编码方式读取
                encodings = ['utf-8', 'gbk', 'gb2312']
                for encoding in encodings:
                    try:
                        with open(self.config_file, 'r', encoding=encoding) as f:
                            self.configs = json.load(f)
                        self.refresh_tree()
                        self.status_var.set(f"配置已从文件加载 (编码: {encoding})")
                        return
                    except UnicodeDecodeError:
                        continue

                # 如果所有编码都失败，创建新的空配置
                self.configs = []
                self.status_var.set("配置文件编码不兼容，已创建新配置")
            else:
                self.configs = []
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {e}")
            self.configs = []

    def load_configs_from_file(self):
        """从文件加载配置"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # 尝试多种编码方式读取
                encodings = ['utf-8', 'gbk', 'gb2312']
                success = False
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            self.configs = json.load(f)
                        self.refresh_tree()
                        self.status_var.set(f"配置已从文件加载 (编码: {encoding})")
                        success = True
                        break
                    except UnicodeDecodeError:
                        continue

                if not success:
                    messagebox.showerror("错误", "无法识别文件编码")

            except Exception as e:
                messagebox.showerror("错误", f"加载配置失败: {e}")

    def apply_static_ip(self):
        """应用静态IP配置"""
        if not self.selected_config:
            messagebox.showwarning("警告", "请先选择要应用的配置")
            return

        adapter = self.adapter_var.get()
        if not adapter:
            messagebox.showwarning("警告", "请选择网络适配器")
            return

        ip = self.selected_config['ip']
        mask = self.selected_config['mask']
        gateway = self.selected_config.get('gateway', '')

        try:
            if platform.system() == "Windows":
                # Windows系统应用静态IP
                cmd = f'netsh interface ip set address name="{adapter}" static {ip} {mask}'
                if gateway:
                    cmd += f' {gateway}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
                if result.returncode != 0:
                    raise Exception(result.stderr)
                
            # 更新详情显示
            self.ip_var.set(ip)
            self.mask_var.set(mask)
            self.gateway_var.set(gateway if len(gateway) > 2 else "")
            # self.dns1_var.set("")
            # self.dns1_var.set("")

            self.status_var.set(f"静态IP已应用到 {adapter}")
            # messagebox.showinfo("成功", f"静态IP配置已应用到 {adapter}")

        except Exception as e:
            messagebox.showerror("错误", f"应用静态IP失败: {str(e)[:200]}")  # 限制错误信息长度

    def apply_current_adapter_config(self):
        """应用左侧详情区修改后的当前网卡配置到选中网卡"""
        adapter = self.adapter_var.get()
        ip = self.ip_var.get().strip()
        mask = self.mask_var.get().strip()
        gateway = self.gateway_var.get().strip()
        dns1 = self.dns1_var.get().strip()
        dns2 = self.dns2_var.get().strip()
        if not adapter:
            messagebox.showwarning("警告", "请选择网络适配器")
            return
        if not ip or not mask:
            messagebox.showwarning("警告", "IP地址和子网掩码不能为空")
            return
        try:
            if platform.system() == "Windows":
                # 设置IP和掩码
                cmd_ip = f'netsh interface ip set address name="{adapter}" static {ip} {mask}'
                if gateway:
                    cmd_ip += f' {gateway}'
                result = subprocess.run(cmd_ip, shell=True, capture_output=True, text=True, encoding='gbk')
                if result.returncode != 0:
                    raise Exception(result.stderr)
                # 设置DNS1
                if dns1:
                    cmd_dns1 = f'netsh interface ip set dns name="{adapter}" static {dns1} primary'
                    result = subprocess.run(cmd_dns1, shell=True, capture_output=True, text=True, encoding='gbk')
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                else:
                    cmd_dns1 = f'netsh interface ip set dns name="{adapter}" source=static addr=none primary'
                    result = subprocess.run(cmd_dns1, shell=True, capture_output=True, text=True, encoding='gbk')
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                # 设置DNS2
                if dns2:
                    cmd_dns2 = f'netsh interface ip add dns name="{adapter}" {dns2} index=2'
                    result = subprocess.run(cmd_dns2, shell=True, capture_output=True, text=True, encoding='gbk')
                    if result.returncode != 0:
                        raise Exception(result.stderr)
                else:
                    cmd_dns2 = f'netsh interface ip set dns name="{adapter}" source=static addr=none index=2'
                    result = subprocess.run(cmd_dns2, shell=True, capture_output=True, text=True, encoding='gbk')
                    if result.returncode != 0:
                        raise Exception(result.stderr)

        except Exception as e:
            messagebox.showerror("错误", f"应用失败: {str(e)[:200]}")

    def enable_dhcp(self):
        """启用DHCP"""
        adapter = self.adapter_var.get()
        if not adapter:
            messagebox.showwarning("警告", "请选择网络适配器")
            return

        try:
            if platform.system() == "Windows":
                # Windows系统启用DHCP
                cmd = f'netsh interface ip set address name="{adapter}" dhcp & netsh interface ip set dns name="{adapter}" source=dhcp'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
                if result.returncode != 0:
                    raise Exception(result.stderr)

            self.status_var.set(f"DHCP已启用在 {adapter}")
            # messagebox.showinfo("成功", f"DHCP已启用在 {adapter}")
        except Exception as e:
            messagebox.showerror("错误", f"启用DHCP失败: {str(e)[:200]}")  # 限制错误信息长度

    def move_top(self):
        """将选中配置置顶"""
        if self.selected_index is not None and self.selected_index > 0:
            config = self.configs.pop(self.selected_index)
            self.configs.insert(0, config)
            self.refresh_tree()
            self.selected_index = 0
            self.tree.selection_set(self.tree.get_children()[0])
            self.tree.focus(self.tree.get_children()[0])
            self.on_select(None)

    def move_up(self):
        """将选中配置上移一行"""
        if self.selected_index is not None and self.selected_index > 0:
            self.configs[self.selected_index], self.configs[self.selected_index - 1] = self.configs[self.selected_index - 1], self.configs[self.selected_index]
            self.refresh_tree()
            self.selected_index -= 1
            self.tree.selection_set(self.tree.get_children()[self.selected_index])
            self.tree.focus(self.tree.get_children()[self.selected_index])
            self.on_select(None)

    def move_down(self):
        """将选中配置下移一行"""
        if self.selected_index is not None and self.selected_index < len(self.configs) - 1:
            self.configs[self.selected_index], self.configs[self.selected_index + 1] = self.configs[self.selected_index + 1], self.configs[self.selected_index]
            self.refresh_tree()
            self.selected_index += 1
            self.tree.selection_set(self.tree.get_children()[self.selected_index])
            self.tree.focus(self.tree.get_children()[self.selected_index])
            self.on_select(None)

    def move_bottom(self):
        """将选中配置置底"""
        if self.selected_index is not None and self.selected_index < len(self.configs) - 1:
            config = self.configs.pop(self.selected_index)
            self.configs.append(config)
            self.refresh_tree()
            self.selected_index = len(self.configs) - 1
            self.tree.selection_set(self.tree.get_children()[self.selected_index])
            self.tree.focus(self.tree.get_children()[self.selected_index])
            self.on_select(None)

    def toggle_move_buttons(self):
        """显示或隐藏配置移动按钮组"""
        if self.move_visible:
            self.move_frame.place_forget()
            self.move_visible = False
        else:
            self.move_frame.place(relx=0.98, rely=0.5, anchor="e")
            self.move_visible = True

    def toggle_adapter_status(self):
        """启用或禁用当前选中网卡"""
        adapter = self.adapter_var.get()
        if not adapter:
            messagebox.showwarning("警告", "请选择网络适配器")
            return
        # 判断当前状态
        status = self.get_adapter_status(adapter)
        try:
            if "禁用" in status or "Disabled" in status:
                # 当前是禁用，执行启用
                if platform.system() == "Windows":
                    cmd = f'netsh interface set interface name="{adapter}" admin=ENABLED'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
                    if result.returncode != 0:
                        raise Exception(result.stderr)

                self.status_var.set(f"{adapter} 已启用")
                # self.adapter_status_var.set("状态：已启用")
                # self.toggle_adapter_btn.config(text="禁用网卡")
                # messagebox.showinfo("成功", f"{adapter} 已启用")
            else:
                # 当前是启用，执行禁用
                if platform.system() == "Windows":
                    cmd = f'netsh interface set interface name="{adapter}" admin=DISABLED'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk')
                    if result.returncode != 0:
                        raise Exception(result.stderr)

                self.status_var.set(f"{adapter} 已禁用")
                # self.adapter_status_var.set("状态：已禁用")
                # self.toggle_adapter_btn.config(text="启用网卡")
                # messagebox.showinfo("成功", f"{adapter} 已禁用")
        except Exception as e:
            messagebox.showerror("错误", f"操作失败: {str(e)[:200]}")

    def get_adapter_status(self, adapter_name):
        """返回指定网卡的启用/禁用状态（Windows）"""
        try:
            result = subprocess.run(
                ['netsh', 'interface', 'show', 'interface'],
                capture_output=True, text=True, shell=True, encoding='gbk'
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip().endswith(adapter_name):
                        # 一般格式：已启用    已连接     专用    以太网
                        # 或 Enabled   Connected   Dedicated   Ethernet
                        if '已禁用' in line or 'Disabled' in line:
                            return '禁用'
                        elif '已启用' in line or 'Enabled' in line:
                            return '启用'
            return '未知'
        except Exception as e:
            print(f"获取网卡状态失败: {e}")
            return '未知'

    def show_adapter_config(self, adapter=None):
        """显示指定网卡的配置信息到详情区（self.adapter_configs为List[Dict]类型）"""
        if adapter is None:
            adapter = self.adapter_var.get()
        config = None
        for item in self.adapter_configs:
            # 网卡名字段通常为 'interface'
            if item.get('interface') == adapter:
                config = item
                break
        # 更新详情区
        if config:
            self.ip_var.set(config.get('ip', ''))
            self.mask_var.set(config.get('mask', ''))
            self.gateway_var.set(config.get('gateway', ''))
            self.dns1_var.set(config.get('dns1', ''))
            self.dns2_var.set(config.get('dns2', ''))
        else:
            self.ip_var.set('')
            self.mask_var.set('')
            self.gateway_var.set('')
            self.dns1_var.set('')
            self.dns2_var.set('')

    def on_adapter_changed(self, event=None):
        """网卡选择变化时，显示对应网卡的配置"""
        adapter = self.adapter_var.get()
        self.show_adapter_config(adapter)

class interfaces_info:
    def __init__(self):
        self.system = platform.system()

    def get_all_interfaces_info(self) -> List[Dict]:
        """
        获取本机所有网卡的详细信息
        """
        if self.system == "Windows":
            return self._get_windows_all_interfaces_info()
        elif self.system == "Linux":
            return self._get_linux_all_interfaces_info()
        else:
            raise NotImplementedError(f"不支持的操作系统: {self.system}")
    
    def _get_windows_all_interfaces_info(self) -> List[Dict]:
        """
        Windows系统获取所有网卡信息
        """
        interfaces_info = []
        
        try:
            # 使用ipconfig /all获取所有网络接口信息
            result = subprocess.run(['ipconfig', '/all'], 
                                  capture_output=True, shell=True)
            output = result.stdout.decode('gbk', errors='ignore')
            
            if result.returncode == 0:
                # output = result.stdout
                
                # 按适配器分割输出
                adapters = re.split(r'\r?\n\r?\n(?=\w)', output)
                
                for adapter_section in adapters:
                    if 'adapter' in adapter_section.lower() or '适配器' in adapter_section:
                        info = self._parse_windows_adapter_info(adapter_section)
                        if info:
                            interfaces_info.append(info)
            
            # 如果ipconfig失败，尝试使用netsh
            if not interfaces_info:
                interfaces_info = self._get_windows_interfaces_via_netsh()
                
        except Exception as e:
            print(f"获取Windows网卡信息失败: {e}")
        
        return interfaces_info
    
    def _parse_windows_adapter_info(self, adapter_section: str) -> Dict:
        """
        解析Windows单个适配器信息
        """
        info = {
            'interface': '',
            'description': '',
            'physical_address': '',
            'ip': '',
            'mask': '',
            'gateway': '',
            'dns1': '',
            'dns2': '',
            'status': ''
        }
        
        try:
            # 提取适配器名称
            name_match = re.search(r'(Ethernet adapter|无线局域网适配器|适配器)\s+([^\r\n:]+):', adapter_section)
            if name_match:
                info['interface'] = name_match.group(2).strip()
            else:
                # 尝试其他格式
                name_match = re.search(r'([^\r\n:]+):\r?\n', adapter_section)
                if name_match:
                    info['interface'] = name_match.group(1).strip()
            
            # 物理地址(MAC)
            mac_match = re.search(r'(Physical Address|物理地址)[\. ]*:\s*([^\r\n]+)', adapter_section)
            if mac_match:
                info['physical_address'] = mac_match.group(2).strip()
            
            # 状态
            status_match = re.search(r'(Media State|媒体状态)[\. ]*:\s*([^\r\n]+)', adapter_section)
            if status_match:
                info['status'] = status_match.group(2).strip()
            
            # 描述
            desc_match = re.search(r'(Description|描述)[\. ]*:\s*([^\r\n]+)', adapter_section)
            if desc_match:
                info['description'] = desc_match.group(2).strip()
            
            # IP地址
            ip_match = re.search(r'(IPv4 Address|IPv4 地址)[\. ]*:\s*([^\r\n\(]+)', adapter_section)
            if ip_match:
                info['ip'] = ip_match.group(2).strip()
            
            # 子网掩码
            mask_match = re.search(r'(Subnet Mask|子网掩码)[\. ]*:\s*([^\r\n]+)', adapter_section)
            if mask_match:
                info['mask'] = mask_match.group(2).strip()
            
            # 按行处理，找到“默认网关”行及其后所有缩进行
            gateway_ip = ''
            lines = adapter_section.splitlines()
            gw_lines = []
            # 允许前面有空白的字段名匹配
            field_pattern = re.compile(r'^[\s　]*[\w\u4e00-\u9fa5\s]+[\. 　]*[:：]', re.UNICODE)

            for idx, line in enumerate(lines):
                m = re.search(r'(Default Gateway|默认网关)[\. ]*:(.*)$', line)
                if m:
                    # 收集本行冒号后的所有内容（可能有IPv6/IPv4）
                    rest = m.group(2).strip()
                    if rest:
                        gw_lines.append(rest)
                    # 收集后续缩进行，遇到下一个字段名或空行就停
                    for next_line in lines[idx+1:]:
                        if next_line.strip() == '':
                            break
                        if field_pattern.match(next_line):
                            break
                        if re.match(r'^\s+\S+', next_line):
                            gw_lines.append(next_line.strip())
                        else:
                            break
                    break

            # 查找第一个IPv4地址
            for gw in gw_lines:
                if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', gw):
                    gateway_ip = gw
                    break

            if gateway_ip:
                info['gateway'] = gateway_ip
            
            # DNS服务器
            dns_matches = re.search(r'(DNS Servers|DNS 服务器).*?(?=\n\s*\n|\Z)', adapter_section, re.DOTALL | re.IGNORECASE)
            if dns_matches:
                # 在DNS段落中提取所有IP地址
                ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', dns_matches.group(0))
                
                # 验证并返回结果
                dns_info = {'dns1': '', 'dns2': ''}
                valid_ips = []
                
                for ip in ips:
                    parts = ip.split('.')
                    if all(0 <= int(part) <= 255 for part in parts):
                        valid_ips.append(ip)
                
                if len(valid_ips) >= 1:
                    dns_info['dns1'] = valid_ips[0]
                if len(valid_ips) >= 2:
                    dns_info['dns2'] = valid_ips[1]
                    
                info['dns1'] = dns_info['dns1']
                info['dns2'] = dns_info['dns2']
        
        except Exception as e:
            print(f"解析适配器信息失败: {e}")
        
        # 只返回有IP地址的有效接口
        if info['ip'] and info['interface']:
            return info
        return {}
    
    def _get_windows_interfaces_via_netsh(self) -> List[Dict]:
        """
        使用netsh获取Windows网卡信息（备用方法）
        """
        interfaces_info = []
        
        try:
            # 获取接口列表
            result = subprocess.run(['netsh', 'interface', 'show', 'interface'], 
                                  capture_output=True, text=True, shell=True, encoding='gbk')
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if '已连接' in line or 'Connected' in line or '启用' in line or 'Enabled' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            interface_name = ' '.join(parts[3:])
                            
                            # 获取该接口的详细信息
                            interface_info = self._get_windows_interface_detail(interface_name)
                            if interface_info:
                                interfaces_info.append(interface_info)
        
        except Exception as e:
            print(f"通过netsh获取接口信息失败: {e}")
        
        return interfaces_info
    
    def _get_windows_interface_detail(self, interface_name: str) -> Dict:
        """
        获取Windows单个接口的详细信息
        """
        info = {
            'interface': interface_name,
            'ip': '',
            'mask': '',
            'gateway': '',
            'dns1': '',
            'dns2': ''
        }
        
        try:
            # 获取IP配置
            cmd = ['netsh', 'interface', 'ip', 'show', 'config', f'name="{interface_name}"']
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='gbk')
            
            if result.returncode == 0:
                output = result.stdout
                
                # 提取IP地址
                ip_match = re.search(r'IP Address:\s*([\d\.]+)', output)
                if ip_match:
                    info['ip'] = ip_match.group(1)
                
                # 提取子网掩码
                mask_match = re.search(r'Subnet Prefix:\s*([\d\.]+)/(\d+)', output)
                if mask_match:
                    info['mask'] = self._cidr_to_mask(mask_match.group(2))
                else:
                    mask_match = re.search(r'IP Address:\s*[\d\.]+\s*\(([\d\.]+)\)', output)
                    if mask_match:
                        info['mask'] = mask_match.group(1)
                
                # 提取网关
                gateway_match = re.search(r'Default Gateway:\s*([\d\.]+)', output)
                if gateway_match:
                    info['gateway'] = gateway_match.group(1)
            
            # 获取DNS配置
            cmd = ['netsh', 'interface', 'ip', 'show', 'dns', f'name="{interface_name}"']
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='gbk')
            
            if result.returncode == 0:
                output = result.stdout
                dns_matches = re.findall(r'(配置的 DNS 服务器|Configured DNS Servers):\s*([\d\.]+)', output)
                if dns_matches:
                    dns_list = re.findall(r'[\d\.]+', output[output.find(dns_matches[0][1]):])
                    if dns_list:
                        info['dns1'] = dns_list[0]
                        if len(dns_list) > 1:
                            info['dns2'] = dns_list[1]
        
        except Exception as e:
            print(f"获取接口详细信息失败: {e}")
        
        return info
    
    def _cidr_to_mask(self, cidr: str) -> str:
        """
        CIDR转换为子网掩码
        """
        try:
            cidr = int(cidr)
            mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
            return '.'.join([str((mask >> (24 - i * 8)) & 0xff) for i in range(4)])
        except:
            return ''
    
    def print_interfaces_info(self, interfaces_info: List[Dict]):
        """
        格式化打印网卡信息
        """
        if not interfaces_info:
            print("未找到有效的网络接口")
            return
        
        print("=" * 80)
        print("本机网络接口信息")
        print("=" * 80)
        
        for i, info in enumerate(interfaces_info, 1):
            print(f"\n[{i}] 网卡名称: {info.get('interface', 'N/A')}")
            if info.get('description'):
                print(f"    描述:     {info.get('description', 'N/A')}")
            if info.get('physical_address'):
                print(f"    MAC地址:  {info.get('physical_address', 'N/A')}")
            print(f"    IP地址:   {info.get('ip', 'N/A')}")
            print(f"    子网掩码: {info.get('mask', 'N/A')}")
            print(f"    默认网关: {info.get('gateway', 'N/A')}")
            print(f"    DNS1:     {info.get('dns1', 'N/A')}")
            print(f"    DNS2:     {info.get('dns2', 'N/A')}")
            if info.get('status'):
                print(f"    状态:     {info.get('status', 'N/A')}")
            print("-" * 60)
        
        print(f"\n总共找到 {len(interfaces_info)} 个活动的网络接口")

def main():
    root = tk.Tk()
    app = NetworkConfigManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()