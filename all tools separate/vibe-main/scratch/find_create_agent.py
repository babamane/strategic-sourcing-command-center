try:
    from langchain.agents import create_agent
    import inspect
    print(f"create_agent is imported from: {inspect.getfile(create_agent)}")
except ImportError:
    print("create_agent NOT found in langchain.agents")
except Exception as e:
    print(f"Error: {e}")
