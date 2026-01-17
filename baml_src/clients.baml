// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

// Environment-driven clients for CodeWriter4.0 BAML migration
// These clients use environment variables for configuration but have static providers

// Primary OpenAI client for LLM_PROVIDER=openai
client<llm> EnvironmentOpenAI {
  provider openai
  options {
    model env.LLM_MODEL
    api_key env.OPENAI_API_KEY
    temperature env.LLM_TEMPERATURE
    max_tokens env.MAX_TOKENS
  }
}

// Primary Anthropic client for LLM_PROVIDER=anthropic  
client<llm> EnvironmentAnthropic {
  provider anthropic
  options {
    model env.ANTHROPIC_MODEL
    api_key env.ANTHROPIC_API_KEY
    temperature env.ANTHROPIC_TEMPERATURE
    
  }
}

// SRC2 Ollama client for SRC2_LLM_PROVIDER=ollama
client<llm> EnvironmentOllama {
  provider "openai-generic"
  options {
    model gemma3:latest
    base_url "http://localhost:11434/v1"
    temperature 0.3
    max_tokens 32015
  }
}

// Hardcoded Ollama client for when API credits are exhausted
// Uses qwen2.5-coder:14b which is available locally
client<llm> OllamaQwen {
  provider "openai-generic"
  options {
    model "qwen2.5-coder:14b"
    base_url "http://localhost:11434/v1"
    temperature 0.5
    max_tokens 32015
  }
}

// Ollama-only fallback that doesn't require any API keys
client<llm> OllamaOnlyFallback {
  provider fallback
  options {
    strategy [OllamaQwen]
  }
}

client<llm> CustomGPT4o {
  provider openai
  options {
    model env.LLM_MODEL
    api_key env.OPENAI_API_KEY
    temperature env.LLM_TEMPERATURE
    max_tokens env.MAX_TOKENS
  }
}

client<llm> CustomGPT4oMini {
  provider openai
  retry_policy Exponential
  options {
    model "gpt-4o-mini"
    api_key env.OPENAI_API_KEY
    temperature env.LLM_TEMPERATURE
    max_tokens env.MAX_TOKENS
  }
}

client<llm> CustomSonnet {
  provider anthropic
  options {
    model "claude-sonnet-4-5-20250929"
    api_key env.ANTHROPIC_API_KEY
    temperature env.ANTHROPIC_TEMPERATURE
    max_tokens env.ANTHROPIC_MAX_TOKENS
  }
}


client<llm> CustomHaiku {
  provider anthropic
  retry_policy Constant
  options {
    model "claude-haiku-4-5-20251001"
    api_key env.ANTHROPIC_API_KEY
    temperature 0.3
    max_tokens 64000
    
  }
}

client<llm> OllamaClient {
  provider "openai-generic"
  options {
    model env.OLLAMA_MODEL
    base_url env.OLLAMA_HOST
    temperature env.OLLAMA_TEMPERATURE
    max_tokens env.OLLAMA_MAX_TOKENS
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/round-robin
client<llm> CustomFast {
  provider round-robin
  options {
    // This will alternate between the two clients
    strategy [CustomGPT4oMini, CustomHaiku]
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/fallback
client<llm> OpenaiFallback {
  provider fallback
  options {
    // This will try the clients in order until one succeeds
    strategy [CustomGPT4oMini, CustomGPT4oMini]
  }
}

// Haiku with Ollama fallback for requirement decomposition
// Tries Claude Haiku first (high accuracy), falls back to local Ollama if API fails
client<llm> HaikuWithOllamaFallback {
  provider fallback
  options {
    strategy [CustomHaiku, EnvironmentOllama]
  }
}

// Ollama with Haiku fallback for requirement decomposition
// Tries Claude Haiku first (high accuracy), falls back to local Ollama if API fails
client<llm> OllamaWithHaikuFallback {
  provider fallback
  options {
    strategy [EnvironmentOllama, CustomHaiku]
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/retry
retry_policy Constant {
  max_retries 3
  // Strategy is optional
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 2
  // Strategy is optional
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}

// =============================================================================
// OPUS AGENT SDK INTEGRATION (REQ_004.4)
// =============================================================================
// OpusAgent client for Agent SDK + BAML modular API integration
// Uses Claude Opus 4.5 for high-quality decomposition and validation

client<llm> OpusAgent {
  provider anthropic
  retry_policy Exponential
  options {
    model "claude-opus-4-5-20251101"
    api_key env.ANTHROPIC_API_KEY
    max_tokens 8192
    // Temperature configurable via env, default 0.3 for consistency
    temperature 0.3
  }
}

// Fallback configuration: OpusAgent -> CustomHaiku
// For resilience when Opus unavailable or for cost optimization
client<llm> OpusWithHaikuFallback {
  provider fallback
  options {
    strategy [OpusAgent, CustomHaiku]
  }
}

// OpusAgent with local Ollama fallback for offline scenarios
client<llm> OpusWithOllamaFallback {
  provider fallback
  options {
    strategy [OpusAgent, EnvironmentOllama]
  }
}