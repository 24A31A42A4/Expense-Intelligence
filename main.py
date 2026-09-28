from langgraph.graph import END, START, StateGraph

from agents.analysis_agent import analysis_agent
from agents.category_agent import category_agent
from agents.recommendation_agent import recommendation_agent
from agents.transaction_agent import transaction_agent
from state import ExpenseState


graph = StateGraph(ExpenseState)
graph.add_node("transaction_agent", transaction_agent)
graph.add_node("category_agent", category_agent)
graph.add_node("analysis_agent", analysis_agent)
graph.add_node("recommendation_agent", recommendation_agent)

graph.add_edge(START, "transaction_agent")
graph.add_edge("transaction_agent", "category_agent")
graph.add_edge("category_agent", "analysis_agent")
graph.add_edge("analysis_agent", "recommendation_agent")
graph.add_edge("recommendation_agent", END)

expense_graph = graph.compile()


def run_expense_query(user_query: str) -> dict:
    """Run the complete expense-analysis graph for a user query."""
    return expense_graph.invoke({"user_query": user_query})


def stream_expense_query(user_query: str):
    """Stream each agent's state update for a user query."""
    yield from expense_graph.stream(
        {"user_query": user_query},
        stream_mode="updates",
    )


if __name__ == "__main__":
    graph_image_png = expense_graph.get_graph().draw_mermaid_png()
    with open("final_expense_graph.png", "wb") as image_file:
        image_file.write(graph_image_png)

    result = run_expense_query(
        "Analyze my expenses for July. Show my total spending, highest spending "
        "categories, unusual transactions, spending patterns, and any policy "
        "violations. Give me recommendations to reduce unnecessary expenses "
        "next month."
    )
    print("Final Result:")
    print(result)
