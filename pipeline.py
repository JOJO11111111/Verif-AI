"""VerifAI three-stage fact-checking pipeline.

Stage 1: Claude decomposes the claim into sub-assertions
Stage 2: GPT-4o-mini + Tavily gathers evidence for each sub-claim
Stage 3: Claude synthesizes a final verdict with sources and reasoning
"""

import os
import re
import json
from anthropic import Anthropic
from openai import OpenAI
from tavily import TavilyClient

from prompts import DECOMPOSITION_PROMPT, SYNTHESIS_PROMPT

# Initialize clients (API keys read from environment)
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

CLAUDE_MODEL = "claude-sonnet-4-5"  # reasoning-optimized
GPT_MODEL = "gpt-4o-mini"             # speed/cost-optimized for retrieval

DEFAULT_MAX_SUB_CLAIMS = 3

_LIST_PREFIX_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s*")


def decompose_claim(claim: str, max_sub_claims: int = DEFAULT_MAX_SUB_CLAIMS) -> list[str]:
    """Stage 1: Use Claude to break the claim into atomic sub-assertions."""
    response = anthropic_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": DECOMPOSITION_PROMPT.format(
                    claim=claim, max_sub_claims=max_sub_claims
                ),
            }
        ],
    )
    text = response.content[0].text.strip()

    sub_claims = []
    for line in text.split("\n"):
        line = _LIST_PREFIX_RE.sub("", line).strip()
        if line:
            sub_claims.append(line)
    return sub_claims[:max_sub_claims]


def _tavily_search(query: str, max_results: int = 5) -> list[dict]:
    """Call Tavily and return clean result dicts."""
    try:
        results = tavily_client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        )
        return results.get("results", [])
    except Exception as e:
        return [{"error": str(e)}]


def gather_evidence(sub_claims: list[str]) -> list[dict]:
    """Stage 2: Use GPT-4o-mini as a tool-calling agent with Tavily search.

    For each sub-claim, GPT decides what to search and Tavily returns evidence.
    Returns a list of {sub_claim, search_query, evidence} dicts.
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "tavily_search",
                "description": "Search the web for evidence to verify a financial or factual claim. Use authoritative sources like SEC.gov, FINRA.org, official company registries, and reputable financial news.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Targeted search query (be specific - include entity names, dates, regulator names)",
                        }
                    },
                    "required": ["query"],
                },
            },
        }
    ]

    all_evidence = []

    for sub_claim in sub_claims:
        messages = [
            {
                "role": "system",
                "content": "You are a fact-checking research agent. Use the tavily_search tool to find authoritative evidence for or against the given sub-claim. Run 1-2 targeted searches, then summarize what you found with source URLs.",
            },
            {
                "role": "user",
                "content": f"Research this sub-claim and report your findings with sources:\n\n{sub_claim}",
            },
        ]

        # Tool-calling loop (max 3 iterations to avoid runaway calls)
        for _ in range(3):
            response = openai_client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            msg = response.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                # Agent finished with a final text answer
                break

            for tool_call in msg.tool_calls:
                if tool_call.function.name == "tavily_search":
                    args = json.loads(tool_call.function.arguments)
                    search_results = _tavily_search(args["query"])
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(search_results)[:4000],
                        }
                    )

        final_text = messages[-1].get("content", "") if isinstance(messages[-1], dict) else ""
        all_evidence.append(
            {
                "sub_claim": sub_claim,
                "evidence": final_text,
            }
        )

    return all_evidence


def synthesize_verdict(claim: str, evidence: list[dict]) -> str:
    """Stage 3: Use Claude to weigh evidence and produce the final verdict."""
    evidence_text = "\n\n".join(
        f"SUB-CLAIM: {item['sub_claim']}\nEVIDENCE:\n{item['evidence']}"
        for item in evidence
    )

    response = anthropic_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": SYNTHESIS_PROMPT.format(claim=claim, evidence=evidence_text),
            }
        ],
    )
    return response.content[0].text


def run_pipeline(claim: str, progress_callback=None, max_sub_claims: int = DEFAULT_MAX_SUB_CLAIMS):
    """Run the full three-stage pipeline. Optionally report progress via callback."""
    if progress_callback:
        progress_callback("decompose", "Decomposing claim into sub-assertions...")
    sub_claims = decompose_claim(claim, max_sub_claims=max_sub_claims)

    if progress_callback:
        progress_callback("evidence", f"Gathering evidence for {len(sub_claims)} sub-claims...")
    evidence = gather_evidence(sub_claims)

    if progress_callback:
        progress_callback("synthesize", "Synthesizing final verdict...")
    verdict = synthesize_verdict(claim, evidence)

    return {
        "sub_claims": sub_claims,
        "evidence": evidence,
        "verdict": verdict,
    }