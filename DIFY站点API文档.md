# Dify API 文档

## 概述

本文档描述了 Dify 平台的管理 API 接口，包括应用管理、API 密钥管理、标签管理等功能。

## 基础信息

- 基础 URL: `{base_url}/console/api`
- 认证方式: Bearer Token (通过登录获取)

## 接口列表

### 1. 登录认证

**路由**: `/login`  
**方法**: POST  
**描述**: 登录 Dify 平台并获取访问令牌

**请求参数**:

```json
{
  "email": "string",
  "language": "string",
  "password": "string",
  "remember_me": boolean
}
```

**响应**:

```json
{
  "data": {
    "access_token": "string",
    "refresh_token": "string"
  }
}
```

---

### 2. 应用管理

#### 2.1 获取应用列表

**路由**: `/apps`  
**方法**: GET  
**查询参数**:

- `page`: 页码 (默认 1)
- `limit`: 每页数量 (默认 100)
- `name`: 应用名称过滤
- `is_created_by_me`: 是否只查询当前用户创建的应用
- `keywords`: 关键词搜索
- `tagIDs`: 标签 ID 列表 (分号分隔)

**响应**:

```json
{
  "page": 1,
  "limit": 100,
  "total": 0,
  "has_more": false,
  "data": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "mode": "string",
      "icon_type": "string",
      "icon": "string",
      "icon_background": "string",
      "icon_url": "string",
      "model_config": {},
      "workflow": {},
      "created_by": "string",
      "created_at": 0,
      "updated_by": "string",
      "updated_at": 0,
      "tags": []
    }
  ]
}
```

#### 2.2 创建应用

**路由**: `/apps`  
**方法**: POST  
**请求体**:

```json
{
  "name": "string",
  "description": "string",
  "mode": "string",
  "icon": "string",
  "icon_background": "string",
  "icon_type": "string"
}
```

**响应**:

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "mode": "string",
  "icon": "string",
  "icon_background": "string",
  "status": "string",
  "api_status": "string",
  "api_rpm": 0,
  "api_rph": 0,
  "is_demo": false,
  "created_at": 0
}
```

#### 2.3 获取单个应用信息

**路由**: `/apps/{app_id}`  
**方法**: GET  
**响应**:

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "mode": "string",
  "icon_type": "string",
  "icon": "string",
  "icon_background": "string",
  "icon_url": "string",
  "enable_site": true,
  "enable_api": true,
  "model_config": {},
  "workflow": {},
  "site": {},
  "api_base_url": "string",
  "use_icon_as_answer_icon": true,
  "created_by": "string",
  "created_at": 0,
  "updated_by": "string",
  "updated_at": 0,
  "deleted_tools": []
}
```

#### 2.4 更新应用

**路由**: `/apps/{app_id}`  
**方法**: PUT  
**请求体**:

```json
{
  "name": "string",
  "description": "string",
  "icon": "string",
  "icon_background": "string",
  "icon_type": "string",
  "use_icon_as_answer_icon": true
}
```

**响应**:

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "mode": "string",
  "icon": "string",
  "icon_background": "string",
  "icon_type": "string"
}
```

#### 2.5 删除应用

**路由**: `/apps/{app_id}`  
**方法**: DELETE  
**响应**: 204 No Content

---

### 3. 应用 DSL 管理

#### 3.1 导出应用 DSL

**路由**: `/apps/{app_id}/export`  
**方法**: GET  
**查询参数**:

- `include_secret`: 是否包含密钥 (默认 false)

**响应**:

```json
{
  "data": "string"
}
```

#### 3.2 导入应用 DSL

**路由**: `/apps/imports`  
**方法**: POST  
**请求体**:

```json
{
  "mode": "yaml-content",
  "yaml_content": "string",
  "app_id": "string"
}
```

**响应**:

```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "mode": "string",
  "icon": "string",
  "icon_background": "string",
  "icon_type": "string"
}
```

---

### 4. API 密钥管理

#### 4.1 创建 API 密钥

**路由**: `/apps/{app_id}/api-keys`  
**方法**: POST  
**响应**:

```json
{
  "id": "string",
  "type": "string",
  "token": "string",
  "last_used_at": null,
  "created_at": 0
}
```

#### 4.2 获取 API 密钥列表

**路由**: `/apps/{app_id}/api-keys`  
**方法**: GET  
**响应**:

```json
{
  "data": [
    {
      "id": "string",
      "type": "string",
      "token": "string",
      "last_used_at": null,
      "created_at": 0
    }
  ]
}
```

#### 4.3 删除 API 密钥

**路由**: `/apps/{app_id}/api-keys/{api_key_id}`  
**方法**: DELETE  
**响应**: 204 No Content

---

### 5. 标签管理

#### 5.1 获取标签列表

**路由**: `/tags`  
**方法**: GET  
**查询参数**:

- `type`: 标签类型 (如'app')

**响应**:

```json
[
  {
    "id": "string",
    "name": "string",
    "binding_count": "string"
  }
]
```

#### 5.2 创建标签

**路由**: `/tags`  
**方法**: POST  
**请求体**:

```json
{
  "name": "string",
  "type": "string"
}
```

**响应**:

```json
{
  "id": "string",
  "name": "string",
  "binding_count": "string"
}
```

#### 5.3 更新标签

**路由**: `/tags/{tag_id}`  
**方法**: PATCH  
**请求体**:

```json
{
  "name": "string"
}
```

**响应**:

```json
{
  "id": "string",
  "name": "string",
  "type": "string",
  "binding_count": "string"
}
```

#### 5.4 删除标签

**路由**: `/tags/{tag_id}`  
**方法**: DELETE  
**响应**: 204 No Content

---

### 6. 标签绑定管理

#### 6.1 绑定标签到应用

**路由**: `/tag-bindings/create`  
**方法**: POST  
**请求体**:

```json
{
  "target_id": "string",
  "tag_ids": ["string"],
  "type": "string"
}
```

**响应**: {}

#### 6.2 从应用移除标签

**路由**: `/tag-bindings/remove`  
**方法**: POST  
**请求体**:

```json
{
  "target_id": "string",
  "tag_ids": ["string"],
  "type": "string"
}
```

**响应**: {}

---

### 7. 工具提供者管理

#### 7.1 获取工具提供者列表

**路由**: `/workspaces/current/tool-providers`  
**方法**: GET  
**描述**: 获取当前工作空间中的所有工具提供者列表

**响应**:

```json
[
  {
    "id": "string",
    "author": "string",
    "name": "string",
    "plugin_id": "string",
    "plugin_unique_identifier": "string",
    "description": {
      "en": "string",
      "zh-Hans": "string"
    },
    "icon": "string",
    "label": {
      "en": "string",
      "zh-Hans": "string"
    },
    "type": "string",
    "team_credentials": {},
    "is_team_authorization": boolean,
    "allow_delete": boolean,
    "tools": [],
    "labels": []
  }
]
```

#### 7.2 发布工作流应用

**路由**: `/apps/{app_id}/workflows/publish`  
**方法**: POST  
**描述**: 发布指定的工作流应用

**请求体**:

```json
{
  "marked_comment": "string",
  "marked_name": "string"
}
```

**响应**:

```json
{
  // 响应内容取决于具体实现
}
```

#### 7.3 更新工作流工具

**路由**: `/workspaces/current/tool-provider/workflow/update`  
**方法**: POST  
**描述**: 更新指定工作流工具的配置

**请求体**:

```json
{
  "name": "string",
  "description": "string",
  "icon": {
    "content": "string",
    "background": "string"
  },
  "label": "string",
  "parameters": [
    {
      "name": "string",
      "description": "string",
      "form": "string"
    }
  ],
  "labels": [],
  "privacy_policy": "string",
  "workflow_tool_id": "string"
}
```

**响应**:

```json
{
  // 响应内容取决于具体实现
}
```

---

## 应用模式枚举

```python
class DifyAppMode:
    CHAT = "chat"  # 聊天助手chatbot
    AGENT_CHAT = "agent-chat"  # Agent - 代理模式
    COMPLETION = "completion"  # 文本生成应用
    ADVANCED_CHAT = "advanced-chat"  # Chatflow - 高级聊天流
    WORKFLOW = "workflow"  # 工作流应用
```

## 工具提供者类型枚举

```python
class ToolProviderType:
    BUILTIN = "builtin"  # 内置工具
    WORKFLOW = "workflow"  # 工作流工具
    PLUGIN = "plugin"  # 插件工具
```
