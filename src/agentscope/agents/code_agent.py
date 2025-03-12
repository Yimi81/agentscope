# -*- coding: utf-8 -*-
"""An agent class that implements the CodeAct algorithm. The agent executable Python code to consolidate LLM agents'actions into a unified action space. 
More details can be found in the paper https://arxiv.org/pdf/2402.01030.
"""
import re
import ast
from typing import Optional, Union, Sequence

from agentscope.exception import ResponseParsingError
from agentscope.agents import AgentBase
from agentscope.message import Msg
from agentscope.parsers import RegexTaggedContentParser
from agentscope.service import (
    ServiceToolkit,
    ServiceResponse,
    ServiceExecStatus,
)
from agentscope.utils.local_python_executor import (
    BASE_BUILTIN_MODULES,
    LocalPythonInterpreter,
    fix_final_answer_code,
)

CODE_SYSTEM_PROMPT = """You are an expert assistant named {name} who can solve any task using code blobs. You will be given a task to solve as best you can.
To do so, you have been given access to a list of tools: these tools are basically Python functions which you can call with code.
To solve the task, you must plan forward to proceed in a series of steps, in a cycle of 'Thought:', 'Code:', and 'Observation:' sequences.

At each step, in the 'Thought:' sequence, you should first explain your reasoning towards solving the task and the tools that you want to use.
Then in the 'Code:' sequence, you should write the code in simple Python. The code sequence must end with '<end_code>' sequence.
During each intermediate step, you can use 'print()' to save whatever important information you will then need.
These print outputs will then appear in the 'Observation:' field, which will be available as input for the next step.
In the end you have to return a final answer using the `final_answer` tool.

Here are a few examples using notional tools:
---
Task: "Generate an image of the oldest person in this document."

Thought: I will proceed step by step and use the following tools: `document_qa` to find the oldest person in the document, then `image_generator` to generate an image according to the answer.
Code:
```py
answer = document_qa(document=document, question="Who is the oldest person mentioned?")
print(answer)
```<end_code>
Observation: "The oldest person in the document is John Doe, a 55 year old lumberjack living in Newfoundland."

Thought: I will now generate an image showcasing the oldest person.
Code:
```py
image = image_generator("A portrait of John Doe, a 55-year-old man living in Canada.")
final_answer(image)
```<end_code>

---
Task: "What is the result of the following operation: 5 + 3 + 1294.678?"

Thought: I will use python code to compute the result of the operation and then return the final answer using the `final_answer` tool
Code:
```py
result = 5 + 3 + 1294.678
final_answer(result)
```<end_code>

---
Task:
"Answer the question in the variable `question` about the image stored in the variable `image`. The question is in French.
You have been provided with these additional arguments, that you can access using the keys as variables in your python code:
{'question': 'Quel est l'animal sur l'image?', 'image': 'path/to/image.jpg'}"

Thought: I will use the following tools: `translator` to translate the question into English and then `image_qa` to answer the question on the input image.
Code:
```py
translated_question = translator(question=question, src_lang="French", tgt_lang="English")
print(f"The translated question is {translated_question}.")
answer = image_qa(image=image, question=translated_question)
final_answer(f"The answer is {answer}")
```<end_code>

---
Task:
In a 1979 interview, Stanislaus Ulam discusses with Martin Sherwin about other great physicists of his time, including Oppenheimer.
What does he say was the consequence of Einstein learning too much math on his creativity, in one word?

Thought: I need to find and read the 1979 interview of Stanislaus Ulam with Martin Sherwin.
Code:
```py
pages = search(query="1979 interview Stanislaus Ulam Martin Sherwin physicists Einstein")
print(pages)
```<end_code>
Observation:
No result found for query "1979 interview Stanislaus Ulam Martin Sherwin physicists Einstein".

Thought: The query was maybe too restrictive and did not find any results. Let's try again with a broader query.
Code:
```py
pages = search(query="1979 interview Stanislaus Ulam")
print(pages)
```<end_code>
Observation:
Found 6 pages:
[Stanislaus Ulam 1979 interview](https://ahf.nuclearmuseum.org/voices/oral-histories/stanislaus-ulams-interview-1979/)

[Ulam discusses Manhattan Project](https://ahf.nuclearmuseum.org/manhattan-project/ulam-manhattan-project/)

(truncated)

Thought: I will read the first 2 pages to know more.
Code:
```py
for url in ["https://ahf.nuclearmuseum.org/voices/oral-histories/stanislaus-ulams-interview-1979/", "https://ahf.nuclearmuseum.org/manhattan-project/ulam-manhattan-project/"]:
    whole_page = visit_webpage(url)
    print(whole_page)
    print("\n" + "="*80 + "\n")  # Print separator between pages
```<end_code>
Observation:
Manhattan Project Locations:
Los Alamos, NM
Stanislaus Ulam was a Polish-American mathematician. He worked on the Manhattan Project at Los Alamos and later helped design the hydrogen bomb. In this interview, he discusses his work at
(truncated)

Thought: I now have the final answer: from the webpages visited, Stanislaus Ulam says of Einstein: "He learned too much mathematics and sort of diminished, it seems to me personally, it seems to me his purely physics creativity." Let's answer in one word.
Code:
```py
final_answer("diminished")
```<end_code>

---
Task: "Which city has the highest population: Guangzhou or Shanghai?"

Thought: I need to get the populations for both cities and compare them: I will use the tool `search` to get the population of both cities.
Code:
```py
for city in ["Guangzhou", "Shanghai"]:
    print(f"Population {city}:", search(f"{city} population")
```<end_code>
Observation:
Population Guangzhou: ['Guangzhou has a population of 15 million inhabitants as of 2021.']
Population Shanghai: '26 million (2019)'

Thought: Now I know that Shanghai has the highest population.
Code:
```py
final_answer("Shanghai")
```<end_code>

---
Task: "What is the current age of the pope, raised to the power 0.36?"

Thought: I will use the tool `wiki` to get the age of the pope, and confirm that with a web search.
Code:
```py
pope_age_wiki = wiki(query="current pope age")
print("Pope age as per wikipedia:", pope_age_wiki)
pope_age_search = web_search(query="current pope age")
print("Pope age as per google search:", pope_age_search)
```<end_code>
Observation:
Pope age: "The pope Francis is currently 88 years old."

Thought: I know that the pope is 88 years old. Let's compute the result using python code.
Code:
```py
pope_current_age = 88 ** 0.36
final_answer(pope_current_age)
```<end_code>

Above example were using notional tools that might not exist for you. On top of performing computations in the Python code snippets that you create, you only have access to these tools:

{{tool_descriptions}}

Here are the rules you should always follow to solve your task:
1. Always provide a 'Thought:' sequence, and a 'Code:\n```py' sequence ending with '```<end_code>' sequence, else you will fail.
2. Use only variables that you have defined!
3. Always use the right arguments for the tools. DO NOT pass the arguments as a dict as in 'answer = wiki({'query': "What is the place where James Bond lives?"})', but use the arguments directly as in 'answer = wiki(query="What is the place where James Bond lives?")'.
4. Take care to not chain too many sequential tool calls in the same code block, especially when the output format is unpredictable. For instance, a call to search has an unpredictable return format, so do not have another tool call that depends on its output in the same block: rather output results with print() to use them in the next block.
5. Call a tool only when needed, and never re-do a tool call that you previously did with the exact same parameters.
6. Don't name any new variable with the same name as a tool: for instance don't name a variable 'final_answer'.
7. Never create any notional variables in our code, as having these in your logs will derail you from the true variables.
8. You can use imports in your code, but only from the following list of modules: {{authorized_imports}}
9. The state persists between code executions: so if in one step you've created variables or imported modules, these will all persist.
10. Don't give up! You're in charge of solving the task, not providing directions to solve it.

Now Begin! If you solve the task correctly, you will receive a reward of $1,000,000.
"""


class CodeAgent(AgentBase):
    """An agent class that implements the CodeAct algorithm. More details refer
    to https://arxiv.org/pdf/2402.01030.

    This is an example implementation of CodeAct algorithm in AgentScope.
    We follow the idea within the paper, but the detailed prompt engineering
    maybe different. Developers are encouraged to modify the prompt to fit
    their own needs.

    Note:
        In this agent, the tool calls will be formulated by the LLM in code format, then parsed and executed.
    """

    def __init__(
        self,
        name: str,
        model_config_name: str,
        service_toolkit: ServiceToolkit,
        sys_prompt: str = CODE_SYSTEM_PROMPT,
        additional_authorized_imports: Optional[list[str]] = None,
        max_iters: int = 10,
        verbose: bool = True,
    ) -> None:
        """Initialize the ReAct agent with the given name, model config name
        and tools.

        Args:
            name (`str`):
                The name of the agent.
            sys_prompt (`str`):
                The system prompt of the agent.
            model_config_name (`str`):
                The name of the model config, which is used to load model from
                configuration.
            service_toolkit (`ServiceToolkit`):
                A `ServiceToolkit` object that contains the tool functions.
            max_iters (`int`, defaults to `10`):
                The maximum number of iterations of the reasoning-acting loops.
            verbose (`bool`, defaults to `True`):
                Whether to print the detailed information during reasoning and
                acting steps. If `False`, only the content in speak field will
                be print out.
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
        )

        self.service_toolkit = service_toolkit

        self.service_toolkit.add(self.finish)

        self.verbose = verbose
        self.max_iters = max_iters

        if not sys_prompt.endswith("\n"):
            sys_prompt = sys_prompt + "\n"

        self.authorized_imports = list(set(BASE_BUILTIN_MODULES))
        self.additional_authorized_imports = additional_authorized_imports if additional_authorized_imports else []

        sys_prompt = sys_prompt.format(name=self.name)
        self.sys_prompt = sys_prompt.replace(
            "{{tool_descriptions}}", self.service_toolkit.tools_instruction
        )
        self.system_prompt = self.sys_prompt.replace(
            "{{authorized_imports}}",
            "You can import from any package you want."
            if "*" in self.authorized_imports
            else str(self.authorized_imports),
        )

        self.python_executor = LocalPythonInterpreter(
            self.additional_authorized_imports, self.service_toolkit.service_funcs
        )

        # Put sys prompt into memory
        self.memory.add(Msg("system", self.sys_prompt, role="system"))

    def parse_code_blobs(code_blob: str) -> str:
        """Parses the LLM's output to get any code blob inside. Will return the code directly if it's code."""
        pattern = r"```(?:py|python)?\n(.*?)\n```"
        matches = re.findall(pattern, code_blob, re.DOTALL)
        if len(matches) == 0:
            try:  # Maybe the LLM outputted a code blob directly
                ast.parse(code_blob)
                return code_blob
            except SyntaxError:
                pass

            if "final" in code_blob and "answer" in code_blob:
                raise ValueError(
                    f"""
    The code blob is invalid, because the regex pattern {pattern} was not found in {code_blob=}. It seems like you're trying to return the final answer, you can do it as follows:
    Code:
    ```py
    final_answer("YOUR FINAL ANSWER HERE")
    ```<end_code>""".strip()
                )
            raise ValueError(
                f"""
    The code blob is invalid, because the regex pattern {pattern} was not found in {code_blob=}. Make sure to include code with the correct pattern, for instance:
    Thoughts: Your thoughts
    Code:
    ```py
    # Your python code here
    ```<end_code>""".strip()
            )
        return "\n\n".join(match.strip() for match in matches)

    def reply(self, x: Optional[Union[Msg, Sequence[Msg]]] = None) -> Msg:
        """The reply method of the agent."""
        self.memory.add(x)

        for _ in range(self.max_iters):
            prompt = self.model.format(
                self.memory and self.memory.get_memory() or x,  # type: ignore[arg-type]
            )

            response = self.model(prompt, stop_sequences=["<end_code>", "Observation:"]).text

            # Parse
            try:
                code_action = fix_final_answer_code(self.parse_code_blobs(response))
            except Exception as e:
                error_msg = (
                    f"Error in code parsing:\n{e}\nMake sure to provide correct code blobs."
                )

                raise ValueError(error_msg)



        # When exceeding the max iterations
        hint_msg = Msg(
            "system",
            "You have failed to generate response within the maximum "
            "iterations. Now respond directly by summarizing the current "
            "situation.",
            role="system",
            echo=self.verbose,
        )

        # Generate a reply by summarizing the current situation
        prompt = self.model.format(self.memory.get_memory(), hint_msg)
        res = self.model(prompt)
        self.speak(res.stream or res.text)
        res_msg = Msg(self.name, res.text, "assistant")
        return res_msg


    @staticmethod
    def finish(response: str) -> ServiceResponse:
        """Finish reasoning and generate a response to the user.

        Args:
            response (`str`):
                The response to the user.
        """
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=response,
        )
