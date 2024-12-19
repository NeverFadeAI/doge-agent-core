# doge-agent-core

AI Agent-driven backend for dogecoin.ai platform.

## Project Structure
```python
doge_agent_core/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py           # Agent基类
│   │   ├── creative_agent.py # 创意生成Agent
│   │   ├── vision_agent.py   # 视觉分析Agent
│   │   ├── market_agent.py   # 市场分析Agent
│   │   └── coordinator.py    # Agent协调器
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   ├── logger.py        # 日志管理
│   │   └── exceptions.py    # 异常定义
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── short_term.py    # 短期记忆管理
│   │   └── long_term.py     # 长期记忆管理
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── grok.py         # Grok模型接口
│   │   └── flux.py         # Flux图像生成接口
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── templates.py    # 提示词模板
│   │   └── manager.py      # 提示词管理
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── react.py        # ReAct工具
│   │   └── reflection.py   # 反思工具
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── milvus_manager.py   # Milvus向量数据库存储
│   │   ├── mysql.py            # MySQL存储
│   │   └── redis.py            # Redis缓存
│   │
│   └── api/
│       ├── __init__.py
│       ├── routes.py      # API路由
│       └── models.py      # 数据模型
│
├── tests/                 # 测试用例
│   ├── __init__.py
│   ├── test_agents/
│   ├── test_memory/
│   └── test_api/
│
├── examples/             # 示例代码
│   ├── basic_usage.py
│   └── webui_demo.py
│
├── docs/                # 文档
│   ├── api.md
│   └── development.md
│
├── requirements.txt     # 依赖
├── api_doge.py            # 安装配置
└── README.md           # 项目说明
