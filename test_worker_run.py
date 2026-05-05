import asyncio
from app.core.graph_builder import build_graph

async def main():
    graph = build_graph()
    state = {
        "query": "us iran war",
        "report_format": "weekly_trend_report",
        "region": None,
        "industry": None,
        "time_window_hours": 72
    }
    try:
        result = await asyncio.get_running_loop().run_in_executor(None, graph.invoke, state)
        print("RESULT KEYS:", result.keys())
        if 'report' in result:
            print("REPORT SUMMARY:", result['report'].get('summary'))
        else:
            print("NO REPORT KEY")
    except Exception as e:
        print("EXCEPTION:", e)

if __name__ == "__main__":
    asyncio.run(main())
