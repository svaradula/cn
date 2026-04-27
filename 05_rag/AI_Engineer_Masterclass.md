# 🧠 AI Engineer Masterclass
## From Foundational LLMs → Agentic AI & Advanced RAG Systems

> **Based on your Coding Ninjas curriculum (Sessions 6–10) + extended engineering depth**
> Tech Stack: Python · Pydantic · LangChain · Gemini/OpenAI · Vector DBs

---

# PART 1 — THE AGENTIC AI LEARNING ROADMAP
## Transitioning from Linear LLM Calls → Complex Multi-Agent Systems

---

## 🗺️ The Big Picture: Your Journey in 5 Stages

```
[Stage 1]          [Stage 2]           [Stage 3]            [Stage 4]           [Stage 5]
Foundation    →  Structured I/O   →  Memory & Tools  →   Agentic Reasoning  →  Multi-Agent
  Python            Pydantic          LangChain +         ReAct / Planning       CrewAI /
  Async              + LangChain       Function Calls        Loops                AutoGen
```

---

## ⚙️ STAGE 1 — Python Foundations for AI Engineering
### *(Duration: 1–2 weeks)*

### Key Concepts to Master

#### 1.1 Asynchronous Programming — The Engine of Agentic Systems

You've already seen `stream()` vs `astream()` in your Session 6 materials. Here's why async is **non-negotiable** for agents: an agent might call 5 tools simultaneously — weather API, database lookup, calculator, web search, email sender. If you do this sequentially (sync), you wait for each to finish. Async does them all in parallel.

```python
import asyncio
import time

# ❌ SYNCHRONOUS — Sequential, Blocking
def sync_call_llm(prompt: str) -> str:
    """Simulates a blocking LLM API call."""
    time.sleep(2)  # Blocks everything
    return f"Response to: {prompt}"

def run_sync_pipeline():
    start = time.time()
    results = []
    prompts = ["Summarize resume 1", "Summarize resume 2", "Summarize resume 3"]
    for prompt in prompts:
        results.append(sync_call_llm(prompt))
    print(f"Sync took: {time.time() - start:.2f}s")  # ~6 seconds
    return results


# ✅ ASYNCHRONOUS — Concurrent, Non-Blocking
async def async_call_llm(prompt: str) -> str:
    """Simulates a non-blocking LLM API call."""
    await asyncio.sleep(2)  # Releases control to event loop
    return f"Response to: {prompt}"

async def run_async_pipeline():
    start = time.time()
    prompts = ["Summarize resume 1", "Summarize resume 2", "Summarize resume 3"]
    # asyncio.gather fires ALL calls concurrently
    results = await asyncio.gather(*[async_call_llm(p) for p in prompts])
    print(f"Async took: {time.time() - start:.2f}s")  # ~2 seconds
    return results

# Run it
asyncio.run(run_async_pipeline())
```

**The key insight:** `asyncio.gather()` is your best friend in agentic systems. When your agent needs to call multiple tools, gather them all into a single `await`.

#### 1.2 Classes — Building Reusable AI Components

Every production AI system uses OOP. Agents, tools, memory — all are classes.

```python
from dataclasses import dataclass
from typing import Optional
import asyncio

# A reusable LLM wrapper class
class LLMClient:
    """
    A base class for any LLM provider.
    Real agents will extend this with specific provider logic.
    """
    def __init__(self, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        self._call_count = 0  # Track usage (private)

    def __repr__(self) -> str:
        return f"LLMClient(model={self.model_name}, temp={self.temperature})"

    async def ainvoke(self, prompt: str) -> str:
        """Async invoke — the core method every agent uses."""
        self._call_count += 1
        # In real code: call openai.ChatCompletion.acreate() or google.generativeai
        await asyncio.sleep(0.1)  # Simulating API latency
        return f"[{self.model_name}] Response #{self._call_count}: {prompt[:50]}..."

    @property
    def usage_stats(self) -> dict:
        return {"model": self.model_name, "calls_made": self._call_count}


# Subclass for a specialized agent role
class SummarizerAgent(LLMClient):
    """An agent specialized in summarization tasks."""
    SYSTEM_PROMPT = "You are an expert summarizer. Always respond in bullet points."

    def __init__(self):
        super().__init__(model_name="gemini-2.5-flash", temperature=0.3)

    async def summarize(self, text: str, max_words: int = 100) -> str:
        prompt = f"{self.SYSTEM_PROMPT}\n\nSummarize in {max_words} words:\n{text}"
        return await self.ainvoke(prompt)


# Usage
async def main():
    agent = SummarizerAgent()
    result = await agent.summarize("LangChain is a framework for building LLM applications...")
    print(result)
    print(agent.usage_stats)

asyncio.run(main())
```

### 🏗️ Mini-Project 1: Async Resume Batch Processor

**Goal:** Process 50 resumes concurrently using `asyncio.gather()`, returning structured summaries.

```python
import asyncio
import json
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize LLM — from your Session 6 materials
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

async def process_single_resume(resume_text: str, candidate_id: int) -> dict:
    """Process one resume asynchronously."""
    prompt = f"""
    Analyze this resume and return a JSON object with exactly these fields:
    - name: string
    - total_experience_years: number
    - top_3_skills: list of strings
    - seniority_level: "junior" | "mid" | "senior"
    
    Resume:
    {resume_text}
    
    Return ONLY valid JSON, no explanation.
    """
    # Use LangChain's async invoke
    response = await llm.ainvoke(prompt)
    try:
        return {"id": candidate_id, "data": json.loads(response.content)}
    except json.JSONDecodeError:
        return {"id": candidate_id, "error": "Parse failure", "raw": response.content}

async def batch_process_resumes(resumes: List[str]) -> List[dict]:
    """Process ALL resumes concurrently — this is the Agentic power move."""
    tasks = [
        process_single_resume(resume, idx)
        for idx, resume in enumerate(resumes)
    ]
    # Fire all tasks at once — no sequential waiting
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return list(results)

# --- Test it ---
sample_resumes = [
    "John Doe, 5 years Python developer, skills: FastAPI, Docker, Kubernetes",
    "Jane Smith, 2 years ML engineer, skills: TensorFlow, Pandas, SQL",
    "Bob Wilson, 10 years architect, skills: AWS, Microservices, Java",
]

results = asyncio.run(batch_process_resumes(sample_resumes))
for r in results:
    print(json.dumps(r, indent=2))
```

**What this teaches you:** async programming, LangChain's `.ainvoke()`, error handling in concurrent tasks.

---

## 📐 STAGE 2 — Structured Outputs with Pydantic + LangChain
### *(Duration: 1–2 weeks)*

### Key Concepts to Master

#### 2.1 Why Raw LLM Output is Dangerous in Production

As your Session 6 materials show: "raw LLM output" is a string. In production, a string is a disaster:
- It might say `"name: John"` or `"Name: John"` or `"The person's name is John"` — all different formats
- Parsing failures cascade into broken pipelines
- No type safety, no validation

**Pydantic is your contract** between the LLM and your application.

#### 2.2 Pydantic Models — Deep Dive

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Literal
from enum import Enum

# --- Basic Model ---
class Skill(BaseModel):
    name: str
    proficiency: Literal["beginner", "intermediate", "expert"]
    years_used: float = Field(ge=0, le=50, description="Years of experience with this skill")

# --- Nested & Complex Model ---
class CandidateProfile(BaseModel):
    """
    Pydantic enforces this schema on whatever the LLM returns.
    If the LLM hallucinates a field or gives wrong types → ValidationError.
    """
    full_name: str = Field(min_length=2, max_length=100)
    email: Optional[str] = Field(default=None, pattern=r'^[\w.-]+@[\w.-]+\.\w+$')
    total_experience_years: float = Field(ge=0, description="Total professional experience")
    skills: List[Skill] = Field(min_length=1, max_length=20)
    seniority_level: Literal["junior", "mid", "senior", "principal"]
    is_remote_eligible: bool = True
    expected_salary_usd: Optional[int] = Field(default=None, ge=30000)

    # --- Custom Field Validator ---
    @field_validator('total_experience_years')
    @classmethod
    def validate_experience(cls, v: float) -> float:
        if v > 50:
            raise ValueError("Experience cannot exceed 50 years")
        return round(v, 1)  # Normalize to 1 decimal

    # --- Model-Level Validator (cross-field logic) ---
    @model_validator(mode='after')
    def validate_seniority_matches_experience(self) -> 'CandidateProfile':
        exp = self.total_experience_years
        level = self.seniority_level
        rules = {"junior": (0, 3), "mid": (2, 7), "senior": (5, 20), "principal": (10, 50)}
        min_exp, max_exp = rules[level]
        if not (min_exp <= exp <= max_exp):
            raise ValueError(
                f"Seniority '{level}' requires {min_exp}-{max_exp} years, got {exp}"
            )
        return self

# --- Test Pydantic Validation ---
try:
    # Valid profile
    candidate = CandidateProfile(
        full_name="Priya Sharma",
        email="priya@example.com",
        total_experience_years=6.5,
        skills=[
            Skill(name="Python", proficiency="expert", years_used=5),
            Skill(name="LangChain", proficiency="intermediate", years_used=1.5),
        ],
        seniority_level="senior",
    )
    print("✅ Valid:", candidate.model_dump_json(indent=2))

except Exception as e:
    print("❌ Validation Error:", e)

try:
    # Invalid — junior with 8 years experience (will trigger model_validator)
    bad_candidate = CandidateProfile(
        full_name="Test User",
        total_experience_years=8.0,
        skills=[Skill(name="Java", proficiency="expert", years_used=8)],
        seniority_level="junior",  # ← mismatch!
    )
except Exception as e:
    print("❌ Caught mismatch:", e)
```

#### 2.3 Pydantic + LangChain: PydanticOutputParser

As your Session 6 covers the `PydanticOutputParser` — here's the complete pattern with error recovery:

```python
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import OutputFixingParser
from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Define your Pydantic schema
class JobAnalysis(BaseModel):
    job_title: str = Field(description="The exact job title from the posting")
    required_skills: List[str] = Field(description="List of required technical skills")
    nice_to_have_skills: List[str] = Field(description="Optional/preferred skills")
    experience_years_required: int = Field(description="Minimum years of experience required")
    remote_policy: str = Field(description="Remote work policy: remote/hybrid/onsite")
    estimated_salary_range: str = Field(description="Salary range if mentioned, else 'Not disclosed'")

# 2. Create the parser
parser = PydanticOutputParser(pydantic_object=JobAnalysis)

# 3. Build the prompt — note how we inject format_instructions
prompt_template = PromptTemplate(
    template="""
    Analyze the following job description and extract key information.
    
    Job Description:
    {job_description}
    
    {format_instructions}
    
    Important: Return ONLY valid JSON matching the schema above.
    """,
    input_variables=["job_description"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

# 4. Build the chain using LCEL (LangChain Expression Language)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1  # Lower temperature for structured output
)

# Chain: prompt → llm → parser
chain = prompt_template | llm | parser

# 5. Auto-fixing parser — retries when LLM gives malformed JSON
fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=llm)
robust_chain = prompt_template | llm | fixing_parser

# 6. Invoke with error handling
def analyze_job(job_description: str) -> JobAnalysis:
    try:
        result = robust_chain.invoke({"job_description": job_description})
        return result
    except Exception as e:
        print(f"⚠️ Chain failed: {e}")
        # Fallback: return a default/empty analysis
        return JobAnalysis(
            job_title="Unknown",
            required_skills=[],
            nice_to_have_skills=[],
            experience_years_required=0,
            remote_policy="Unknown",
            estimated_salary_range="Not disclosed"
        )

# --- Test ---
sample_job = """
Senior ML Engineer at TechCorp
We're looking for a Senior ML Engineer with 5+ years experience.
Must have: Python, TensorFlow, MLflow, Docker, Kubernetes
Nice to have: LLMs, LangChain, Ray
This is a hybrid role (3 days in office, Bangalore). Salary: ₹40-60 LPA
"""

analysis = analyze_job(sample_job)
print(analysis.model_dump_json(indent=2))
```

#### 2.4 Streaming with Pydantic — Real-Time Structured Output

```python
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))

async def stream_with_display(prompt: str):
    """
    Stream token-by-token while accumulating for final Pydantic parse.
    This is how ChatGPT-style typing effect works.
    """
    print("🤖 Generating: ", end="", flush=True)
    accumulated = ""
    
    async for chunk in llm.astream(prompt):
        token = chunk.content
        print(token, end="", flush=True)
        accumulated += token
    
    print("\n✅ Stream complete")
    return accumulated

asyncio.run(stream_with_display("Explain transformer attention in 3 sentences"))
```

### 🏗️ Mini-Project 2: Structured Job Board Parser

**Goal:** Build a CLI tool that takes any job posting URL/text, extracts structured data with Pydantic, and outputs a clean JSON report with validation.

```python
# Full pipeline: Input text → LangChain chain → Pydantic schema → JSON output
# Add: retry logic (max 3 attempts), logging failures, batch mode for multiple jobs
```

---

## 🧠 STAGE 3 — Memory, Conversations & Tool Integration
### *(Duration: 2–3 weeks)*

### Key Concepts to Master

#### 3.1 How LLMs "Remember" — The Illusion of Memory

Your Session 7 materials explain this perfectly: **LLMs have NO inherent memory**. Every API call is stateless. The illusion of memory comes from passing the entire conversation history as input tokens.

```
Turn 1: [system_prompt + user_msg_1] → response_1
Turn 2: [system_prompt + user_msg_1 + response_1 + user_msg_2] → response_2
Turn 3: [system_prompt + user_msg_1 + response_1 + user_msg_2 + response_2 + user_msg_3] → response_3
```

This grows linearly with conversation length → hits context window → you need memory management.

#### 3.2 LangChain Memory Types — A Technical Comparison

```python
from langchain.memory import (
    ConversationBufferMemory,           # Keep ALL history — simple, hits context window
    ConversationBufferWindowMemory,     # Keep last K turns — sliding window
    ConversationSummaryMemory,          # Summarize old turns — uses extra LLM calls
    ConversationSummaryBufferMemory,    # Hybrid: summary + recent raw turns
    ConversationTokenBufferMemory,      # Budget by token count, not turn count
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain
import os
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))

# --- TYPE 1: Buffer Memory (Keep everything) ---
buffer_memory = ConversationBufferMemory(return_messages=True)
# Good for: Short conversations, debugging
# Bad for: Long sessions (blows up context window)

# --- TYPE 2: Window Memory (Keep last K turns) ---
window_memory = ConversationBufferWindowMemory(k=5, return_messages=True)
# Good for: Customer support chats (recent context matters most)
# Bad for: When early context is critical

# --- TYPE 3: Summary Memory (Compress history) ---
summary_memory = ConversationSummaryMemory(llm=llm, return_messages=True)
# Good for: Long sessions where gist > verbatim
# Bad for: When exact wording matters

# --- TYPE 4: Summary Buffer (Best of both) ---
summary_buffer_memory = ConversationSummaryBufferMemory(
    llm=llm,
    max_token_limit=500,  # Keep raw text until 500 tokens, then summarize
    return_messages=True
)
# Good for: Production chatbots — RECOMMENDED DEFAULT


# --- Build a complete chatbot with summary buffer memory ---
class SmartChatbot:
    def __init__(self, system_persona: str):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=800,
            return_messages=True,
            memory_key="chat_history"
        )
        self.system_persona = system_persona
        self._conversation_history = []

    async def chat(self, user_message: str) -> str:
        # Load memory variables
        memory_vars = self.memory.load_memory_variables({})
        history = memory_vars.get("chat_history", [])
        
        # Build the full message list
        messages = [
            {"role": "system", "content": self.system_persona},
            # Inject compressed history here
            *[{"role": m.type, "content": m.content} for m in history],
            {"role": "user", "content": user_message}
        ]
        
        # Get response
        response = await self.llm.ainvoke(str(messages))
        
        # Save to memory
        self.memory.save_context(
            {"input": user_message},
            {"output": response.content}
        )
        
        return response.content
    
    def get_memory_summary(self) -> str:
        """See what the bot currently 'remembers'."""
        vars = self.memory.load_memory_variables({})
        return str(vars.get("chat_history", "No history yet"))


# Test the chatbot
async def demo_chatbot():
    bot = SmartChatbot(
        system_persona="You are a helpful Python tutor. Be concise and use code examples."
    )
    
    conversations = [
        "What is a decorator in Python?",
        "Can you show me a real-world example of the one you just explained?",
        "How does that relate to what we discussed about decorators earlier?",  # Tests memory
    ]
    
    for msg in conversations:
        print(f"\n👤 User: {msg}")
        response = await bot.chat(msg)
        print(f"🤖 Bot: {response[:200]}...")

asyncio.run(demo_chatbot())
```

#### 3.3 Function Calling / Tool Integration (Session 8 Deep Dive)

Your Session 8 materials cover the full lifecycle. Here's the production-grade pattern:

```python
import json
import asyncio
import requests
from typing import Any, Callable, Dict, List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool, StructuredTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# STEP 1: Define Tools with Pydantic schemas (type-safe tools)
# ============================================================

class WeatherInput(BaseModel):
    city: str = Field(description="City name, e.g., 'Hyderabad'")
    date: str = Field(default="today", description="Date in YYYY-MM-DD format or 'today'")

class CalculatorInput(BaseModel):
    expression: str = Field(description="Mathematical expression, e.g., '(15 * 8) / 3'")

class WebSearchInput(BaseModel):
    query: str = Field(description="Search query for retrieving current information")


# ============================================================
# STEP 2: Implement the actual tool functions
# ============================================================

@tool(args_schema=WeatherInput)
def get_weather(city: str, date: str = "today") -> str:
    """
    Fetches current or forecast weather for a given city.
    Use when user asks about weather, temperature, rain, or conditions.
    """
    # In production: call OpenWeatherMap API
    # Simulated response for demo
    mock_data = {
        "Hyderabad": {"temp": "32°C", "condition": "Partly Cloudy", "humidity": "65%"},
        "Mumbai": {"temp": "29°C", "condition": "Humid", "humidity": "80%"},
    }
    city_data = mock_data.get(city, {"temp": "N/A", "condition": "City not found", "humidity": "N/A"})
    return json.dumps({
        "city": city,
        "date": date,
        "temperature": city_data["temp"],
        "condition": city_data["condition"],
        "humidity": city_data["humidity"],
        "source": "WeatherAPI"
    })

@tool(args_schema=CalculatorInput)
def calculator(expression: str) -> str:
    """
    Evaluates mathematical expressions safely.
    Use for any computation: arithmetic, percentages, conversions.
    """
    try:
        # Safe eval — only allows math operations
        allowed_chars = set('0123456789+-*/().% ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid expression (only math operations allowed)"
        result = eval(expression)  # In production: use numexpr or sympy
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {str(e)}"

@tool(args_schema=WebSearchInput)
def web_search(query: str) -> str:
    """
    Searches the web for current, real-time information.
    Use when user asks about recent events, news, or any time-sensitive data.
    """
    # In production: use SerpAPI, Tavily, or DuckDuckGo
    return f"[Mock Search Results for '{query}']: Top results about {query} from the web."


# ============================================================
# STEP 3: Build the Tool-Calling Agent
# ============================================================

def build_tool_agent(tools: List) -> AgentExecutor:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )
    
    # System prompt — critical for guiding tool selection
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant with access to tools.
        
        TOOL SELECTION RULES:
        - Use get_weather ONLY for weather/temperature/climate queries
        - Use calculator ONLY for mathematical computations
        - Use web_search for any real-time or recent information needs
        - If you can answer from your knowledge, do NOT call a tool
        - Always validate tool results before presenting to user
        
        Be concise and factual."""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,           # Show reasoning steps
        max_iterations=5,       # Prevent infinite loops
        handle_parsing_errors=True,
        return_intermediate_steps=True  # For debugging
    )


# ============================================================
# STEP 4: Run the agent
# ============================================================

async def run_tool_agent():
    tools = [get_weather, calculator, web_search]
    agent_executor = build_tool_agent(tools)
    
    test_queries = [
        "What's the weather in Hyderabad today?",
        "If it rains for 3 days this week and I need to buy umbrellas at ₹250 each for 15 employees, what's the total cost?",
        "What are the latest AI news this week?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🧑 Query: {query}")
        result = await agent_executor.ainvoke({"input": query})
        print(f"🤖 Final Answer: {result['output']}")

asyncio.run(run_tool_agent())
```

### 🏗️ Mini-Project 3: AI-Powered Personal Finance Assistant

**Goal:** Build a conversational chatbot with memory + 4 tools: calculator, expense tracker (writes to CSV), currency converter, and spending analyzer.

```python
# Extended challenge:
# - Use ConversationSummaryBufferMemory for multi-turn memory
# - Implement 4 tools with Pydantic schemas
# - Add error handling with Pydantic validation
# - Stream responses token-by-token
# - Export conversation summary to file
```

---

## 🤖 STAGE 4 — Agentic Reasoning: From Linear to ReAct
### *(Duration: 2–3 weeks)*

### The Critical Conceptual Shift

**Linear LLM Call (what you start with):**
```
User Input → Prompt → LLM → Response → Done
```

**Agentic Reasoning (what you build toward):**
```
User Input → LLM thinks → Decides action → Calls tool → Observes result
           → LLM thinks again → Decides next action → Calls another tool
           → Observes result → LLM thinks → Has enough info → Final Answer
```

This loop — **Thought → Action → Observation** — is called **ReAct** (Reasoning + Acting).

### Key Concepts to Master

#### 4.1 ReAct Pattern — Manual Implementation

Understanding ReAct from scratch before using frameworks:

```python
import asyncio
import json
from typing import Dict, Any, List, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()

class AgentAction(BaseModel):
    thought: str = Field(description="The agent's reasoning for its next step")
    action: str = Field(description="The tool to call. Use 'FINAL_ANSWER' when done")
    action_input: Dict[str, Any] = Field(description="Input to pass to the tool")

class ReActAgent:
    """
    Manual ReAct implementation — understand the internals before using LangChain agents.
    
    The loop:
    1. Agent THINKS (generates thought + action + input)
    2. We EXECUTE the action (call the tool)
    3. Agent OBSERVES the result
    4. Repeat until agent outputs FINAL_ANSWER
    """
    
    REACT_PROMPT = """You are an AI agent that solves problems step-by-step using tools.

Available tools:
{tools_description}

Your response MUST always be a JSON object with this exact structure:
{{
  "thought": "Your step-by-step reasoning about what to do next",
  "action": "tool_name or FINAL_ANSWER",
  "action_input": {{"key": "value"}} or {{"answer": "your final answer text"}}
}}

Previous steps:
{scratchpad}

User question: {question}

Think carefully. Use tools only when needed. When you have the final answer, set action to FINAL_ANSWER."""

    def __init__(self, tools: Dict[str, callable]):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )
        self.tools = tools
        self.max_steps = 8
    
    def _format_tools(self) -> str:
        descriptions = []
        for name, func in self.tools.items():
            descriptions.append(f"- {name}: {func.__doc__ or 'No description'}")
        return "\n".join(descriptions)
    
    async def _think(self, question: str, scratchpad: str) -> AgentAction:
        """Ask the LLM what to do next."""
        prompt = self.REACT_PROMPT.format(
            tools_description=self._format_tools(),
            scratchpad=scratchpad,
            question=question
        )
        response = await self.llm.ainvoke(prompt)
        
        # Parse the JSON response
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        
        action_dict = json.loads(content)
        return AgentAction(**action_dict)
    
    def _execute(self, action: str, action_input: Dict) -> str:
        """Execute the chosen tool."""
        if action not in self.tools:
            return f"Error: Tool '{action}' not found. Available: {list(self.tools.keys())}"
        try:
            return str(self.tools[action](**action_input))
        except Exception as e:
            return f"Tool execution error: {str(e)}"
    
    async def run(self, question: str) -> str:
        """The main ReAct loop."""
        scratchpad = ""
        
        for step in range(self.max_steps):
            print(f"\n--- Step {step + 1} ---")
            
            # THINK
            action = await self._think(question, scratchpad)
            print(f"💭 Thought: {action.thought}")
            print(f"🔧 Action: {action.action}")
            print(f"📥 Input: {action.action_input}")
            
            # FINAL ANSWER?
            if action.action == "FINAL_ANSWER":
                answer = action.action_input.get("answer", str(action.action_input))
                print(f"\n✅ FINAL ANSWER: {answer}")
                return answer
            
            # EXECUTE
            observation = self._execute(action.action, action.action_input)
            print(f"👁️ Observation: {observation}")
            
            # Update scratchpad
            scratchpad += f"""
Step {step + 1}:
Thought: {action.thought}
Action: {action.action}
Input: {json.dumps(action.action_input)}
Observation: {observation}
"""
        
        return "Max steps reached without a final answer."


# --- Tool definitions ---
def get_weather(city: str) -> dict:
    """Get current weather for a city. Returns temperature and conditions."""
    weather_data = {
        "Hyderabad": {"temp_celsius": 34, "condition": "Sunny", "humidity_pct": 55},
        "Delhi": {"temp_celsius": 38, "condition": "Hazy", "humidity_pct": 40},
    }
    return weather_data.get(city, {"error": f"City '{city}' not found"})

def convert_celsius_to_fahrenheit(celsius: float) -> dict:
    """Convert temperature from Celsius to Fahrenheit."""
    fahrenheit = (celsius * 9/5) + 32
    return {"celsius": celsius, "fahrenheit": fahrenheit}

def get_clothing_recommendation(temperature_celsius: float, condition: str) -> str:
    """Get clothing recommendation based on weather conditions."""
    if temperature_celsius > 35:
        return "Wear lightweight cotton, carry water, use sunscreen"
    elif temperature_celsius > 25:
        return "Light clothes, sunglasses recommended"
    elif temperature_celsius > 15:
        return "Layer up with a jacket"
    else:
        return "Wear warm clothes, coat recommended"


# --- Run the ReAct agent ---
async def main():
    tools = {
        "get_weather": get_weather,
        "convert_celsius_to_fahrenheit": convert_celsius_to_fahrenheit,
        "get_clothing_recommendation": get_clothing_recommendation,
    }
    
    agent = ReActAgent(tools=tools)
    
    # This requires MULTIPLE tool calls chained together:
    result = await agent.run(
        "What's the weather in Hyderabad? Convert the temperature to Fahrenheit "
        "and tell me what to wear."
    )

asyncio.run(main())
```

#### 4.2 LangGraph — State Machine for Agents (Advanced)

```python
# LangGraph is the next evolution: agents as graph nodes with state
# Install: pip install langgraph

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from typing import TypedDict, Annotated, List
import operator

class AgentState(TypedDict):
    """The state that flows through the graph nodes."""
    messages: Annotated[List, operator.add]  # Accumulate messages
    tool_calls_made: int
    final_answer: str

def agent_node(state: AgentState) -> AgentState:
    """The LLM reasoning node."""
    # Call LLM with current state
    # Returns updated state with new messages
    pass

def tool_node(state: AgentState) -> AgentState:
    """Execute tool calls from agent's last message."""
    pass

def should_continue(state: AgentState) -> str:
    """Router: should we call more tools, or are we done?"""
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"  # Route to tool execution
    return END         # We're done

# Build the graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")  # After tools, back to agent

compiled_graph = graph.compile()
```

### 🏗️ Mini-Project 4: Research Report Generator (Agentic)

**Goal:** Build an agent that, given a topic, autonomously plans, searches multiple sources, synthesizes information, and writes a structured research report — all without human intervention.

```python
# The agent should:
# 1. Decompose the topic into 3-5 sub-questions
# 2. Call web_search for each sub-question (concurrently via asyncio.gather)
# 3. Synthesize all search results
# 4. Use Pydantic to structure the final report
# 5. Stream the report to the user token-by-token
```

---

## 🌐 STAGE 5 — Multi-Agent Systems
### *(Duration: 3–4 weeks)*

### Key Concepts to Master

#### 5.1 Why Single Agents Aren't Enough

A single agent has limitations:
- Can't specialize deeply in multiple domains simultaneously
- Long complex tasks cause context drift
- No parallelism across independent sub-tasks
- Single point of failure

**Multi-agent systems** solve this with division of labor.

#### 5.2 Multi-Agent Architecture Patterns

**Pattern 1: Sequential Pipeline**
```
Researcher Agent → Writer Agent → Editor Agent → Publisher Agent
```

**Pattern 2: Supervisor + Workers**
```
                 Supervisor Agent
                /       |       \
     Researcher   Analyst   Writer
```

**Pattern 3: Peer Collaboration (Debate)**
```
Agent A ←→ Agent B ←→ Agent C
(All critique and improve each other's output)
```

#### 5.3 Building a Multi-Agent System from Scratch

```python
import asyncio
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# BASE AGENT CLASS
# ============================================================

class BaseAgent:
    """Foundation for all specialized agents."""
    
    def __init__(self, name: str, role: str, goal: str, backstory: str):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        self._memory: List[str] = []  # Simple message log
    
    @property
    def system_prompt(self) -> str:
        return f"""You are {self.name}, a {self.role}.
        
Your goal: {self.goal}
Your background: {self.backstory}

IMPORTANT: Stay strictly within your role. Do not perform tasks outside your expertise.
Pass clear, actionable output to the next agent in the pipeline."""
    
    async def execute(self, task: str, context: str = "") -> str:
        """Execute a task with optional context from previous agents."""
        full_prompt = f"""{self.system_prompt}

Context from previous agents:
{context if context else "None — you are the first agent."}

Your current task:
{task}

Provide your best output for this task."""
        
        response = await self.llm.ainvoke(full_prompt)
        result = response.content
        self._memory.append(f"Task: {task[:100]}... | Output: {result[:100]}...")
        return result
    
    def __repr__(self) -> str:
        return f"Agent(name={self.name}, role={self.role})"


# ============================================================
# SPECIALIZED AGENTS
# ============================================================

class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Dr. Arjun",
            role="Senior Research Analyst",
            goal="Find accurate, relevant, and comprehensive information on any topic",
            backstory="PhD in Information Science with 15 years of research experience. "
                     "Expert at identifying key facts, statistics, and insights."
        )
    
    async def research(self, topic: str) -> str:
        return await self.execute(
            task=f"Research the topic '{topic}'. Identify: "
                 "1) Key facts and statistics "
                 "2) Recent developments "
                 "3) Main controversies or debates "
                 "4) Expert opinions "
                 "Format as numbered sections."
        )


class AnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Priya",
            role="Strategic Business Analyst",
            goal="Analyze research data to extract actionable insights and patterns",
            backstory="MBA from IIM with expertise in data analysis and strategic thinking. "
                     "Specializes in synthesizing complex information into clear insights."
        )
    
    async def analyze(self, research_output: str, focus_area: str) -> str:
        return await self.execute(
            task=f"Analyze the following research with focus on: {focus_area}\n\n"
                 f"Identify: strengths, weaknesses, opportunities, threats (SWOT). "
                 f"Draw 3 key actionable insights.",
            context=f"Research data:\n{research_output}"
        )


class WriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Kavya",
            role="Technical Content Writer",
            goal="Transform research and analysis into clear, engaging, publication-ready content",
            backstory="Former journalist turned tech writer with expertise in making complex "
                     "topics accessible. Known for clarity and engaging prose."
        )
    
    async def write(self, research: str, analysis: str, content_type: str) -> str:
        return await self.execute(
            task=f"Write a {content_type} that presents this information in an "
                 f"engaging, clear, and well-structured way. "
                 f"Include: headline, introduction, main body with headers, conclusion.",
            context=f"Research:\n{research}\n\nAnalysis:\n{analysis}"
        )


class EditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Rahul",
            role="Senior Editor and Quality Controller",
            goal="Ensure all content is accurate, clear, well-structured, and publication-ready",
            backstory="20 years in publishing with a reputation for improving content quality "
                     "without losing the author's voice. Expert at fact-checking and clarity."
        )
    
    async def edit(self, draft_content: str) -> str:
        return await self.execute(
            task="Review and improve this draft. Check for: "
                 "1) Factual accuracy and logical consistency "
                 "2) Clarity and readability "
                 "3) Structure and flow "
                 "4) Grammar and style "
                 "Return the improved version with a brief editor's note on changes made.",
            context=f"Draft to edit:\n{draft_content}"
        )


# ============================================================
# SUPERVISOR / ORCHESTRATOR AGENT
# ============================================================

class SupervisorAgent(BaseAgent):
    """
    The orchestrator — decides which agents to call and in what order.
    This is the 'brain' of the multi-agent system.
    """
    
    def __init__(self, available_agents: List[BaseAgent]):
        super().__init__(
            name="Vikram",
            role="Project Manager and Orchestrator",
            goal="Coordinate specialized agents to produce the best possible output efficiently",
            backstory="Expert project manager who understands each team member's strengths "
                     "and assigns the right tasks to the right agents."
        )
        self.available_agents = {agent.name: agent for agent in available_agents}
    
    async def plan_and_execute(self, user_request: str) -> Dict[str, Any]:
        """
        The supervisor's main loop:
        1. Plan which agents to use
        2. Execute in the right order
        3. Combine outputs into final result
        """
        print(f"\n🎯 Supervisor received: {user_request}")
        results = {}
        
        # For this example: always use full pipeline
        # In advanced systems: supervisor dynamically decides
        
        # Stage 1: Research
        print("\n📚 Stage 1: Research Agent working...")
        researcher = ResearcherAgent()
        research_result = await researcher.research(user_request)
        results["research"] = research_result
        print(f"✅ Research complete ({len(research_result)} chars)")
        
        # Stage 2: Analysis (can run after research)
        print("\n🔍 Stage 2: Analyst working...")
        analyst = AnalystAgent()
        analysis_result = await analyst.analyze(research_result, focus_area=user_request)
        results["analysis"] = analysis_result
        print(f"✅ Analysis complete ({len(analysis_result)} chars)")
        
        # Stage 3: Writing (needs both research + analysis)
        print("\n✍️ Stage 3: Writer working...")
        writer = WriterAgent()
        draft = await writer.write(research_result, analysis_result, content_type="blog post")
        results["draft"] = draft
        print(f"✅ Draft complete ({len(draft)} chars)")
        
        # Stage 4: Editing
        print("\n📝 Stage 4: Editor polishing...")
        editor = EditorAgent()
        final_content = await editor.edit(draft)
        results["final"] = final_content
        print(f"✅ Editing complete")
        
        return results


# ============================================================
# PARALLEL MULTI-AGENT EXECUTION
# ============================================================

class ParallelResearchSystem:
    """
    Multiple research agents working simultaneously on different aspects.
    Then a synthesis agent combines all findings.
    """
    
    def __init__(self, num_researchers: int = 3):
        self.researchers = [ResearcherAgent() for _ in range(num_researchers)]
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    async def parallel_research(self, topic: str, sub_topics: List[str]) -> str:
        """Research multiple sub-topics simultaneously using different agents."""
        print(f"\n🚀 Launching {len(sub_topics)} research agents in parallel...")
        
        # All agents work simultaneously — asyncio.gather is the key
        research_tasks = [
            researcher.research(f"{topic}: {sub_topic}")
            for researcher, sub_topic in zip(self.researchers, sub_topics)
        ]
        
        all_research = await asyncio.gather(*research_tasks)
        
        # Synthesize all research
        synthesis_prompt = f"""
        Synthesize the following research reports on '{topic}' into one comprehensive summary.
        
        {chr(10).join([f'Report {i+1} (on {sub_topics[i]}): {report[:500]}...' 
                      for i, report in enumerate(all_research)])}
        
        Create a unified, coherent summary that captures key insights from all reports.
        """
        
        response = await self.llm.ainvoke(synthesis_prompt)
        return response.content


# ============================================================
# RUN THE MULTI-AGENT SYSTEM
# ============================================================

async def main():
    # Example 1: Sequential Pipeline
    print("="*60)
    print("EXAMPLE 1: Sequential Multi-Agent Pipeline")
    print("="*60)
    
    supervisor = SupervisorAgent(available_agents=[])
    results = await supervisor.plan_and_execute("The impact of Agentic AI on software development")
    
    print("\n" + "="*60)
    print("FINAL OUTPUT:")
    print("="*60)
    print(results["final"][:1000] + "...")
    
    # Example 2: Parallel Research
    print("\n" + "="*60)
    print("EXAMPLE 2: Parallel Research System")
    print("="*60)
    
    parallel_system = ParallelResearchSystem(num_researchers=3)
    combined_research = await parallel_system.parallel_research(
        topic="LLM Agents",
        sub_topics=["Technical Architecture", "Real-world Applications", "Limitations and Risks"]
    )
    print("\nSynthesized Research:")
    print(combined_research[:500] + "...")

asyncio.run(main())
```

### 🏗️ Mini-Project 5: AI Software Development Team

**Goal:** Build a multi-agent "software team" where:
- **PM Agent** breaks down requirements into user stories
- **Architect Agent** designs the system architecture
- **Developer Agent** writes the actual code
- **QA Agent** reviews for bugs and edge cases
- **DevOps Agent** writes deployment configs

---

# PART 2 — THE RAG MASTERCLASS
## A Deep Dive into Retrieval-Augmented Generation

---

## 1️⃣ FOUNDATIONS & TEXT REPRESENTATION

### 1.1 What is RAG and Why It Exists

Your Session 10 materials open with the core analogy: LLMs are "super-smart students who read millions of books — but can't remember *everything*, especially recent news or your company's data."

**The fundamental problem:** An LLM's knowledge is **frozen at its training cutoff**. It cannot know:
- Your company's internal documents
- News from yesterday
- Your private customer data
- Anything that changed after training

**Why not just use "long-context" prompting?** Modern LLMs support 128K–1M token contexts. Why not just dump all your documents into the prompt?

| Factor | Long-Context Prompting | RAG |
|--------|------------------------|-----|
| **Cost** | ❌ Enormous — you pay for every token every call | ✅ Only relevant chunks sent |
| **Latency** | ❌ Slow — model processes all text every query | ✅ Fast — selective retrieval |
| **Accuracy** | ❌ "Lost in the Middle" — model ignores buried content | ✅ Precise — retrieves most relevant chunks |
| **Scalability** | ❌ Can't scale to millions of documents | ✅ Indexes millions of docs efficiently |
| **Updates** | ❌ Must re-inject everything when docs change | ✅ Re-embed only changed docs |
| **Privacy** | ❌ Entire corpus exposed each call | ✅ Only relevant chunks retrieved |

**RAG's formula:** `Answer = Retrieve(relevant_chunks) + Generate(LLM + chunks + query)`

Think of it like an open-book exam vs. a closed-book exam. RAG lets the AI take an open-book exam — it doesn't memorize everything, it knows *how to find the answer*.

---

### 1.2 Embeddings — The Mathematical Heart of RAG

**The core question:** How does a model compare "What is the company vacation policy?" with "Employees receive 25 days of paid leave per year" and know they're related?

They share zero words in common. Traditional keyword search (Bag-of-Words, TF-IDF) would fail here. **Embeddings** solve this.

#### What is an Embedding?

An **embedding** is a numerical vector — a list of floating-point numbers — that encodes the *semantic meaning* of text. Texts with similar meanings map to nearby points in high-dimensional space.

```
"What is the vacation policy?"     → [0.23, -0.87, 0.45, 0.12, ..., 0.67]  # 768 numbers
"Employees get 25 days of leave."  → [0.21, -0.82, 0.48, 0.15, ..., 0.63]  # 768 numbers
"The Eiffel Tower is in Paris."    → [0.91,  0.14, -0.33, 0.78, ..., -0.11] # 768 numbers
```

The first two vectors are close together (high cosine similarity). The third is far away (unrelated topic).

#### How Does a Model Create Embeddings?

```python
# Conceptual visualization of the embedding process

# Step 1: Tokenization
text = "Vacation policy"
tokens = ["Vacation", " policy"]  # WordPiece tokenization

# Step 2: Token → Dense Vector (learned during pre-training)
# Each token maps to a 768-dim vector from the embedding matrix
token_vectors = {
    "Vacation": [0.12, -0.34, ...],  # 768 floats
    "policy":   [0.45,  0.78, ...],  # 768 floats
}

# Step 3: Transformer layers refine vectors using attention
# Each token's vector is updated based on ALL other tokens in the sentence
# This is why "bank" in "river bank" vs "bank account" get different vectors

# Step 4: Pooling — combine all token vectors into ONE sentence vector
# Common strategies:
# - [CLS] token pooling: use the first special token's vector
# - Mean pooling: average all token vectors (most common for sentence embeddings)
# - Max pooling: take max value per dimension

# Final: one vector representing the ENTIRE text's meaning
sentence_vector = mean_pool([token_vectors["Vacation"], token_vectors["policy"]])
```

#### Embedding Model Comparison

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# ============================================================
# Option 1: HuggingFace Open-Source (Free, Local)
# ============================================================
# Best for: Privacy-sensitive data, cost-conscious projects

model_hf = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
# - Dimensions: 384 (compact)
# - Speed: Very fast (~14,000 sentences/second on GPU)
# - Quality: Good for general use
# - Cost: Free

model_hf_large = SentenceTransformer("BAAI/bge-large-en-v1.5")
# - Dimensions: 1024 (richer representation)
# - Speed: Slower than MiniLM
# - Quality: Excellent — consistently top MTEB leaderboard
# - Cost: Free (but needs more RAM/GPU)

# ============================================================
# Option 2: OpenAI API (Paid, Cloud)
# ============================================================
# Best for: Highest quality, production systems, mixed languages

from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    model="text-embedding-3-large",  # 3072 dimensions — highest quality
    input="Vacation policy text here"
)
embedding = response.data[0].embedding
# Cost: ~$0.00013 per 1K tokens
# Dimensions: 3072 (or 256/1536 with truncation support)

# ============================================================
# Option 3: Google / Vertex AI
# ============================================================
# Best for: When using Gemini as your LLM

from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
# Dimensions: 768
# Best used with Gemini LLM for consistency

# ============================================================
# Practical Comparison
# ============================================================

def compare_embeddings():
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    texts = [
        "What is the vacation leave policy?",           # Query
        "Employees receive 25 days of paid annual leave.",  # Relevant
        "The office is located in Hyderabad, India.",   # Irrelevant
        "All staff are entitled to annual paid holidays.",  # Also relevant (different words!)
    ]
    
    vectors = model.encode(texts)
    
    # Compute cosine similarity between query (index 0) and all others
    query_vec = vectors[0]
    for i, (text, vec) in enumerate(zip(texts[1:], vectors[1:]), 1):
        # Cosine similarity = dot product of normalized vectors
        similarity = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec))
        print(f"Similarity with text {i}: {similarity:.4f} | '{text[:50]}'")

compare_embeddings()
# Expected output:
# Similarity with text 1: 0.7832 | 'Employees receive 25 days of paid annual leave.'
# Similarity with text 2: 0.2341 | 'The office is located in Hyderabad, India.'
# Similarity with text 3: 0.8204 | 'All staff are entitled to annual paid holidays.'
```

**Key insight:** Text 3 ("All staff are entitled to annual paid holidays") has *higher* similarity than text 1 even though they share only one word ("paid"). This is the magic of semantic embeddings.

---

## 2️⃣ THE BUILDING BLOCKS — THE CORE RAG PIPELINE

### 2.1 Chunking Strategies — The Most Underestimated Component

Before embedding, you must split your documents into manageable pieces (chunks). This is **critically important** — bad chunking = bad retrieval = bad answers.

#### Why Chunk at All?

1. **Context window limits:** You can't embed a 500-page document as one vector
2. **Precision:** Embedding a small, focused chunk captures its meaning better
3. **Relevance:** You want to retrieve the *specific paragraph* that answers the query, not the whole chapter

#### Chunking Method 1: Fixed-Size Chunking

```python
from langchain.text_splitter import CharacterTextSplitter

fixed_splitter = CharacterTextSplitter(
    chunk_size=500,      # Max characters per chunk
    chunk_overlap=50,    # How many chars from prev chunk to include in next
    separator="\n"       # Split on newlines first
)

text = """
Section 1: Vacation Policy
All employees are entitled to 25 days of paid annual leave...

Section 2: Sick Leave
Employees may take up to 12 days of sick leave per year...
"""

chunks = fixed_splitter.split_text(text)
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {len(chunk)} chars | '{chunk[:80]}...'")
```

**Pros:** Simple, predictable, fast
**Cons:** May cut sentences mid-way; ignores document structure

#### Chunking Method 2: Recursive Character Splitting (Recommended Default)

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    # It tries these separators in ORDER — stops when chunks are small enough
    separators=[
        "\n\n",    # First try: paragraph breaks
        "\n",      # Then: line breaks
        ". ",      # Then: sentence ends
        ", ",      # Then: clause breaks
        " ",       # Then: word breaks
        "",        # Last resort: character-level split
    ]
)

chunks = recursive_splitter.split_text(text)
# This preserves paragraph structure when possible
# Falls back to sentence splitting when needed
# Never cuts mid-word
```

**Why this is the default:** It respects document structure hierarchy. Most LangChain tutorials use this.

#### Chunking Method 3: Semantic Chunking (Advanced, Best Quality)

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Uses embedding model to detect semantic boundaries
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

semantic_splitter = SemanticChunker(
    embeddings=embedding_model,
    breakpoint_threshold_type="percentile",  # or "standard_deviation", "interquartile"
    breakpoint_threshold_amount=95,          # Split when similarity drops below 95th percentile
)

# How it works:
# 1. Split text into sentences
# 2. Embed each sentence
# 3. Compare consecutive sentence embeddings
# 4. When similarity drops significantly → that's a chunk boundary

chunks = semantic_splitter.split_text(text)
# Chunks are semantically coherent — each chunk is about ONE topic
```

**Pros:** Best quality — chunks align with topic shifts, not arbitrary character counts
**Cons:** Slower (requires embedding every sentence), more expensive

#### The Overlap Parameter — Why It's Critical

```
Without overlap (chunk_overlap=0):
Chunk 1: "The employee must submit their leave request at least two weeks"
Chunk 2: "in advance. Requests submitted less than 5 days before"
Chunk 3: "will require manager approval."

→ If query asks "How much notice for leave?", the answer spans chunks 1-3
→ Any single chunk gives incomplete information

With overlap (chunk_overlap=100):
Chunk 1: "The employee must submit their leave request at least two weeks"
Chunk 2: "at least two weeks in advance. Requests submitted less than 5 days before"
Chunk 3: "less than 5 days before will require manager approval."

→ Each chunk now has enough context to answer the question independently
```

**Rule of thumb:** Use 10-20% overlap of your chunk size. For chunk_size=500, use chunk_overlap=50-100.

---

### 2.2 Indexing — Organizing for Fast Retrieval

Once you have chunks, you need to embed and store them efficiently.

```python
from langchain_community.vectorstores import Chroma, FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
import os

# ============================================================
# COMPLETE INDEXING PIPELINE
# ============================================================

async def build_index(documents_path: str) -> any:
    """
    Full pipeline: Load → Split → Embed → Store
    This is the 'offline' phase — done once (or on document updates).
    """
    
    # Step 1: Load documents
    print("📄 Loading documents...")
    loader = DirectoryLoader(
        documents_path,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader
    )
    raw_docs = loader.load()
    print(f"  Loaded {len(raw_docs)} document pages")
    
    # Step 2: Split into chunks
    print("✂️ Chunking documents...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=75,
        # Add metadata to each chunk
        add_start_index=True,
    )
    chunks = splitter.split_documents(raw_docs)
    print(f"  Created {len(chunks)} chunks")
    
    # Inspect a chunk's structure:
    sample_chunk = chunks[0]
    print(f"\n  Sample chunk content: '{sample_chunk.page_content[:100]}...'")
    print(f"  Sample chunk metadata: {sample_chunk.metadata}")
    # metadata contains: source filename, page number, start_index
    
    # Step 3: Create embeddings + store in vector DB
    print("\n🔢 Creating embeddings (this takes time)...")
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # FAISS — local, in-memory, fast (good for development)
    vectorstore = FAISS.from_documents(
        documents=chunks,
        embedding=embedding_model
    )
    
    # Persist to disk (so you don't re-embed every time)
    vectorstore.save_local("./faiss_index")
    print("✅ Index saved to ./faiss_index")
    
    return vectorstore


def load_existing_index() -> any:
    """Load a previously built index — no re-embedding needed."""
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = FAISS.load_local(
        "./faiss_index",
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )
    print("✅ Loaded existing index")
    return vectorstore
```

---

### 2.3 Vector Databases — The Storage Layer

**A vector database is a specialized database optimized to store and search high-dimensional vectors.**

Regular databases search by exact match or range queries: `WHERE salary > 50000`.
Vector databases search by **similarity**: "Find me the 5 vectors most similar to this query vector."

#### The Math Behind Nearest Neighbor Search

```python
import numpy as np

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Measures the ANGLE between two vectors (not distance).
    Range: -1 (opposite) to +1 (identical).
    Most common metric for text embeddings.
    """
    dot_product = np.dot(vec_a, vec_b)
    magnitude_a = np.linalg.norm(vec_a)
    magnitude_b = np.linalg.norm(vec_b)
    return dot_product / (magnitude_a * magnitude_b)

def euclidean_distance(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Straight-line distance between two points.
    Better for image embeddings, less common for text.
    """
    return np.linalg.norm(vec_a - vec_b)

# Brute-force k-NN search (exact, O(n) per query)
def exact_knn_search(query_vec: np.ndarray, all_vectors: list, k: int = 5) -> list:
    """
    Exact k-Nearest Neighbors: compare query against EVERY stored vector.
    Accurate but slow for large datasets (millions of vectors).
    """
    similarities = [
        (i, cosine_similarity(query_vec, vec))
        for i, vec in enumerate(all_vectors)
    ]
    # Sort by similarity (descending) and return top k
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:k]
```

#### kNN vs ANN — The Speed vs. Accuracy Tradeoff

| | Exact kNN | Approximate NN (ANN) |
|---|---|---|
| **Algorithm** | Compare against ALL vectors | Use index structures (HNSW, IVF) |
| **Accuracy** | 100% correct | ~95-99% correct (configurable) |
| **Speed** | O(n) — slow at scale | O(log n) — very fast |
| **Use case** | < 100K vectors | Millions to billions of vectors |
| **Examples** | FAISS flat index | FAISS IVF, Pinecone, Weaviate |

**HNSW (Hierarchical Navigable Small World)** is the most popular ANN algorithm — it builds a multi-layer graph where each layer is a "highway" that skips over many nodes, dramatically reducing search time.

#### Vector Database Comparison

```python
# ============================================================
# Option 1: FAISS (Facebook AI Similarity Search)
# Best for: Local development, research, <10M vectors
# ============================================================
from langchain_community.vectorstores import FAISS

faiss_store = FAISS.from_documents(chunks, embedding_model)
# Pros: Free, fast, runs locally
# Cons: No persistence without manual save, single machine only

# ============================================================
# Option 2: ChromaDB
# Best for: Local development with persistence, prototypes
# ============================================================
from langchain_community.vectorstores import Chroma

chroma_store = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model,
    persist_directory="./chroma_db",  # Auto-persists
    collection_name="hr_documents"
)
# Pros: Free, persistent by default, easy setup
# Cons: Not designed for massive scale

# ============================================================
# Option 3: Pinecone (Cloud, Managed)
# Best for: Production, massive scale, teams
# ============================================================
from langchain_pinecone import PineconeVectorStore
import pinecone

pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("hr-knowledge-base")

pinecone_store = PineconeVectorStore(
    index=index,
    embedding=embedding_model,
    text_key="text"
)
# Pros: Fully managed, scales to billions, fast globally
# Cons: Cost, external dependency

# ============================================================
# Option 4: Weaviate (Open-source, Cloud or Self-hosted)
# Best for: Complex metadata filtering, hybrid search
# ============================================================
# Supports: vector search + BM25 keyword search (hybrid)
# Unique: GraphQL API, multi-tenancy, modules for classification
```

---

## 3️⃣ IMPLEMENTATION DETAILS — COMPLETE RAG PIPELINE

### 3.1 What's Actually Stored in the Vector Database?

This is a key concept many tutorials skip. The database stores **three things per chunk**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Vector DB Entry                                                │
├─────────────────────────────────────────────────────────────────┤
│  1. ID (unique identifier)                                      │
│     "chunk_abc123_page5_offset_1200"                           │
│                                                                 │
│  2. Vector (the embedding — what's actually searched)          │
│     [0.234, -0.892, 0.451, 0.123, ..., 0.671]  # 768 floats   │
│                                                                 │
│  3. Metadata (stored alongside, not embedded — for filtering)  │
│     {                                                           │
│       "text": "Employees receive 25 days of paid leave...",    │  ← The raw text
│       "source": "hr_policy_2024.pdf",                          │  ← Document source
│       "page": 12,                                              │  ← Page number
│       "chunk_index": 47,                                       │  ← Position in doc
│       "document_type": "policy",                               │  ← Custom metadata
│       "department": "HR",                                      │  ← For filtering
│       "last_updated": "2024-01-15",                            │  ← Freshness tracking
│     }                                                           │
└─────────────────────────────────────────────────────────────────┘
```

**Critical:** The **vector** is what gets searched. The **raw text** is what gets sent to the LLM.

```python
# Full retrieval flow — showing exactly what happens
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# What actually happens during similarity_search:
def manual_search_flow(query: str, vectorstore: FAISS, k: int = 4):
    """
    Step-by-step breakdown of what vectorstore.similarity_search() does.
    """
    # Step 1: Embed the query using the SAME embedding model used during indexing
    query_embedding = embedding_model.embed_query(query)
    print(f"Query vector shape: {len(query_embedding)} dimensions")
    
    # Step 2: Search the vector index for the k nearest vectors
    # (This is where ANN algorithms shine — done in milliseconds)
    results = vectorstore.similarity_search_with_score(query, k=k)
    
    # Step 3: Return the raw text + metadata for each result
    for i, (doc, score) in enumerate(results):
        print(f"\nResult {i+1} (score={score:.4f}):")
        print(f"  Text: '{doc.page_content[:100]}...'")
        print(f"  Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"  Page: {doc.metadata.get('page', 'N/A')}")
    
    return results

# Using metadata filtering (advanced)
def filtered_search(vectorstore, query: str, department: str = None):
    """
    Search with metadata filters — e.g., only search HR documents.
    """
    filter_dict = {}
    if department:
        filter_dict["department"] = department
    
    results = vectorstore.similarity_search(
        query=query,
        k=4,
        filter=filter_dict  # Only returns chunks matching this metadata filter
    )
    return results
```

### 3.2 Building the Complete RAG Chain

```python
from langchain.chains import RetrievalQA
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# COMPLETE, PRODUCTION-GRADE RAG PIPELINE
# ============================================================

class RAGPipeline:
    """
    A complete RAG system with:
    - FAISS vector store
    - Metadata-enhanced retrieval  
    - Custom prompt template
    - Source citation in responses
    - Async support
    """
    
    RAG_PROMPT = """You are a helpful assistant answering questions based on the provided context.

INSTRUCTIONS:
- Answer ONLY based on the context below
- If the context doesn't contain the answer, say "I don't have information about this in my knowledge base"
- Always cite which document/section you got the information from
- Be concise but complete

CONTEXT:
{context}

QUESTION: {input}

Answer:"""
    
    def __init__(self, vectorstore: FAISS, model_name: str = "gemini-2.5-flash"):
        self.vectorstore = vectorstore
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1  # Low temperature for factual RAG
        )
        self.retriever = vectorstore.as_retriever(
            search_type="mmr",          # Maximum Marginal Relevance — reduces redundancy
            search_kwargs={
                "k": 6,                # Retrieve 6 chunks
                "fetch_k": 20,         # Fetch 20 candidates, then MMR selects best 6
                "lambda_mult": 0.7,    # Balance relevance (1.0) vs diversity (0.0)
            }
        )
        self._build_chain()
    
    def _build_chain(self):
        """Build the RAG chain using LCEL."""
        prompt = ChatPromptTemplate.from_template(self.RAG_PROMPT)
        
        # Chain 1: Stuff documents into prompt + call LLM
        document_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=prompt
        )
        
        # Chain 2: Retrieve + document chain
        self.chain = create_retrieval_chain(
            retriever=self.retriever,
            combine_docs_chain=document_chain
        )
    
    async def query(self, question: str, return_sources: bool = True) -> dict:
        """Query the RAG pipeline."""
        result = await self.chain.ainvoke({"input": question})
        
        response = {
            "question": question,
            "answer": result["answer"],
        }
        
        if return_sources:
            response["sources"] = [
                {
                    "content": doc.page_content[:200],
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page", "N/A"),
                }
                for doc in result.get("context", [])
            ]
        
        return response
    
    async def stream_query(self, question: str):
        """Stream the RAG answer token by token."""
        # First retrieve documents
        docs = await self.retriever.ainvoke(question)
        context = "\n\n".join([d.page_content for d in docs])
        
        prompt = self.RAG_PROMPT.format(context=context, input=question)
        
        print("🤖 Answer: ", end="", flush=True)
        async for chunk in self.llm.astream(prompt):
            print(chunk.content, end="", flush=True)
        print()  # Newline after streaming
        
        return [doc.metadata for doc in docs]  # Return sources


# Usage
async def demo_rag():
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # Mock: load pre-built index
    # vectorstore = FAISS.load_local("./faiss_index", embedding_model)
    
    # For demo: create a tiny in-memory store
    from langchain.schema import Document
    
    sample_docs = [
        Document(
            page_content="All employees are entitled to 25 days of paid annual leave per year.",
            metadata={"source": "hr_policy.pdf", "page": 5, "department": "HR"}
        ),
        Document(
            page_content="Maternity leave: 26 weeks of fully paid leave for primary caregivers.",
            metadata={"source": "hr_policy.pdf", "page": 8, "department": "HR"}
        ),
        Document(
            page_content="Work from home policy: Up to 3 days per week for eligible roles.",
            metadata={"source": "remote_policy.pdf", "page": 2, "department": "IT"}
        ),
    ]
    
    vectorstore = FAISS.from_documents(sample_docs, embedding_model)
    rag = RAGPipeline(vectorstore)
    
    questions = [
        "How many days of annual leave do employees get?",
        "What is the maternity leave policy?",
        "Can I work from home every day?",
        "What is the company's policy on salary increments?",  # Not in knowledge base
    ]
    
    for q in questions:
        print(f"\n{'='*60}")
        result = await rag.query(q)
        print(f"❓ Q: {result['question']}")
        print(f"💬 A: {result['answer']}")
        print(f"📚 Sources: {[s['source'] for s in result['sources']]}")

import asyncio
asyncio.run(demo_rag())
```

---

### 3.3 RAG vs Fine-Tuning — Decision Framework

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FINE-TUNING vs RAG — When to Use Each                    │
├────────────────────┬─────────────────────────────┬───────────────────────── ┤
│  Dimension         │  Fine-Tuning                 │  RAG                    │
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  Primary Purpose   │  Change HOW the model        │  Expand WHAT the model  │
│                    │  responds (style, format,    │  knows (new facts,      │
│                    │  tone, task-specific skill)  │  private documents)     │
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  Knowledge Type    │  Behavioral / stylistic      │  Factual / domain       │
│                    │  patterns                    │  specific data          │
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  Data Updates      │  Requires full retraining    │  Add documents, re-     │
│                    │  to incorporate new info     │  embed — minutes        │
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  Data Volume       │  Needs 100s-1000s of         │  Works even with 10     │
│                    │  high-quality examples       │  documents              │
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  Cost              │  High (GPU training time)    │  Low (inference only)   │
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  Interpretability  │  Black box — hard to trace   │  Can cite exact source  │
│                    │  what it learned             │  chunk for each answer  │
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  Hallucination     │  May hallucinate trained     │  Grounded in retrieved  │
│                    │  facts with confidence       │  documents — lower risk │
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  Use Case Examples │  Code completion assistant   │  Company Q&A chatbot    │
│                    │  Medical note generation     │  Legal document search  │
│                    │  Specific language style     │  Technical support bot  │
│                    │  Custom output format        │  Internal knowledge base│
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  Time to Deploy    │  Weeks (training pipeline)   │  Days (index + chain)   │
├────────────────────┼─────────────────────────────┼─────────────────────────┤
│  VERDICT           │  When behavior/style needs   │  When you have specific │
│                    │  to change at a deep level   │  documents to query     │
└────────────────────┴─────────────────────────────┴─────────────────────────┘

BEST PRACTICE: Use BOTH together.
Fine-tune for style/format → Add RAG for current knowledge.
Example: Fine-tune a model to write in your brand voice, then RAG it your product catalog.
```

---

## 4️⃣ ADVANCED INSIGHTS

### 4.1 The Three Phases of RAG in Detail

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE RAG LIFECYCLE                            │
│                                                                 │
│  OFFLINE (One-time or on update)                                │
│  ─────────────────────────────                                 │
│  Documents → Chunk → Embed → Index → Vector DB                 │
│                                                                 │
│  ONLINE (Every query)                                           │
│  ─────────────────────────────                                 │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │  RETRIEVAL   │   │ AUGMENTATION │   │   GENERATION     │   │
│  │              │   │              │   │                  │   │
│  │ Query         │→ │ Build        │→ │ LLM generates    │   │
│  │ → Embed       │   │ augmented    │   │ answer using     │   │
│  │ → ANN Search  │   │ prompt:      │   │ only the         │   │
│  │ → Rank/Filter │   │             │   │ provided         │   │
│  │ → Top-k docs  │   │ [System]    │   │ context          │   │
│  │              │   │ [Context]   │   │                  │   │
│  │ Quality       │   │ [Query]     │   │ Streams token    │   │
│  │ matters most  │   │             │   │ by token to user │   │
│  │ here!         │   │             │   │                  │   │
│  └──────────────┘   └──────────────┘   └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight:** "Retrieval" is 70% of where RAG quality is determined. If you retrieve the wrong chunks, the best LLM in the world can't save you. This is why chunking strategy and embedding model choice matter so much.

### 4.2 Common RAG Pitfalls — And How to Fix Them

#### Pitfall 1: "Lost in the Middle" Phenomenon

**Problem:** When you stuff many retrieved chunks into the prompt, LLMs perform well on information at the beginning and end of the context, but **ignore content in the middle**.

```python
# Empirical finding: In a 20-chunk context, the model focuses on chunks 1-3 and 18-20.
# Chunks 7-15 are frequently ignored in the generated answer.

# FIXES:
# 1. Reduce k (retrieve fewer, more precise chunks)
# 2. Re-rank results: put highest-relevance chunks FIRST and LAST
# 3. Use LongContextReorder from LangChain

from langchain.document_transformers import LongContextReorder

reorder = LongContextReorder()

def reorder_documents(docs):
    """
    Reorders so most relevant docs are at beginning and end.
    Least relevant go in the middle (where attention is lowest).
    LLMs pay most attention to first and last items in context.
    """
    return reorder.transform_documents(docs)
```

#### Pitfall 2: Retrieval Noise (Irrelevant Chunks)

**Problem:** Your similarity search retrieves chunks that are *somewhat* similar but don't actually answer the question.

```python
# FIXES:

# Fix 1: Use a Reranker model (cross-encoder)
# Cross-encoders jointly process query + document for better relevance scoring
# More accurate than bi-encoder (embedding) similarity, but slower

from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_results(query: str, docs: list, top_k: int = 3) -> list:
    """
    Two-stage retrieval:
    Stage 1: Fast ANN retrieval (get top 20)
    Stage 2: Accurate reranking (select top 3 from 20)
    """
    pairs = [(query, doc.page_content) for doc in docs]
    scores = reranker.predict(pairs)
    
    # Sort by reranker scores
    scored_docs = list(zip(docs, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    return [doc for doc, _ in scored_docs[:top_k]]

# Fix 2: Hybrid Search (vector + keyword BM25)
# Some queries are keyword-based ("TDS Section 80C"), not semantic
# Hybrid combines both for better coverage

from langchain.retrievers import BM25Retriever, EnsembleRetriever

bm25_retriever = BM25Retriever.from_documents(chunks, k=4)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.3, 0.7]  # 30% keyword, 70% semantic
)

# Fix 3: Self-querying retrieval
# LLM generates structured query with metadata filters
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

metadata_fields = [
    AttributeInfo(name="department", description="The department the policy applies to", type="string"),
    AttributeInfo(name="page", description="Page number in the source document", type="integer"),
]

self_query_retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    document_contents="HR and company policy documents",
    metadata_field_info=metadata_fields,
)
# Query: "What does HR say about remote work?" 
# → Auto-generates filter: {"department": "HR"} + semantic search
```

#### Pitfall 3: Query-Document Mismatch

**Problem:** Your query is short ("vacation days") but your chunks are dense paragraphs. Short queries embed differently from long paragraphs.

```python
# FIX: HyDE (Hypothetical Document Embeddings)
# Instead of embedding the query directly, ask the LLM to generate
# a HYPOTHETICAL answer, then embed that hypothetical answer.
# Hypothetical answers are linguistically similar to real chunks.

from langchain.chains import HypotheticalDocumentEmbedder

hyde_embedder = HypotheticalDocumentEmbedder.from_llm(
    llm=llm,
    base_embeddings=embedding_model,
    custom_prompt="""Given this question, write a short paragraph that would be 
    the IDEAL answer found in a document.
    
    Question: {QUESTION}
    
    Ideal document excerpt:"""
)

# Now use hyde_embedder instead of embedding_model for query embedding
# The hypothetical answer embeds much closer to actual relevant chunks
```

#### Pitfall 4: Chunk Boundary Problems

**Problem:** The answer to a query spans two chunks. Neither chunk alone is sufficient.

```python
# FIX: Parent Document Retriever
# Store SMALL chunks for precise retrieval
# But return LARGER parent chunks to the LLM for context

from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore

# Child splitter: small chunks for precise embedding
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200)

# Parent splitter: larger chunks for context
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)

docstore = InMemoryStore()

parent_retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)
parent_retriever.add_documents(raw_docs)

# How it works:
# Embed and store 200-char child chunks
# When child is retrieved, return its 1000-char parent to LLM
# Best of both worlds: precise retrieval + rich context
```

#### Pitfall 5: Evaluation Blindness

Most RAG systems are built without proper evaluation. Your Session 9 materials cover this — use structured metrics.

```python
from pydantic import BaseModel, Field
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI

class RAGEvaluationScore(BaseModel):
    """Pydantic schema for RAG evaluation results."""
    question: str
    answer: str
    retrieved_context: str
    
    # Metrics (0.0 to 1.0)
    faithfulness: float = Field(ge=0, le=1, 
        description="Is the answer grounded in the context? (no hallucination)")
    answer_relevance: float = Field(ge=0, le=1,
        description="Does the answer address the question?")
    context_precision: float = Field(ge=0, le=1,
        description="Are the retrieved chunks actually relevant?")
    context_recall: float = Field(ge=0, le=1,
        description="Did retrieval find all necessary information?")
    
    @property
    def overall_score(self) -> float:
        return (self.faithfulness + self.answer_relevance + 
                self.context_precision + self.context_recall) / 4

# Use RAGAS library for automated RAG evaluation
# pip install ragas
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

# Build evaluation dataset
eval_dataset = {
    "question": ["What is the vacation policy?"],
    "answer": ["Employees get 25 days annual leave."],
    "contexts": [["All employees are entitled to 25 days of paid annual leave per year."]],
    "ground_truth": ["25 days of paid annual leave per year"]
}

# results = evaluate(eval_dataset, metrics=[faithfulness, answer_relevancy])
```

---

## 🏗️ CAPSTONE PROJECT — Full Stack RAG + Agentic System

### "Company Intelligence Platform"

Build a production-grade system combining EVERYTHING:

```
Architecture:
─────────────
User Query
    │
    ▼
Intent Classifier Agent (Pydantic output)
    │
    ├──→ [If factual/doc query] → RAG Pipeline → FAISS Search → LLM Answer
    │         ↳ Hybrid Search (BM25 + Vector)
    │         ↳ Reranker Model
    │         ↳ Source Citations
    │
    ├──→ [If computation needed] → Tool Agent → Calculator / API calls
    │
    ├──→ [If complex research] → Multi-Agent Pipeline
    │         ↳ Researcher + Analyst + Writer
    │         ↳ Parallel async execution
    │
    └──→ [Final synthesis] → Summary Agent → Streaming Response

Tech Stack:
- Python (asyncio everywhere)
- Pydantic (all data models)
- LangChain (chains, LCEL, memory)
- FAISS or ChromaDB (vector store)
- Google Gemini (LLM + embeddings)
- FastAPI (to expose as REST API)
- LangGraph (agent orchestration)
```

---

## 🔑 QUICK REFERENCE: KEY COMMANDS & PATTERNS

```python
# LangChain LCEL Chaining
chain = prompt | llm | output_parser

# Async batch processing
results = await asyncio.gather(*[chain.ainvoke(x) for x in inputs])

# Pydantic + LangChain
parser = PydanticOutputParser(pydantic_object=MyModel)
chain = prompt | llm | parser

# RAG retrieval
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
docs = retriever.invoke(query)

# Streaming
async for chunk in llm.astream(prompt):
    print(chunk.content, end="", flush=True)

# Tool-calling agent
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Memory with summary
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=800)
```

---

*Built from your Coding Ninjas Sessions 6–10 curriculum, extended with production-grade engineering patterns.*
*Tech Stack: Python · Pydantic · LangChain · Gemini · FAISS · AsyncIO*
