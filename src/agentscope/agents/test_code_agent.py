import agentscope
from agentscope.agents import CodeAgent
from agentscope.service import (
    bing_search,  # or google_search,
    read_text_file,
    write_text_file,
    ServiceToolkit,
    ServiceResponse,
    ServiceExecStatus,
)
from agentscope.message import Msg


def web_serarch(
    query: str, engine: str, api_key: str, num_results: int = 10
) -> ServiceResponse:
    """
    Search the web using the given search engine.

    Args:
        query: The query string.
        engine: The search engine to use.
        api_key: The API key for the search engine.
        num_results: The number of results to return.

    Returns:
        List[str]: The search results.
    """
    # Search the web using the given search engine
    data = (
        f"Searching the web using {engine} with query: {query} and API key: {api_key}"
    )

    return ServiceResponse(ServiceExecStatus.SUCCESS, data)


def get_weather(location, unit) -> ServiceResponse:
    """
    Get the weather information for a specified location.

    Args:
        location (str): The location for which to get the weather.
        unit (str): The temperature unit, 'c' for Celsius, 'f' for Fahrenheit.

    Returns:
        dict: A dictionary containing weather information.
    """
    # Validate parameters
    if not isinstance(location, str):
        raise TypeError("location must be a string")
    if unit not in ["c", "f"]:
        raise ValueError("unit must be 'c' or 'f'")

    # Simulate getting weather information
    # In practice, you would call a real weather API here
    sample_weather_data = {
        "location": location,
        "temperature": 20 if unit == "c" else 68,
        "unit": unit,
        "description": "Clear",
    }

    return ServiceResponse(ServiceExecStatus.SUCCESS, sample_weather_data)


service_toolkit = ServiceToolkit()

service_toolkit.add(web_serarch, api_key="xxx", num_results=3)

service_toolkit.add(get_weather)

print(service_toolkit.tools_instruction)
# print(service_toolkit.json_schemas)
tools = []

for tool in service_toolkit.service_funcs.keys():
    tools.append(service_toolkit.json_schemas[tool])
print(tools)
# qwen_model_config =     {
#         "model_type": "openai_chat",
#         "config_name": "vllm_qwen2.5-72b-chat",
#         "model_name": "Qwen2.5-72B-Chat",
#         "api_key": "test",  # Load from env if not provided
#         "client_args": {
#             "base_url": "http://10.3.2.203:8000/v1/",  # 用于指定 API 的基础 URL
#         },
#         "generate_args": {
#             "temperature": 0.5,
#         },
#     },

# azure_model_config = {
#     "api_base": "https://ai2team.openai.azure.com/",
#     "api_key": "3d97a348a4a24119ac590d12a4751509",
#     "api_version": "2024-06-01",
#     "config_name": "gpt4o-mini",
#     "model_type": "litellm_chat",
#     "model_name": "azure/ai2team-gpt4o",
#     "stream": False
# }

# deepseek_model_config = {
#     "config_name": "deepseek-chat",
#     "model_type": "openai_chat",
#     "model_name": "deepseek-chat",
#     "api_key": "sk-90bb5d4f19cb40008658523cc58ea7f5",
#     "client_args": {
#         "base_url": "https://api.deepseek.com",
#     },
#     "stream": False,
# }

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
    ]
)

# agent1 = DialogAgent(name="Guofeng Yi", model_config_name="gpt4o-mini", sys_prompt="You are a new student in Anhui University.")

agent1 = CodeAgent(
    name="Guofeng Yi",
    model_config_name="vllm_qwen2.5-72b-chat",
    sys_prompt="You are a new student in Anhui University.",
    service_toolkit=service_toolkit,
)

response = agent1(Msg(name="user", role="user", content="你好，上海今天的天气怎么样"))
