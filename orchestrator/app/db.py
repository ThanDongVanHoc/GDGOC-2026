import asyncio
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async def execute_graph(graph_builder, state_or_command, thread_id: str):
    """
    Safely executes a LangGraph ainvoke inside the lifespan of an SQLite connection.
    This resolves the compatibility issues with asynchronous graph invocation.
    """
    async with AsyncSqliteSaver.from_conn_string("state.db") as checkpointer:
        # Give LangGraph a chance to generate SQLite migration tables if not exist
        await checkpointer.setup()
        
        # Build the graph with the checkpointer
        graph = graph_builder(checkpointer)
        
        # Invoke the graph
        await graph.ainvoke(
            state_or_command, 
            config={"configurable": {"thread_id": thread_id}}
        )
