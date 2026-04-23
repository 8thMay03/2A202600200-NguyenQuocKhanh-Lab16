# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot100.json
- Mode: mock
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.97 | 0.98 | 0.01 |
| Avg attempts | 1 | 1.05 | 0.05 |
| Avg token estimate | 419.51 | 473.4 | 53.89 |
| Avg latency (ms) | 1865.94 | 2146.12 | 280.18 |

## Failure modes
```json
{
  "react": {
    "none": 97,
    "wrong_final_answer": 3
  },
  "reflexion": {
    "none": 98,
    "wrong_final_answer": 2
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity. The tradeoff is higher attempts, token cost, and latency. In a real report, students should explain when the reflection memory was useful, which failure modes remained, and whether evaluator quality limited gains.
