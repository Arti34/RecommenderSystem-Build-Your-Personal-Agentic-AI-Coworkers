# Interactive Career Coaching Session — DEMO TRANSCRIPT

**Demo only:** This illustrates the new offline interactive coaching flow. It is not a record of a real learner's assessment or an actual employer interview. Keyword-rubric scores indicate recognized concepts, not overall answer correctness.

**Career target:** AI / ML Engineer  
**Topic:** RAG  
**Session length:** 3 questions

## Turn 1

**Coach:** Explain retrieval-augmented generation (RAG). Why is retrieval useful, and how would you check source citations?

**Student:** Retrieval searches.

**Coach feedback:** You mentioned *retrieval*. Try adding *grounding* and *citation verification*.

**Adaptive follow-up:** Let's focus on grounding, which was missing from your answer. Explain how retrieved documents become context for the language model, with an example.

## Turn 2

**Student:** Retrieved documents are passed as context to the model so it can answer a question using that information.

**Coach feedback:** You mentioned grounding. Next, explain how to verify a source citation.

**Adaptive follow-up:** Let's focus on citation verification. How would you check whether a generated claim is really supported by its cited passage?

## Turn 3

**Student:** Compare every claim with the original supporting passage and flag anything missing or contradictory.

**Coach feedback:** Good coverage of citation verification. Explain the full retrieval-to-answer pipeline and practice another question later.

## End of session

All three answers are saved in SQLite. The Career Readiness Report includes per-turn feedback and practice topics. This mock transcript illustrates the expected conversation structure; actual feedback depends on the learner's answers and whether local Ollama is enabled.
