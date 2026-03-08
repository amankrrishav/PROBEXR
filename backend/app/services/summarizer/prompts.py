"""
Summarizer Prompts: Advanced Chain-of-Density and Synthesis templates.
Adapted for high information density and professional tone.
"""
from typing import Any

# Separator for streaming-friendly parsing
JSON_SEP = "---JSON_START---"

def build_unified_prompt(
    text: str,
    target_words: int,
    preset: dict[str, Any],
    content_type: str = "general",
) -> list[dict[str, str]]:
    """
    Build a single-call prompt that returns summary + takeaways.
    Uses the "Chain of Density" approach for maximum information per word.
    """
    tone_guidance = preset.get("tone", "clear, natural prose")
    takeaway_count = preset.get("takeaway_count", 5)
    structure = preset.get("structure_guidance", "")

    system = f"""You are a Tier-1 Research Analyst at a premier technology firm (Google/Meta/Apple). 
Your objective is to perform a high-fidelity "Chain-of-Density" summarization that maximizes information density while maintaining clarity.

## Core Directives
1. **Summary Phase (Density-Iteration)**:
   - Target: {target_words} words. 
   - Strategy: Identify the "Hollow" core concepts first, then iteratively layer in Missing Entities, Quantitative Data, and Causal Mechanics.
   - Avoid all meta-discourse ("The article discusses", "In this text").
   - Every sentence must be a "Power Sentence": 80% information, 20% connective tissue.
   
2. **TL;DR Generation**: 
   - A single, punchy, "executive floor" sentence that captures the primary existential takeaway.

3. **Key Takeaways**: Exactly {takeaway_count} points.
   - Format: [Insight] -> [Actionable Impact].
   - No generic bullets; everything must be specific to the source.

4. **Intelligence Metadata**:
   - Accurately identify People, Organizations, and Technical Concepts.
   - Gauge Sentiment (Positive/Negative/Neutral) and the specific Professional Tone.

## Format Requirements
Summary Text Content
{JSON_SEP}
{{
  "tldr": "...",
  "key_takeaways": ["...", "..."],
  "entities": {{"people": [], "orgs": [], "concepts": []}},
  "sentiment": "Neutral",
  "professional_tone": "Technical",
  "complexity_score": 1-10
}}
"""
    user = f"Source Text:\n\n{text}"
    
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]

def build_reduce_prompt(
    chunk_summaries: list[str],
    target_words: int,
    preset: dict[str, Any],
) -> list[dict[str, str]]:
    """Prompt for the 'Reduce' phase of map-reduce synthesis."""
    combined = "\n\n---\n\n".join(chunk_summaries)
    
    system = f"""You are a Senior Content Strategist. You are performing a high-stakes synthesis of sectional intelligence reports.
Merge the provided sectional summaries into a single, seamless, high-density narrative of {target_words} words.

## Synthesis Mandates
1. **Narrative Continuity**: The output must not read like a list of summaries; it must be a single, fluid argumentative arc.
2. **De-duplication**: Aggressively prune overlapping entities and redundant causal explanations across sections.
3. **Hierarchical Importance**: Prioritize existential threats/opportunities and 1st-order facts over 2nd-order examples.
4. **Follow Output Protocol**: Summary content + {JSON_SEP} + unified JSON metadata.

JSON Schema:
{{
  "tldr": "Total executive summary sentence",
  "key_takeaways": ["consolidated tactical insights"],
  "entities": {{"unified_people": [], "unified_orgs": [], "unified_concepts": []}},
  "sentiment": "Overall Sentiment",
  "synthesis_integrity": 1-10
}}
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Section Summaries:\n\n{combined}"}
    ]
