import streamlit as st

from main import stream_expense_query


st.set_page_config(
    page_title="Expense Intelligence",
    page_icon="₹",
)

st.title("Expense Intelligence Chatbot")
st.caption("Ask questions about your transaction data.")

AGENT_TOOLS = {
    "transaction_agent": "load_transactions, filter_transactions",
    "category_agent": "No external tools",
    "analysis_agent": "retrieve_policy_context (conditional RAG retrieval)",
    "recommendation_agent": "No external tools",
}

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], str):
            st.markdown(message["content"])
        else:
            st.json(message["content"])

user_query = st.chat_input("Analyze my expenses for July...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        result = {}
        try:
            with st.status("Running expense agents...", expanded=True) as status:
                for update in stream_expense_query(user_query):
                    for agent_name, agent_result in update.items():
                        result.update(agent_result)
                        st.write(f"Completed: {agent_name}")
                        st.caption(
                            f"Tools: {AGENT_TOOLS.get(agent_name, 'Not specified')}"
                        )
                status.update(label="Analysis complete", state="complete")

            response = result.get("final_response", "")
            st.markdown(response)
            st.json({
                "analysis": result.get("analysis", {}),
                "recommendations": result.get("recommendations", []),
            })
            with st.expander("Tool outputs"):
                st.subheader("Transaction tools")
                st.json(result.get("transaction_result", {}))
                st.subheader("Category Agent output")
                st.json(result.get("categorized_transactions", []))
                st.subheader("RAG retrieval scores")
                st.json(result.get("policy_scores", []))
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
            })
        except Exception as error:
            message = f"Unable to complete the analysis: {error}"
            st.error(message)
            st.session_state.messages.append({
                "role": "assistant",
                "content": message,
            })
