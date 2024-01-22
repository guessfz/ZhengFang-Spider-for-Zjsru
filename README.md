# ZhengFang-Spider-for-Zjsru
# 正方教务系统信息获取工具

该Python脚本可用于获取教务系统个人信息和成绩，以及成绩更新监控和通知。

## 使用

1. 在 `config.py` 文件中配置您的个人信息，包括学号、密码和其他必要的信息。

2. 使用以下命令安装所需的依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 功能说明


### 1. 获取信息

- 使用 `run_spider.py` 脚本可以登录教务系统并获取学生信息和成绩信息。

### 2. 计算GPA

- `run_spider.py` 脚本还可用于计算学期和学年GPA。

### 3. 成绩监控

- 您可以通过定时运行 `gradeMonitor.py` 脚本，设置成绩更新的监控，当成绩有变化时，会发送通知提醒您。


#### PushPlus通知配置

- 如果您需要通过PushPlus发送通知，可以按照以下步骤配置PushPlus Token：

   - 登录 [PushPlus](https://www.pushplus.plus/)
   - 在 [Token页面](https://www.pushplus.plus/api/open/user/token) 复制您的Token

### 注意事项

- 由于验证码有概率识别错误，如果登录失败，请尝试重新运行脚本。

- 如果您的教务系统登录页面包含验证码，且验证码的图片链接为 `xxxxxx/CheckCode.aspx?SafeKey=97198bdf1f2143059f3ccf570c7c10b1`，则大概率可以使用此工具。
