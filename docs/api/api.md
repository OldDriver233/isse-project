## AI沟通相关功能

### *GET* /api/v1/chat

#### 请求体

```jsonc
{
    "character": "xxx", // 描述所需模仿的角色
    "messages": [
        // 描述用户的对话记录
        {
            "role": "user", // 这里一般有3种参数：system, user, assistant. 
            // 三者的含义可参照https://help.aliyun.com/zh/model-studio/multi-round-conversation
            "content": "Lorem ipsum" // 系统Prompt，用户输入或者模型的输出
        }
    ],
    "stream": false, // 可选，表征是否为流式输出
    "temperature": 0.5, // 可选，模型采样温度
}
```

#### 响应体（非流式输出）

```jsonc
{
    "result": { 
        "message": {
            // 标准的OpenAI模型其实会返回一个 choices 数组，内容为模型输出内容以及概率信息，此处我们暂且不考虑多个可能返回的情形
            "role": "assistant",
            "content": "Lorem ipsum"
        },
        "finish_reason": "stop"
    },
    "usage": {
        // Token 用量。考虑到后续运维可能需要，故保留
        "prompt_tokens": 114,
        "completion_tokens": 514,
        "total_tokens": 628,
        "prompt_tokens_details": {
            "cached_tokens": 90
        }
    },
    "created": 1762669782, // 以秒为单位的 Unix timestamp
    // 一个小坑：JS/TS 调用 Date.now() 返回的时间戳单位是毫秒
    "id": "xxx-9303a5a3-325f-4855-98b8-34de84a8a9af" // 前缀为模仿的角色对应代码，后面为UUID
}
```

#### 响应体（流式输出）

OpenAI 采用 Server Sent Events(SSE) 的方式进行流式输出数据的传输。相关内容可参考 [服务器发送事件 - Web API | MDN](https://developer.mozilla.org/zh-CN/docs/Web/API/Server-sent_events)

```jsonc
data: {"result": {"delta": {"role": "assistant", "content": ""}, "finish_reason": null}, "usage": null, "created": 1762669782, "id": "xxx-9303a5a3-325f-4855-98b8-34de84a8a9af"}
data: {"result": {"delta": {"content": "Lorem ipsum"}, "finish_reason": null}, "usage": null, "created": 1762669782, "id": "xxx-9303a5a3-325f-4855-98b8-34de84a8a9af"}
data: {"result": {"delta": {"content": ""}, "finish_reason": "stop"}, "usage": null, "created": 1762669782, "id": "xxx-9303a5a3-325f-4855-98b8-34de84a8a9af"}
data: {"usage": {"prompt_tokens": 114, "completion_tokens": 514, "total_tokens": 628, "prompt_tokens_details": { "cached_tokens": 90 }}, "created": 1762669782, "id": "xxx-9303a5a3-325f-4855-98b8-34de84a8a9af"}
data: [DONE]
```

## 遥测功能相关

### *POST* /api/v1/telemetry

#### 请求体

```jsonc
{
    "user_id": "8f9678c0-979f-40b9-b0e8-d4544ae77b66", // 用户对应的UUID
    // 保留字段，只是搓Demo的话跟随浏览器cookie就行
    "rating": {
        // 用户评价
        "overall_rating": 1, // 1-10之间，越高越好
        "comment": "114514" // 用户评论
    },
    "messages": [
        {
            "role": "assistant",
            "content": "网络错误，请稍后重试。"
        }
    ]
}
```

#### 响应体

```json
{
    "result": "ok"
}
```