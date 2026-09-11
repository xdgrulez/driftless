import asyncio
import time
import mcp.types as types
from llama_index.core.agent.workflow import (
    ReActAgent,
    AgentStream,
    AgentInput,
    AgentOutput,
    ToolCall,
    ToolCallResult,
)
from llama_index.core.workflow import Context
from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

MCP_SSE_URL = "http://localhost:8000/sse"

if not hasattr(types.Tool, "inputSchema"):
    types.Tool.inputSchema = property(lambda self: self.input_schema)

SYSTEM_PROMPT = """You are an assistent with access to a tool called
`search_customer_context`, that can do look-ups in a vector database.

The tool has the following signature:
search_customer_context(query: Optional[str] = None, id: Optional[str] = None, customer_id: Optional[str] = None, customer_name: Optional[str] = None, limit: int = 3) -> list[CustomerContextResult]

- query: the query (similarity seaech)
- id: the order ID (exact column filter)
- customer_id: the customer ID (exact column filter)
- customer_name: the customer name (substring column filter)
- limit: maximum number of results (default: 3)

where you need to summarize the output list of CustomerContextResult entries (use the score only for internal purposes):
class CustomerContextResult(TypedDict):
    summary: str
    score: float
"""


def ts() -> str:
    return time.strftime("%H:%M:%S")


async def start_chat():
    print(f"[{ts()}] Connecting to MCP server...")

    llm = Ollama(
        model="qwen2.5:1.5b-instruct",
        request_timeout=120.0,
        additional_kwargs={"stop": ["Observation:"]},
    )

    try:
        t0 = time.time()
        mcp_client = BasicMCPClient(MCP_SSE_URL)
        mcp_tool_spec = McpToolSpec(client=mcp_client)
        tools = await mcp_tool_spec.to_tool_list_async()
        print(f"[{ts()}] MCP-Tools loaded in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"[{ts()}] Error connecting to MCP server: {e}")
        return

    if not tools:
        print(f"[{ts()}] Warning: No tools found on MCP server.")
    else:
        print(f"[{ts()}] Found tools:")
        for t in tools:
            print(f"  - {t.metadata.name}: {t.metadata.get_parameters_dict()}")

    agent = ReActAgent(tools=tools, llm=llm, system_prompt=SYSTEM_PROMPT, verbose=True)
    ctx = Context(agent)

    print("\n" + "=" * 50)
    print("Starting chat (type exit or quit to stop).")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input = input("$ ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print(f"[{ts()}] Chat stopped.")
                break

            print(f"[{ts()}] -> Sending to agent server...")
            t0 = time.time()

            handler = agent.run(user_input, ctx=ctx)

            async for event in handler.stream_events():
                if isinstance(event, AgentInput):
                    print(f"[{ts()}] [Agent] Prepared input for LLM.")
                elif isinstance(event, AgentStream):
                    print(event.delta, end="", flush=True)
                elif isinstance(event, ToolCall):
                    print(
                        f"\n[{ts()}] [Tool call] {event.tool_name}({event.tool_kwargs})"
                    )
                elif isinstance(event, ToolCallResult):
                    print(f"[{ts()}] [Tool result] {event.tool_output}")
                elif isinstance(event, AgentOutput):
                    print(f"\n[{ts()}] [Agent] Response done.")

            response = await handler
            print(f"[{ts()}] Done after {time.time() - t0:.2f}s\n")
            print(f"Assistent: {response}\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n[{ts()}] Chat stopped.")
            break
        except Exception as e:
            print(f"[{ts()}] Error processing: {e}\n")


if __name__ == "__main__":
    asyncio.run(start_chat())
