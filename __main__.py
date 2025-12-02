"""Run Chaos Mesh MCP server."""

from chaos_mesh_mcp.server import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
