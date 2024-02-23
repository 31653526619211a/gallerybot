# 使用官方Python运行时环境作为父镜像
FROM python:3.8-slim

# 设置工作目录为/app
WORKDIR /app

# 将当前目录下的所有文件复制到容器中的/app
COPY . /app

# 安装requirements.txt中指定的所有依赖
RUN pip install --no-cache-dir -r requirements.txt

# 使端口80可用于与世界外部的通信
EXPOSE 80

# 定义环境变量
ENV NAME World

# 当容器启动时运行Python脚本
CMD ["python", "./main.py"]
