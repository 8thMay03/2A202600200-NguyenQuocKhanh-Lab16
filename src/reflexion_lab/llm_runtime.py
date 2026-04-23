import os
import time
from typing import Tuple
from openai import OpenAI
from dotenv import load_dotenv

from .schemas import QAExample, JudgeResult, ReflectionEntry
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM

load_dotenv()

# Initialize OpenAI client 
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
GPT_MODEL = "gpt-4o-mini" # Fast and cost-effective model

def _get_context_str(context: list) -> str:
    return "\n\n".join([f"Title: {c.title}\n{c.text}" for c in context])

def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> Tuple[str, int, int]:
    start_time = time.time()
    
    user_prompt = f"Context:\n{_get_context_str(example.context)}\n\nQuestion: {example.question}\n"
    
    if reflection_memory and agent_type == "reflexion":
        user_prompt += "\nPast Mistakes (Reflections):\n"
        for i, ref in enumerate(reflection_memory):
            user_prompt += f"- Attempt {i+1}: {ref}\n"
            
    user_prompt += "\nPlease provide a concise final answer."

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": ACTOR_SYSTEM},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        answer = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens
    except Exception as e:
        answer = str(e)
        tokens = 0
        
    latency_ms = int((time.time() - start_time) * 1000)
    return answer, tokens, latency_ms

def evaluator(example: QAExample, answer: str) -> Tuple[JudgeResult, int, int]:
    start_time = time.time()
    
    user_prompt = f"Question: {example.question}\nGold Answer: {example.gold_answer}\nAgent's Answer: {answer}\nPlease evaluate."

    try:
        # Sử dụng structured output parser (Beta) của OpenAI cho Pydantic Models 
        response = client.beta.chat.completions.parse(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": EVALUATOR_SYSTEM},
                {"role": "user", "content": user_prompt}
            ],
            response_format=JudgeResult,
            temperature=0.0
        )
        judge = response.choices[0].message.parsed
        tokens = response.usage.total_tokens
    except Exception as e:
        judge = JudgeResult(score=0, reason=f"Evaluation Error: {str(e)}")
        tokens = 0
        
    latency_ms = int((time.time() - start_time) * 1000)
    return judge, tokens, latency_ms

def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> Tuple[ReflectionEntry, int, int]:
    start_time = time.time()
    
    user_prompt = (
        f"Question: {example.question}\n"
        f"Evaluator Score: {judge.score}\n"
        f"Evaluator Reason: {judge.reason}\n"
        f"Missing Evidence: {judge.missing_evidence}\n"
        f"Spurious Claims: {judge.spurious_claims}\n\n"
        f"Please reflect on this failure and provide the next strategy."
    )

    try:
        response = client.beta.chat.completions.parse(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": REFLECTOR_SYSTEM},
                {"role": "user", "content": user_prompt}
            ],
            response_format=ReflectionEntry,
            temperature=0.3
        )
        reflection = response.choices[0].message.parsed
        reflection.attempt_id = attempt_id
        tokens = response.usage.total_tokens
    except Exception as e:
        reflection = ReflectionEntry(attempt_id=attempt_id, failure_reason=str(e), lesson="Error calling LLM", next_strategy="Try again.")
        tokens = 0
        
    latency_ms = int((time.time() - start_time) * 1000)
    return reflection, tokens, latency_ms
