# AI Token Saving

**little lovely planet** - quality-preserving token & credit savings for AI
agents. Context is expensive; re-pasted files, verbose tool output, and
padded replies burn tokens on every message. This project cuts that waste
**without dropping a single fact the user needs**.

- **Model-agnostic** - behavioral rules work on any model.
- **Harness-agnostic** - universal system-prompt bundle + context filter;
  native skills for WorkBuddy and Hermes.
- **Pure stdlib Python 3.9+** - zero dependencies, zero telemetry, zero
  network calls.

## Quick start (any harness)

1. Paste the [system-prompt bundle](https://github.com/remembervictorchatbot-vip/AI_Token_Saving/blob/main/dist/system-prompt/token-savings-prompt.md)
   at the TOP of your system prompt.
2. Optional context filter - see [[DeepSeek-Harness-Adapter]].
3. Optional CLI: add `skills/token-savings/bin` to PATH, then `toks selftest`
   (197 tests, must pass).

## The four promises

1. Never re-paste what you already read (dedup)
2. Never send markup when meaning is enough (compress / normalize)
3. Never generate prose when data will do (output discipline)
4. Never lose the one fact that mattered (protected zones)

## Measured impact

**52.1% aggregate tool-level input savings** on representative samples
([[Benchmark]]). Honest scope: tool-level only; end-to-end savings also
depend on the model following the rules.

## Explore

- [[Installation]] - install per harness
- [[Architecture]] - how the discipline works
- [[CLI-Reference]] - command surface
- [[Skills]] - the four skills
- [[FAQ]] - common questions