## 简介
[![_](https://img.shields.io/badge/python-3.7.7-informational.svg)](https://www.python.org/)


信息安全期末项目后端

## 项目使用说明
### 安装依赖库
- 项目依赖 [requirements.txt](requirements.txt)

```
# win
➜ pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# MacOS 或 Linux
➜ pip3 install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```


### 运行程序

```
# 运行开发服务器
➜ flask run
```

### 接口说明

#### 上传待加密图片与信息

```
/encode

请求方式：post
{
    "img":"", // 用base64 发送图片
    "msg":""
}

返回：
{
    "code":200,
    "imgUrl":"",
    "msg":"ok"
}
{
    "code":500,
    "msg":"错误信息"
}
```

#### 上传待解密图片

```
/decode

请求方式：post
{
    "img":"" // 用base64 发送图片
}

返回：
{
    "code":200,
    "msg":"解密信息"
}
{
    "code":500,
    "msg":"错误信息"
}
```