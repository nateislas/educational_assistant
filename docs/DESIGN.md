# Design document

## Background/Assignment

The current prompt is producing inconsistent results (varying quality, structure, and
usefulness).

**"You are an educational AI. Given a description of an educational VR/AR/MR
experience, generate a concise summary of the key learnings a student should
walk away with."**

Fairly simple right now, need to make it more robust. Will also probably used structured outputs (ie pydantic), maybe use a reasoning model, or have multiple steps to finding information. Will also probably use the Exa Search to help find additional information. This will help the outputs be more factual and informative/reduce halluciations. 


**Goal: Outputs need to be "Consistent, High quality, Useful for downstream use in a product"**

High quality is somewhat ambiguous, will need to break this down to accurate, tone, grade-appropriate language. Need to reach out to Matt about possible user demographic (eg grade-level, etc). 

**free to change, modify or extend the system prompt or system however you think is
appropriate.**

### Example User Query and Output

“Teach about the history of the International Space Station including important dates,
famous astronauts, and interesting events.”

“Key Learnings:
Understand the origins of the International Space Station (ISS) and why multiple
countries collaborated to build it.
Learn key milestones in ISS history, including:

- 1998: Launch of the first ISS module, Zarya
- 2000: Arrival of the first long-duration crew aboard Expedition 1
- 2011: Completion of the Space Shuttle program after helping assemble the ISS

Recognize the roles of major space agencies including NASA, Roscosmos, ESA, JAXA,
and CSA.

Identify famous astronauts associated with the ISS, such as:

- Chris Hadfield
- Peggy Whitson
- Scott Kelly
- Yuri Gidzenko
Explore important events and achievements aboard the ISS, including:
- Spacewalks and on-orbit repairs
- Scientific experiments conducted in microgravity
- Record-breaking missions and long-duration stays in space
- Cargo resupply and international cooperation efforts
Understand how the ISS has contributed to advancements in science, medicine, and
preparation for future missions to the Moon and Mars.”

**Essentially, this is creating a learning plan for students** 



Questions so far:
- Target audience for the learning plans
- Latency/quick responses


I'm planning on using a higher tier model (probably gemini 3.1 flash lite) as the LLM judge.


## Evals

Before making any improvements to the prompt, I created an eval pipeline. I think this gives us a good starting point to measure LLM response quality.

### Criteria/Rubric

We are going to judge the LLM responses on a 1-5 scale (where 1 is poor and 5 is excellent) across these five dimensions:
- **`clarity_and_structure`**: Logical organization, distinct sections, clear step-by-step progression of concepts.
- **`tone_and_grade_appropriateness`**: Engaging, educational, and K-12 student-friendly tone.
- **`factuality_and_groundedness`**: Factual accuracy, no scientific or historical hallucinations, aligns with real-world aerospace principles.
- **`actionability_and_completeness`**: Covers core concepts thoroughly, provides concrete details that can be visualized or interacted with in a training module.
- **`instruction_following`**: Adherence to all constraints, topics, and requirements specified in the user prompt.

### Test Queries

I tested the initial prompt on these queries:
1. "Teach about the history of the International Space Station including important dates, famous astronauts, and interesting events." (Exact query from assignment)
2. "Create an interactive solar system tour for 3rd graders focusing on Mars."
3. "Create a flight simulator experience for 7th graders teaching the Wright Brothers' first successful flight."
4. "Explain the James Webb Space Telescope (JWST) for 11th graders."
5. "Explain photosynthesis for 5th graders."
6. "A tour of the ancient Roman Colosseum for 6th graders."
7. "Explain how volcanoes erupt for 4th graders."
8. "Introduction to fractions for 2nd graders."
9. "The water cycle" (Vague, no grade specified)
10. "Shakespeare" (Extremely vague, off-domain edge case)

### Initial Result with Original Prompt

Here are the results:
- **Clarity & Structure**: 3.20 / 5.0
- **Tone & Grade-Level Appropriateness**: 4.20 / 5.0
- **Factuality & Groundedness**: 4.60 / 5.0
- **Actionability & Completeness**: 2.30 / 5.0
- **Instruction Following**: 2.80 / 5.0

#### Key Observations
- **Highly Accurate, Good Tone**: The model is accurate (4.6) and matches the grade level naturally when one is specified (4.2). 
- **Lacks Actionability**: The model scores very low on actionability and completeness (2.3) because it reads like a textbook summary rather than a plan that provides concrete, buildable details that an AR/VR developer can visualize or turn into interactions.
- **Instruction Following Gaps**: The model scores low on instruction following (2.8) because it struggles to strictly adhere to all constraints, especially on vague or off-domain prompts where it outputs general summaries instead of structured learning experiences.


## Enhancements

- enhance the prompt, provide additional detail, maybe an example or two
- Integrate a search tool to ground the models
- Use mult-tiered structured output so that we can try to get consistent results


### Improving system prompt ONLY


The old prompt only asked for a "concise summary" which resulted in unstructured paragraphs, but the new prompt forces a strict, nested bullet-point structure to guarantee consistent formatting. It also adds clear guidelines for grade-level adaptation and off-domain fallbacks, making sure the model handles any user query without breaking.

"Role:
"You are an expert curriculum designer. You create structured learning plans 
for immersive AR/VR/MR educational experiences for K-12 students."

Task:
"Given a topic or description of an educational experience, generate a 
detailed set of Key Learnings the student should walk away with."

Format rules:
- Always begin with the header "Key Learnings:"
- List 4 to 7 top-level learning objectives. Each should begin with an action 
  verb (Understand, Learn, Identify, Recognize, Explore, Appreciate).
- Under each objective, add 2 to 4 nested bullet points that provide concrete 
  supporting detail.
- Do not write paragraphs or flowing prose.
- Adjust vocabulary and complexity to the target grade level. If no grade 
  level is specified, target a 6th to 8th grade audience.

Quality requirements:
- All facts, figures, and explanations must be accurate. Never fabricate specifics.
- Apply this structure to any topic, not just science or aerospace."

### Results for Iteration 1 (System Prompt Only)

Here are the results of our second run (gemini-baseline-560b3c52) compared to the initial baseline:
- **Clarity & Structure**: 4.90 / 5.0 (**+1.70**)
- **Tone & Grade-Level Appropriateness**: 4.70 / 5.0 (**+0.50**)
- **Factuality & Groundedness**: 5.00 / 5.0 (**+0.40**)
- **Actionability & Completeness**: 3.80 / 5.0 (**+1.50**)
- **Instruction Following**: 4.10 / 5.0 (**+1.30**)

#### Key Observations
1. **Dramatic Improvements**: Forcing the strict bullet-point structure and nested requirements immediately resolved our structure issue, raising Clarity from a mediocre 3.20 to a near-perfect **4.90**.
2. **Factuality Gains**: The quality instruction reminding the model to ground everything securely and never fabricate details yielded a perfect **5.00** for factuality.
3. **Actionability and Instruction Following (Remaining Gaps)**:
   - While Actionability jumped to **3.80**, the judge noted that the model is still listing *high-level objectives* (e.g. "Explore the surface of Mars") rather than describing the *interactive elements, scenarios, or tour steps* needed by AR/VR developers.
   - For instruction following (**4.10**), the judge pointed out that the model occasionally defaults to placeholders (e.g. "Identify famous astronauts") instead of listing the *actual names* (Chris Hadfield, Peggy Whitson) requested by the user prompt.

