# agents/cashflow_agent.py
from langchain_core.messages import BaseMessage, HumanMessage
from core.settings import get_model
import asyncio

async def cashflow_agent(messages, config=None):
    """
    Simple async function to process messages and generate cash flow analysis
    """
    if config is None:
        config = {"configurable": {}}
    
    # Get the model
    model = get_model(config["configurable"].get("model"))
    
    # If messages is a dict with "messages" key, extract it
    if isinstance(messages, dict) and "messages" in messages:
        message_list = messages["messages"]
    else:
        message_list = messages if isinstance(messages, list) else [messages]
    
    # Invoke the model
    response = await model.ainvoke(message_list)
    
    return {"messages": [response]}
