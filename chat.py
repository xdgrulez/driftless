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

# Kompatibilitäts-Patch: mcp v2 nennt das Feld input_schema (snake_case),
# llama-index-tools-mcp 0.6.0 greift noch auf inputSchema (camelCase) zu.
if not hasattr(types.Tool, "inputSchema"):
    types.Tool.inputSchema = property(lambda self: self.input_schema)

SYSTEM_PROMPT = """Du bist ein Assistent mit Zugriff auf ein Tool namens
`search_customer_context`, das frühere Bestellungen eines Kunden
per semantischer Suche in einer Vektordatenbank findet.

Das Tool benötigt:
- query (string): die Suchanfrage in natürlicher Sprache
- customer_id (string): die ID des Kunden, für den gesucht wird (optional)
- limit (int, optional): maximale Anzahl Ergebnisse (Standard 3)

Wenn der Nutzer keine customer_id in seiner Nachricht angibt, frage
danach, bevor du das Tool aufrufst. Erfinde niemals eine customer_id.
Fasse die Ergebnisse des Tools verständlich zusammen (Bestellnummer,
Status, Betrag), anstatt die Rohdaten unverändert auszugeben.
"""


def ts() -> str:
    return time.strftime("%H:%M:%S")


async def start_chat():
    print(f"[{ts()}] Verbinde mit MCP-Server...")

    llm = Ollama(
        model="llama3.2:1b",
        request_timeout=120.0,
        additional_kwargs={"stop": ["Observation:"]},
    )

    try:
        t0 = time.time()
        mcp_client = BasicMCPClient(MCP_SSE_URL)
        mcp_tool_spec = McpToolSpec(client=mcp_client)
        tools = await mcp_tool_spec.to_tool_list_async()
        print(f"[{ts()}] MCP-Tools geladen in {time.time() - t0:.2f}s")
    except Exception as e:
        print(f"[{ts()}] Fehler bei der Verbindung zum MCP-Server: {e}")
        return

    if not tools:
        print(f"[{ts()}] Warnung: Es wurden keine Tools vom MCP-Server geladen.")
    else:
        print(f"[{ts()}] Geladene Tools:")
        for t in tools:
            print(f"  - {t.metadata.name}: {t.metadata.get_parameters_dict()}")

    agent = ReActAgent(tools=tools, llm=llm, system_prompt=SYSTEM_PROMPT, verbose=True)
    ctx = Context(agent)

    print("\n" + "=" * 50)
    print("Chat gestartet! Schreibe 'exit' oder 'quit' zum Beenden.")
    print("=" * 50 + "\n")

    while True:
        try:
            user_input = input("Du: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print(f"[{ts()}] Chat beendet.")
                break

            print(f"[{ts()}] -> Sende an Agent, warte auf LLM (llama3.2:1b)...")
            t0 = time.time()

            handler = agent.run(user_input, ctx=ctx)

            async for event in handler.stream_events():
                if isinstance(event, AgentInput):
                    print(f"[{ts()}] [Agent] Eingabe an LLM vorbereitet.")
                elif isinstance(event, AgentStream):
                    # Token-für-Token-Ausgabe des LLM, live mitschreiben
                    print(event.delta, end="", flush=True)
                elif isinstance(event, ToolCall):
                    print(
                        f"\n[{ts()}] [Tool-Aufruf] {event.tool_name}({event.tool_kwargs})"
                    )
                elif isinstance(event, ToolCallResult):
                    print(f"[{ts()}] [Tool-Ergebnis] {event.tool_output}")
                elif isinstance(event, AgentOutput):
                    print(f"\n[{ts()}] [Agent] Antwort fertig.")

            response = await handler
            print(f"[{ts()}] Fertig nach {time.time() - t0:.2f}s\n")
            print(f"Assistant: {response}\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n[{ts()}] Chat beendet.")
            break
        except Exception as e:
            print(f"[{ts()}] Fehler bei der Verarbeitung: {e}\n")


if __name__ == "__main__":
    asyncio.run(start_chat())