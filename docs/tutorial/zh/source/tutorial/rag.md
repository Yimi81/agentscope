# RAG

我们在此介绍AgentScope与RAG相关的三个概念：知识（Knowledge），知识库（Knowledge Bank）和RAG 智能体。

### Knowledge
知识模块（目前仅有“LlamaIndexKnowledge”；即将提供对LangChain的支持）负责处理所有与RAG相关的操作。

#### 如何初始化一个Knowledge对象
 用户可以使用JSON配置来创建一个Knowledge模块，以指定1）数据路径，2）数据加载器，3）数据预处理方法，以及4）嵌入模型（模型配置名称）。
一个详细的示例可以参考以下内容：
  <details>
  <summary> 详细的配置示例 </summary>

  ```json
  [
  {
    "knowledge_id": "{your_knowledge_id}",
    "emb_model_config_name": "{your_embed_model_config_name}",
    "data_processing": [
      {
        "load_data": {
          "loader": {
            "create_object": true,
            "module": "llama_index.core",
            "class": "SimpleDirectoryReader",
            "init_args": {
              "input_dir": "{path_to_your_data_dir_1}",
              "required_exts": [".md"]
            }
          }
        }
      },
      {
        "load_data": {
          "loader": {
            "create_object": true,
            "module": "llama_index.core",
            "class": "SimpleDirectoryReader",
            "init_args": {
              "input_dir": "{path_to_your_python_code_data_dir}",
              "recursive": true,
              "required_exts": [".py"]
            }
          }
        },
        "store_and_index": {
          "transformations": [
            {
              "create_object": true,
              "module": "llama_index.core.node_parser",
              "class": "CodeSplitter",
              "init_args": {
                "language": "python",
                "chunk_lines": 100
              }
            }
          ]
        }
      }
    ]
  }
  ]
  ```

  </details>

#### 更多关于 knowledge 配置
以上提到的配置通常保存为一个JSON文件，它必须包含以下关键属性
* `knowledge_id`: 每个knowledge模块的唯一标识符;
* `emb_model_config_name`: embedding模型的名称;
* `chunk_size`: 对文件分块的默认大小;
* `chunk_overlap`: 文件分块之间的默认重叠大小;
* `data_processing`: 一个list型的数据处理方法集合。

##### 以配置 LlamaIndexKnowledge 为例

当使用`llama_index_knowledge`是，对于上述的最后一项`data_processing` ，这个`list`型的参数中的每个条目（为`dict`型）都对应配置一个data loader对象，其功能包括用来加载所需的数据（即字段`load_data`中包含的信息），以及处理加载数据的转换对象（`store_and_index`）。换而言之，在一次载入数据时，可以同时从多个数据源中加载数据，并处理后合并在同一个索引下以供后面的数据提取使用（retrieve）。有关该组件的更多信息，请参阅 [LlamaIndex-Loading](https://docs.llamaindex.ai/en/stable/module_guides/loading/)。

在这里，无论是针对数据加载还是数据处理，我们都需要配置以下属性
* `create_object`：指示是否创建新对象，在此情况下必须为true；
* `module`：对象对应的类所在的位置；
* `class`：这个类的名称。

更具体得说，当对`load_data`进行配置时候，您可以选择使用多种多样的的加载器，例如使用`SimpleDirectoryReader`（在`class`字段里配置）来读取各种类型的数据（例如txt、pdf、html、py、md等）。关于这个数据加载器，您还需要配置以下关键属性
* `input_dir`：数据加载的路径；
* `required_exts`：将加载的数据的文件扩展名。

有关数据加载器的更多信息，请参阅[这里](https://docs.llamaindex.ai/en/stable/module_guides/loading/simpledirectoryreader/)。

对于`store_and_index`而言，这个配置是可选的，如果用户未指定特定的转换方式，系统将使用默认的transformation（也称为node parser）方法，名称为`SentenceSplitter`。对于某些特定需求下也可以使用不同的转换方式，例如对于代码解析可以使用`CodeSplitter`，针对这种特殊的node parser，用户可以设置以下属性：
* `language`：希望处理代码的语言名；
* `chunk_lines`：分割后每个代码块的行数。

有关节点解析器的更多信息，请参阅[这里](https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/)。

如果用户想要避免详细的配置，我们也在`KnowledgeBank`中提供了一种快速的方式（请参阅以下内容）。

#### 如何使用一个 Knowledge 对象
当我们成功创建了一个knowledge后，用户可以通过`.retrieve`从`Knowledge` 对象中提取信息。`.retrieve`函数一下三个参数：
* `query`: 输入参数，用户希望提取与之相关的内容;
* `similarity_top_k`: 提取的“数据块”数量；
* `to_list_strs`: 是否只返回字符串(str)的列表(list)。

*高阶:* 对于 `LlamaIndexKnowledge`, 它的`.retrieve`函数也支持熟悉LlamaIndex的用户直接传入一个建好的retriever。

#### 关于`LlamaIndexKnowledge`的细节
在这里，我们将使用`LlamaIndexKnowledge`作为示例，以说明在`Knowledge`模块内的操作。
当初始化`LlamaIndexKnowledge`对象时，`LlamaIndexKnowledge.__init__`将执行以下步骤：
  *  它处理数据并生成检索索引 (`LlamaIndexKnowledge._data_to_index(...)`中完成) 其中包括
      * 加载数据 `LlamaIndexKnowledge._data_to_docs(...)`;
      * 对数据进行预处理，使用预处理方法（比如分割）和向量模型生成向量  `LlamaIndexKnowledge._docs_to_nodes(...)`;
      * 基于生成的向量做好被查询的准备， 即生成索引。
  * 如果索引已经存在，则会调用 `LlamaIndexKnowledge._load_index(...)` 来加载索引，并避免重复的嵌入调用。
</br>

### Knowledge Bank
知识库将一组Knowledge模块（例如，来自不同数据集的知识）作为知识的集合进行维护。因此，不同的智能体可以在没有不必要的重新初始化的情况下重复使用知识模块。考虑到配置Knowledge模块可能对大多数用户来说过于复杂，知识库还提供了一个简单的函数调用来创建Knowledge模块。

* `KnowledgeBank.add_data_as_knowledge`: 创建Knowledge模块。一种简单的方式只需要提供knowledge_id、emb_model_name和data_dirs_and_types。
   因为`KnowledgeBank`默认生成的是 `LlamaIndexKnowledge`, 所以所有文本类文件都可以支持，包括`.txt`， `.html`， `.md` ，`.csv`，`.pdf`和 所有代码文件（如`.py`）.  其他支持的文件类型可以参考 [LlamaIndex document](https://docs.llamaindex.ai/en/stable/module_guides/loading/simpledirectoryreader/).
  ```python
  knowledge_bank.add_data_as_knowledge(
        knowledge_id="agentscope_tutorial_rag",
        emb_model_name="qwen_emb_config",
        data_dirs_and_types={
            "../../docs/sphinx_doc/en/source/tutorial": [".md"],
        },
    )
  ```
  对于更高级的初始化，用户仍然可以将一个知识模块配置作为参数knowledge_config传递：
  ```python
  # load knowledge_config as dict
  knowledge_bank.add_data_as_knowledge(
      knowledge_id=knowledge_config["knowledge_id"],
      emb_model_name=knowledge_config["emb_model_config_name"],
      knowledge_config=knowledge_config,
  )
  ```
* `KnowledgeBank.get_knowledge`: 它接受两个参数，knowledge_id和duplicate。
  如果duplicate为true，则返回提供的knowledge_id对应的知识对象；否则返回深拷贝的对象。
* `KnowledgeBank.equip`: 它接受三个参数，`agent`，`knowledge_id_list` 和`duplicate`。
该函数会根据`knowledge_id_list`为`agent`提供相应的知识（放入`agent.knowledge_list`）。`duplicate` 同样决定是否是深拷贝。



### RAG 智能体
RAG 智能体是可以基于检索到的知识生成答案的智能体。
  * 让智能体使用RAG: RAG agent配有一个`knowledge_list`的列表
    * 可以在初始化时就给RAG agent传入`knowledge_list`
      ```python
          knowledge = knowledge_bank.get_knowledge(knowledge_id)
          agent = LlamaIndexAgent(
              name="rag_worker",
              sys_prompt="{your_prompt}",
              model_config_name="{your_model}",
              knowledge_list=[knowledge], # provide knowledge object directly
              similarity_top_k=3,
              log_retrieval=False,
              recent_n_mem_for_retrieve=1,
          )
        ```
    * 如果通过配置文件来批量启动agent，也可以给agent提供`knowledge_id_list`。这样也可以通过将agent和它的`knowledge_id_list`一起传入`KnowledgeBank.equip`来为agent赋予`knowledge_list`。
      ```python
          # >>> agent.knowledge_list
          # >>> []
          knowledge_bank.equip(agent, agent.knowledge_id_list)
          # >>> agent.knowledge_list
          # [<LlamaIndexKnowledge object at 0x16e516fb0>]
      ```
  * Agent 智能体可以在`reply`函数中使用从`Knowledge`中检索到的信息，将其提示组合到LLM的提示词中。

**自己搭建 RAG 智能体.** 只要您的智能体配置具有`knowledge_id_list`，您就可以将一个agent和这个列表传递给`KnowledgeBank.equip`；这样该agent就是被装配`knowledge_id`。
您可以在`reply`函数中自己决定如何从`Knowledge`对象中提取和使用信息，甚至通过`Knowledge`修改知识库。


## (拓展) 架设自己的embedding model服务

我们在此也对架设本地embedding model感兴趣的用户提供以下的样例。
以下样例基于在embedding model范围中很受欢迎的`sentence_transformers` 包（基于`transformer` 而且兼容HuggingFace和ModelScope的模型）。
这个样例中，我们会使用当下最好的文本向量模型之一`gte-Qwen2-7B-instruct`。


* 第一步: 遵循在 [HuggingFace](https://huggingface.co/Alibaba-NLP/gte-Qwen2-7B-instruct) 或者 [ModelScope](https://www.modelscope.cn/models/iic/gte_Qwen2-7B-instruct )的指示下载模型。
  (如果无法直接从HuggingFace下载模型，也可以考虑使用HuggingFace镜像：bash命令行`export HF_ENDPOINT=https://hf-mirror.com`，或者在Python代码中加入`os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"`)
* 第二步: 设置服务器。以下是一段参考代码。

```python
import datetime
import argparse

from flask import Flask
from flask import request
from sentence_transformers import SentenceTransformer

def create_timestamp(format_: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Get current timestamp."""
    return datetime.datetime.now().strftime(format_)

app = Flask(__name__)

@app.route("/embedding/", methods=["POST"])
def get_embedding() -> dict:
    """Receive post request and return response"""
    json = request.get_json()

    inputs = json.pop("inputs")

    global model

    if isinstance(inputs, str):
        inputs = [inputs]

    embeddings = model.encode(inputs)

    return {
        "data": {
            "completion_tokens": 0,
            "messages": {},
            "prompt_tokens": 0,
            "response": {
                "data": [
                    {
                        "embedding": emb.astype(float).tolist(),
                    }
                    for emb in embeddings
                ],
                "created": "",
                "id": create_timestamp(),
                "model": "flask_model",
                "object": "text_completion",
                "usage": {
                    "completion_tokens": 0,
                    "prompt_tokens": 0,
                    "total_tokens": 0,
                },
            },
            "total_tokens": 0,
            "username": "",
        },
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, required=True)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    global model

    print("setting up for embedding model....")
    model = SentenceTransformer(
        args.model_name_or_path
    )

    app.run(port=args.port)
```

* 第三部：启动服务器。
```bash
python setup_ms_service.py --model_name_or_path {$PATH_TO_gte_Qwen2_7B_instruct}
```


测试服务是否成功启动。
```python
from agentscope.models.post_model import PostAPIEmbeddingWrapper


model = PostAPIEmbeddingWrapper(
    config_name="test_config",
    api_url="http://127.0.0.1:8000/embedding/",
    json_args={
        "max_length": 4096,
        "temperature": 0.5
    }
)

print(model("testing"))
```