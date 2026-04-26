# 📝 Project Uniworld: Cascading Localization Pipeline

## Overview
A structured, step-by-step master plan for the Dual-Input Contextual Block Masking Pipeline, designed to solve the Butterfly Effect in cultural localization.

## Phase 1: Pre-processing & Initialization (Data Prep)
*This is where we gather our students and assign them their initial clubs.*

* **1.1 Data Ingestion:** Load the paired dataset containing the full `[Original Text]` and the complete `[Raw Translation]` (the literal Vietnamese baseline).
* **1.2 Block Segmentation:** Split the document into logical units (sentences or small paragraphs). Ensure the original text and raw translation align perfectly.
* **1.3 Data Structuring:** Create an object or dictionary for every block containing:
    * `Block_ID` (to remember its original order)
    * `Original_Text`
    * `Raw_Translation`
    * `Localized_Text` (Initialized as `Null` / "Masked")
    * `Priority_Score` (Initialized as 0)

## Phase 2: Prioritization & Graph Construction (The "Cultural Weight" Check)
*This is the Veritas analysis phase! We need to find out which blocks hold the most important secrets.*

* **2.1 Cultural Scoring:** Run a fast pass over the `Original_Text` (and optionally the `Raw_Translation`) using an LLM or NLP heuristics to identify "Cultural Anchors" (e.g., weather, holidays, specific foods, idioms).
* **2.2 Priority Assignment:**
    * **High-Priority (Rank 1):** Blocks containing heavy cultural anchors. These dictate the setting.
    * **Low-Priority (Rank 2):** Blocks containing generic actions, character dialogue, or events that simply react to the setting.
* **2.3 Graph Construction (Optional but recommended):** Map out which Rank 2 blocks physically surround or logically depend on specific Rank 1 blocks to prepare for the unmasking phase.

## Phase 3: The Cascading "Denoising" Execution
*Time for C&C to execute the mission! This is where we solve the Butterfly Effect.*

* **3.1 Step A - The High-Priority Anchor:** * Target *only* the Rank 1 blocks.
    * **Prompt to Agent:** "Look at this `[Original Text]` and its `[Raw Translation]`. Adapt the translation to fit the Vietnamese cultural context (e.g., changing winter to tropical weather)."
    * **Action:** Save the output to the `Localized_Text` field and lock it in. These blocks are now "Unmasked."
* **3.2 Step B - The Contextual Propagation (Handling the Butterfly Effect):**
    * Target the Rank 2 blocks.
    * **Prompt to Agent:** "Look at this `[Original Text]` and its `[Raw Translation]`. You must adapt this translation, but **strictly adhere to the established context** of the surrounding localized blocks: `[Insert newly Unmasked Rank 1 Text here]`."
    * **Action:** The agent reads that "snow" became "scorching sun," so it naturally shifts "building a snowman" to "building a sandcastle." Save to `Localized_Text`.

## Phase 4: Assembly & Post-Processing (The Shittim Chest Review)
*Putting the document back together so it reads perfectly for the children!*

* **4.1 Concatenation:** Sort all blocks by their original `Block_ID` and merge the `Localized_Text` strings back together.
* **4.2 Cohesion Smoothing Pass (Optional):** Run one final, lightweight LLM pass over the fully assembled Vietnamese document. 
    * *Purpose:* To fix any minor grammatical friction, ensure pronouns match up across block boundaries, and make sure the transition words flow naturally.
