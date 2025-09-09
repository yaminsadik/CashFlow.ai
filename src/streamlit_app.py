# streamlit_app.py
import streamlit as st
import pandas as pd
import asyncio
from agents.cashflow_agent import cashflow_agent
from langchain_core.messages import HumanMessage

st.title("💰 Cash Flow Generator - MVP")

# Start with Excel/CSV only
st.subheader("📊 Upload Excel or CSV File")
uploaded_file = st.file_uploader("Choose file", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    # Read the file
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Preview data
        st.subheader("📋 Data Preview")
        st.dataframe(df.head())
        
        # Generate cash flow
        if st.button("📊 Generate Cash Flow"):
            with st.spinner("Processing..."):
                try:
                    # Convert dataframe to text for the agent
                    data_text = df.to_csv(index=False)
                    
                    prompt = f"""
                    Generate a direct method cash flow statement from this data:
                    
                    {data_text}
                    
                    Categorize transactions into:
                    - Operating Activities (receipts and payments)
                    - Net Cash Flow calculation
                    
                    Provide a clear, professional format.
                    """
                    
                    # Call the agent using asyncio.run()
                    config = {"configurable": {}}
                    result = asyncio.run(cashflow_agent(
                        {"messages": [HumanMessage(content=prompt)]},
                        config=config
                    ))
                    
                    st.success("✅ Cash Flow Generated!")
                    st.markdown(result["messages"][-1].content)
                    
                except Exception as e:
                    st.error(f"❌ Error generating cash flow: {str(e)}")
                    
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
