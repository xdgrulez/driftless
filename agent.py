import asyncio
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 1. Konfiguration des MCP Servers (Driftless Pod)
server_params = StdioServerParameters(
    command="python",
    args=["driftless_pod.py"]  # Dein Pod mit Kafi Streams + FastMCP
)

MODEL_NAME = "llama3.2"  # Modell mit Tool-Calling Unterstuetzung

async def run_agent():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Tool-Discovery über MCP
            mcp_tools = await session.list_tools()
            ollama_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in mcp_tools.tools
            ]

            messages = [{"role": "user", "content": "Was ist der aktuelle Status der Retoure von Kunde 4711?"}]

            # 2. Frage + Tools an Ollama senden
            response = ollama.chat(
                model=MODEL_NAME,
                messages=messages,
                tools=ollama_tools,
            )

            assistant_msg = response["message"]
            
            # 3. Wenn Ollama ein Tool anfordert -> Auf Driftless Pod ausführen
            if assistant_msg.get("tool_calls"):
                messages.append(assistant_msg)
                
                for tool_call in assistant_msg["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    tool_args = tool_call["function"]["arguments"]

                    # MCP Call an den Pod
                    result = await session.call_tool(tool_name, tool_args)
                    
                    # Tool-Ergebnis in die Message History einfügen
                    messages.append({
                        "role": "tool",
                        "content": str(result.content),
                    })

                # Finale Synthese durch Ollama mit frischem Kontext
                final_response = ollama.chat(model=MODEL_NAME, messages=messages)
                print("Agent Antwort:", final_response["message"]["content"])
            else:
                print("Agent Antwort:", assistant_msg["content"])

if __name__ == "__main__":
    asyncio.run(run_agent())