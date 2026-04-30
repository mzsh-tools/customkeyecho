# CustomKeyEcho 使用说明

## 环境搭建

```bash
# 创建 Conda 环境
conda create -n CustomKeyEcho python=3.12 --yes

# 安装依赖
conda run -n CustomKeyEcho pip install PySide6 pynput platformdirs
```

> 如遇 conda SSL 问题，使用清华镜像源：
> ```bash
> conda create -n CustomKeyEcho python=3.12 --yes --override-channels -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
> ```

## 启动

```bash
eval "$(conda shell.bash hook 2>/dev/null)" && conda activate CustomKeyEcho && python Main.py
```

## 使用步骤

### 1. 选择目标窗口

从下拉列表选择游戏窗口，点击"刷新列表"更新。支持手动输入窗口标题。留空则不做焦点检测。

### 2. 录制按键

点击"录制按键"→ 按下要循环的键盘按键或鼠标按键 → 按键实时添加到列表 → 按**回车键**结束录制。

支持的按键类型：
- 键盘：任意按键（字母、数字、F 键、空格等）
- 鼠标：左键、右键、中键、侧键 1/2

管理序列：
- "删除选中"：删除列表中选中的按键
- "清空"：清空整个序列

### 3. 设置按键间隔

调整最小值和最大值（单位 ms），每次按键之间的延迟从该区间随机取值。

- 默认：1000~1500 ms
- 下限：10 ms（不可低于此值）
- 随机化可降低被反作弊系统检测的风险

### 4. 设置快捷键

点击快捷键按钮 → 按下想要的触发键。默认为 **F6**。

### 5. 开始/停止

按下快捷键切换运行状态：

- 首次按下 → 开始循环
- 再次按下 → 停止
- 再按 → 重新开始
- 序列执行完一轮后自动从头循环

### 焦点检测

设置了目标窗口后：
- 窗口在前台 → 正常发送按键
- 窗口失去焦点 → 自动暂停，状态显示"已暂停（等待窗口焦点）"
- 窗口恢复焦点 → 自动继续

## 配置文件

配置自动保存在 `%LOCALAPPDATA%\CustomKeyEcho\Config.json`，包含按键序列、延迟设置、快捷键和目标窗口。下次启动自动恢复。

## 常见问题

### 按键在游戏中无效

- 尝试以管理员权限运行程序
- 部分游戏使用内核级反作弊，SendInput 可能被拦截

### 无法录制回车键

回车键用于结束录制，无法作为按键序列的一部分录入。

### 延迟设置不生效

修改延迟后需要停止并重新启动回放才能生效。
