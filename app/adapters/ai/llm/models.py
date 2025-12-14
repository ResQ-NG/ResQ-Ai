from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# High-performance but expensive
gpt_4_turbo = ChatOpenAI(model="gpt-4-turbo", temperature=0.2)

# Cheaper, smaller model
gpt_4o_mini = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# External models
claude = ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.3)
gemini = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)

pricing = {
    "gpt-4-turbo": 0.01,
    "gpt-4o-mini": 0.002,
    "claude-3-sonnet-20240229": 0.008,
    "gemini-1.5-flash": 0.0015,
}


models = {
    "fast": gpt_4o_mini,
    "balanced": claude,
    "accurate": gpt_4_turbo,
    "cheap": gemini,
}



OLLAMA_LLAVA = "llava"
