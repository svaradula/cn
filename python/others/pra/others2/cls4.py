class Agent:
    total_agents = 0
    by_type = {}

    def __init__(self, agent_type):
        self.agent_type = agent_type
        Agent.total_agents += 1
        Agent.by_type[agent_type] = Agent.by_type.get(agent_type, 0) + 1


Agent("chat")
Agent("chat")
Agent("tool")

print(Agent.total_agents)     # 3
print(Agent.by_type)          # {'chat': 2, 'tool': 1}
