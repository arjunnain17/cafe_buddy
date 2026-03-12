import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.reccomend import load_indexes
from core.agent import build_agent, invoke_agent

load_indexes()
agent = build_agent()

response = invoke_agent(agent, "hi, what's your name and where do you work?")
print(response)