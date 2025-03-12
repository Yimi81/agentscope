# -*- coding: utf-8 -*-
"""A simple example for conversation between user and assistant agent."""
import agentscope
from agentscope.agents import DialogAgent
from agentscope.agents.user_agent import UserAgent
from agentscope.pipelines.functional import sequentialpipeline


def main() -> None:
    """A basic conversation demo"""

    agentscope.init(
        model_configs=[
            {
                "model_type": "openai_chat",
                "config_name": "vllm_qwen2.5-72b-chat",
                "model_name": "Qwen2.5-72B-Chat",
                "api_key": "test",  # Load from env if not provided
                "client_args": {
                    "base_url": "http://10.3.2.203:8000/v1/",  # 用于指定 API 的基础 URL
                },
                "generate_args": {
                    "temperature": 0.5,
                },
            },
        ],
        project="Multi-Agent Conversation",
        save_api_invoke=True,
    )

    # Init two agents   
    dialog_agent = DialogAgent(
        name="Assistant",
        sys_prompt="You're a helpful assistant.",
        model_config_name="vllm_qwen2.5-72b-chat",  # replace by your model config name
    )
    user_agent = UserAgent()

    # start the conversation between user and assistant
    x = None
    while x is None or x.content != "exit":
        x = sequentialpipeline([dialog_agent, user_agent], x)


if __name__ == "__main__":
    main()
