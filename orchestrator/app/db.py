import asyncio
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


async def execute_graph(graph_builder, state_or_command, thread_id: str) -> dict | None:
    """
    Safely executes a LangGraph ainvoke inside the lifespan of an SQLite connection.
    Returns the final state dict after the graph suspends or completes.
    """
    async with AsyncSqliteSaver.from_conn_string("state.db") as checkpointer:
        await checkpointer.setup()
        
        graph = graph_builder(checkpointer)
        
        result = await graph.ainvoke(
            state_or_command, 
            config={"configurable": {"thread_id": thread_id}}
        )
        
        return result
