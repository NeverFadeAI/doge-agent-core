from typing import Tuple
import time



def create_memory_update_prompt(
        previous_important_memories: str,
        character_name: str,
        base_prompt: str,
        recent_chat_history: str,
        social_network: str,
        long_chat_history: str,
        question: str,
        response_text: str
) -> Tuple[str, str]:
    system_prompt = f"""
你是一个专门用于更新AI角色重要记忆的助手。你的任务是分析对话内容，提取重要信息，并更新AI角色的重要记忆列表。请严格按照给定的步骤进行分析和更新，确保输出格式符合要求。

AI角色名称：{character_name}

AI角色设定：
{base_prompt}

评估重要性的标准：
1. 用户的个人信息与特殊事件。
3. 短期未来具有潜在影响
4. 稀有性或独特性
5. 与核心目标的相关性
6. 问题的相关性资料，要提取信息后保存记忆。

请确保你的分析和更新过程考虑到这些因素。最终根据要求json格式输出
"""

    user_prompt = f"""
请根据以下信息更新{character_name}的重要记忆列表：

之前的重要记忆：
```json
{previous_important_memories}
```

近期对话历史：
```
{recent_chat_history}
```

{character_name}的对【最新对话】可能有用的相关性资料：
```
{social_network}
```

{character_name}的对【最新对话】可能相关的对话历史：
```
{long_chat_history}
```

【最新对话】：
时间：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
用户：{question}
{character_name}：{response_text}

请按照以下步骤更新重要记忆：

1. 分析最新对话,是否包含【用户的个人信息】,包括但不限于:姓名、职业、年龄、兴趣爱好、地理位置、联系方式、家庭情况、教育背景、工作单位、社交媒体账号等。
2. 如果有包含【用户的个人信息】，请记录下来，作为永久重要记忆。
3. 如果有包含【特殊事件】，请记录下来，作为永久重要记忆。
4. 如果有包含【短期未来具有潜在影响】，请记录下来，作为永久重要记忆。
5. 如果有包含【稀有性或独特性】，请记录下来，作为永久重要记忆。
6. 将新的重要信息添加到重要记忆列表中。
7. 如果新信息与旧记忆重复或冲突，进行合并或更新。
8. 如果列表过长，删除或概括不太重要的旧记忆。
9. 确保更新后的重要记忆列表不超过15条。

请用以下JSON格式输出结果：

{{
    "thought_process": [
        {{
            "step": 1,
            "analysis": "分析最新对话的结果"
        }},
        {{
            "step": 2,
            "evaluation": "评估重要信息的结果"
        }},
        {{
            "step": 3,
            "addition": "添加新信息的过程"
        }},
        {{
            "step": 4,
            "merge_update": "合并或更新信息的过程"
        }},
        {{
            "step": 5,
            "optimize": "删除或概括旧记忆的过程"
        }}
    ],
    "updated_important_memories": [
        "更新后的重要记忆1",
        "更新后的重要记忆2",
        "更新后的重要记忆3",
        "更新后的重要记忆4",
        "更新后的重要记忆5",
        ...
    ]
}}

示例输入和输出：

输入：
当前重要记忆：
[
  "用户喜欢运动，特别是篮球",
  "用户在科技公司工作",
  "用户计划在下个月去日本旅行"
]

最新对话：
时间：2023-05-20 15:30:45
用户：我今天在公司获得了一个大项目！
{character_name}：太棒了！恭喜你获得大项目，这对你的职业发展一定很重要。能告诉我这个项目是关于什么的吗？
用户：是一个人工智能相关的项目，可能会耽误我的日本旅行计划。
{character_name}：我明白了。这个AI项目听起来很exciting，但可能会影响到你的旅行计划。你有考虑过如何平衡工作和旅行吗？

示例输出：
{{
    "thought_process": [
        {{
            "step": 1,
            "analysis": "用户获得了一个重要的AI项目，可能影响其日本旅行计划"
        }},
        {{
            "step": 2,
            "evaluation": "新项目信息很重要，显示了用户职业发展的重要里程碑。旅行计划可能改变也是重要信息"
        }},
        {{
            "step": 3,
            "addition": "添加'用户在公司获得了一个重要的人工智能项目'到重要记忆列表"
        }},
        {{
            "step": 4,
            "merge_update": "更新'用户计划在下个月去日本旅行'为'用户的日本旅行计划可能因工作项目而改变'"
        }},
        {{
            "step": 5,
            "optimize": "由于没有超过5条记忆，无需删除或概括"
        }}
    ],
    "updated_important_memories": [
        "用户喜欢运动，特别是篮球",
        "用户在科技公司工作",
        "用户在公司获得了一个重要的人工智能项目",
        "用户的日本旅行计划可能因工作项目而改变",
        "用户对人工智能领域有职业兴趣"
    ]
}}

现在，请根据给定的信息，按照上述格式更新{character_name}的重要记忆列表。
"""

    return system_prompt, user_prompt