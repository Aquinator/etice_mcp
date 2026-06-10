"""
mcp_client/chat.py — Chat interativo com streaming de tokens

Uso:
    python -m mcp_client.chat
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_client.agent import AppState, nova_sessao, invocar_stream

G = "\033[92m"; C = "\033[96m"; Y = "\033[93m"; R = "\033[91m"; N = "\033[0m"
SAIR = {"sair", "exit", "quit", "q"}


async def _ler_input(prompt: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: input(prompt).strip())


async def main() -> None:
    print()
    print(f"{C}═══════════════════════════════════════════════════════{N}")
    print(f"{C}  ETICE — Chat de Contratos de Nuvem                   {N}")
    print(f"{C}  Digite 'sair' para encerrar                           {N}")
    print(f"{C}═══════════════════════════════════════════════════════{N}")
    print()

    state = AppState()
    await state.inicializar()
    try:
        thread_id = nova_sessao()
        print(f"  {G}✓{N} Agente pronto | {len(state.tools)} tool(s) | sessão {thread_id[:8]}…\n")

        while True:
            try:
                pergunta = await _ler_input(f"{Y}Você:{N} ")
            except (KeyboardInterrupt, EOFError):
                print("\n\nEncerrando...")
                break
            if not pergunta:
                continue
            if pergunta.lower() in SAIR:
                print("Até logo!")
                break

            print(f"\n{G}Agente:{N} ", end="", flush=True)
            try:
                async for chunk in invocar_stream(state.agente, pergunta, thread_id):
                    print(chunk, end="", flush=True)
                print("\n")
            except Exception as e:
                print(f"\n\n  {R}✗{N} Erro: {e}\n")
    finally:
        await state.encerrar()


if __name__ == "__main__":
    asyncio.run(main())