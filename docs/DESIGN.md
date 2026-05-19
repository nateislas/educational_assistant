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
- **`factuality_and_groundedness`**: Factual accuracy, no scientific or historical hallucinations, aligns with real-world facts.
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

### Initial Result with Original Prompt (`gemini-baseline-65ec9bae`)

Here are the results:
- **Clarity & Structure**: 3.20 / 5.0
- **Tone & Grade-Level Appropriateness**: 4.20 / 5.0
- **Factuality & Groundedness**: 4.60 / 5.0
- **Actionability & Completeness**: 2.30 / 5.0
- **Instruction Following**: 2.80 / 5.0

The output was a single paragraph with no headers, and had hallucinations (claiming Yuri Gagarin and Valentina Tereshkova flew to the ISS):
> "Students will learn about the International Space Station's (ISS) origins as a collaborative project, key construction milestones (e.g., Zarya module launch in 1998, first crew arrival in 2000), and its continuous human presence. They will identify significant astronauts and their contributions (e.g., Yuri Gagarin's pioneering flight, Valentina Tereshkova as the first woman in space, Chris Hadfield's popularization of space life). Students will also understand major events like the Space Shuttle program's role in construction and resupply, the challenges faced (e.g., Columbia disaster), and the scientific research conducted aboard the ISS, covering topics from microgravity effects on the human body to advanced materials science and Earth observation."

#### Key Observations
- Good tone: matches the specified grade level.
- Low actionability: reads like a textbook summary instead of concrete details for AR/VR interactions.
- Instruction following issues: struggled with vague or off-domain prompts.


## Enhancements

- enhance the prompt, provide additional detail, maybe an example or two
- Integrate a search tool to ground the models
- use thinking tokens
- Use mult-tiered structured output so that we can try to get consistent results


### Improving system prompt ONLY

The old prompt asked for a "concise summary" which made unstructured paragraphs. The new prompt forces a strict, nested bullet-point structure to keep formatting consistent. It also adds guidelines for grade-level adaptation and off-domain cases.

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

### Iteration 1: Upgraded System Prompt (`gemini-baseline-560b3c52`)
Forces a strict nested bullet-point structure.
- **Clarity & Structure:** 3.20 ➔ 4.90
- **Factuality:** 4.60 ➔ 5.00
- **Actionability:** 2.30 ➔ 3.80
- **Instruction Following:** 2.80 ➔ 4.10

#### Actual Output (Iteration 1):
The structure matches nested bullets, but content is vague and doesn't name any specific details (like astronauts or dates).
```markdown
Key Learnings:

*   **Understand the timeline of the ISS's construction and operation.**
    *   Recognize the initial launch date of the first module (Zarya) in 1998.
    *   Identify key milestones like the first long-duration crew arrival and the completion of major assembly.
    *   Appreciate the continuous human presence in space since November 2000.

*   **Learn about the international collaboration involved in the ISS.**
    *   Identify the primary partner space agencies (NASA, Roscosmos, JAXA, ESA, CSA).
    *   Understand how different countries contributed modules, hardware, and expertise.
    *   Recognize the ISS as a symbol of peaceful cooperation in space exploration.

*   **Explore the scientific research conducted on the ISS.**
    *   Understand how the microgravity environment enables unique experiments.
    *   Identify research areas such as human physiology, materials science, and Earth observation.
    *   Appreciate the benefits of ISS research for life on Earth and future space missions.

*   **Recognize significant events and achievements during the ISS's history.**
    *   Recall the first spacewalks conducted by astronauts from different partner nations.
    *   Learn about the challenges faced and overcome, such as repairs and emergencies.
    *   Identify notable visitors and events, like space tourist missions or major scientific discoveries.

*   **Identify famous astronauts and their contributions to the ISS program.**
    *   Learn about the first resident crews and their pioneering work.
    *   Recognize astronauts who have set records for time in space or conducted significant spacewalks.
    *   Understand the diverse backgrounds and roles of the international crews living and working on the station.
```

**Takeaway:** Formatting improved but model still outputs generic objectives instead of concrete details.

### Iteration 2: Enabling Reasoning (`gemini-baseline-ef9d4c3f`)
Added a 1024 token thinking budget so the model can plan before writing.
- **Actionability:** 3.80 ➔ 4.40
- **Instruction Following:** 4.10 ➔ 4.40

**Takeaway:** Model uses the scratchpad to plan details, but still lacks specific names or dates.

### Iteration 2 (Calibrated): Fixing LLM Judge Positivity Bias
This is not a new agent. It's the same Iteration 2 run re-evaluated with a calibrated judge. The LLM judge had positivity bias, scoring outputs high even when they missed specific dates or names. Added negative constraints in `eval.py` to cap scores at a maximum of 2 if the output uses vague placeholders instead of concrete facts.

**Calibrated Results (`gemini-baseline-afd8999f`):**
- **Actionability:** 4.40 ➔ 2.70
- **Instruction Following:** 4.40 ➔ 2.90

#### Actual Agent Output (Iteration 2 - Ungrounded):
Structured well but has placeholders instead of specific details:
```markdown
Key Learnings:
Understand the purpose and global collaboration behind the International Space Station (ISS).
* Learn that the ISS is a unique research laboratory orbiting Earth.
* Identify the major countries and space agencies that partnered to build and operate the ISS, including the USA, Russia, Europe, Japan, and Canada.
* Recognize the ISS as a symbol of international cooperation and peaceful scientific endeavor.

Explore the timeline of the ISS's construction and assembly.
* Identify the launch date of the first ISS module, Zarya, in 1998.
* Learn about the gradual assembly process, with modules and components launched and connected over many years.
* Understand that the ISS became continuously inhabited by astronauts starting in November 2000.

Recognize key milestones and significant events in ISS history.
* Learn about the first long-duration spaceflights and the astronauts who pioneered living and working in space for extended periods.
* Discover major scientific experiments conducted on the ISS, ranging from studying human health in microgravity to observing Earth and the universe.
* Understand the importance of spacewalks (Extravehicular Activities or EVAs) for assembling, repairing, and upgrading the station.

Identify famous astronauts and their contributions to the ISS.
* Learn about astronauts from diverse backgrounds and nationalities who have visited or lived on the ISS.
* Recognize that hundreds of astronauts from over 15 countries have served aboard the station.
* Understand how astronauts conduct experiments, perform maintenance, and contribute to the station's ongoing mission.
```

**Takeaway:** The lower scores show the evaluator is now calibrated. Formatting and tone are good, but the agent needs grounding to produce concrete facts.


## Iteration 3: Integrating Exa Search
Added a search tool using `langchain-exa`. We refined the agent prompt to enforce Exa's declarative/link-continuation strategy:
1. Write queries as natural sentences leading to the answer.
2. Search for raw facts (no 'for kids' filters) and handle simplification in the generation step.
3. Limit to 1-2 searches to save latency.

**Results (`gemini-baseline-b0f753a0`):**
- **Clarity & Structure:** 4.60
- **Tone & Appropriateness:** 4.80
- **Factuality & Groundedness:** 4.80
- **Actionability & Completeness:** 2.70 ➔ 3.30
- **Instruction Following:** 2.90 ➔ 3.50

#### Actual Agent Output 1 (ISS Query - Truncated):
Agent found the right details but the output got cut off mid-sentence:
```markdown
Key Learnings:

**Understand the Vision and Origins of the ISS**
*   Recognize that the idea for a space station dates back centuries, with early concepts by scientists like Konstantin Tsiolkovsky and Wernher von Braun.
*   Learn that the ISS began as separate U.S. (Space Station Freedom) and Soviet (Mir-2) projects in the 1980s, but merged in 1993 due to budget challenges and a desire for international cooperation.
*   Appreciate that President Reagan
```
*This prompted us to use a Pydantic schema and adjust max token settings in Iteration 4.*

#### Actual Agent Output 2 (Wright Flyer Query - Completed Grounded Run):
Exa retrieved accurate physical and historical specs:
```markdown
Key Learnings:

*   **Understand** the historical context and significance of the Wright Brothers' first flight.
    *   Identify the date and location of the first successful powered flight: December 17th, 1903, at Kitty Hawk, North Carolina.
    *   Recognize Wilbur and Orville Wright as aviation pioneers who achieved powered flight.
    *   Appreciate how this event marked the beginning of the aviation age and changed transportation.

*   **Learn** about the design and engineering of the Wright Flyer.
    *   Identify key components like the biplane wings (40 ft, 4 in wingspan), engine, and propellers.
    *   Understand the materials used, such as spruce, ash, muslin, and aluminum for the engine.
    *   Explore innovative features like the canard design (stabilizers at the front) and the propeller system.

*   **Explore** the challenges faced by the Wright Brothers.
    *   Recognize the difficulty in finding or creating a lightweight, powerful engine (12 hp).
    *   Understand how they designed propellers to act like rotary wings for thrust.
    *   Learn about their iterative process of building and testing gliders before the powered flight.

*   **Experience** the mechanics of early flight through simulation.
    *   Practice controlling the aircraft using the hip cradle and levers for pitch and roll.
    *   Understand basic flight principles like lift and thrust as applied to the Wright Flyer.
    *   Compare the flight characteristics of the Wright Flyer to modern aircraft.

*   **Identify** the key specifications and performance of the Wright Flyer.
    *   Recall the aircraft's length (21 ft, 1 in) and empty weight (605 lbs).
    *   Understand the performance of the first flight: 12 seconds duration, 120 feet distance, 8 feet altitude.
    *   Recognize the estimated maximum speed of around 30 mph.
```

**Takeaway:** Declarative queries worked well. Fact density is much better.

## Iteration 4: Golden Queries & Generalized Evaluator
Changes made:
1. Refactored `eval.py` to support general educational topics.
2. Curated `golden_queries.json` with 6 detailed topics and reference outputs.

### Creating the Golden Dataset
To create `golden_queries.json`, we generated a synthetic dataset:
1. Fed the system prompt into Gemini 3.1 Pro to generate 6 queries across different educational topics and grade levels.
2. Had the model generate target structured outputs according to the prompt constraints.
3. Used Gemini 3.1 Pro to review and edit the facts, dates, and names in the outputs to ensure accuracy.

Using a frontier model to bootstrap synthetic data is common for cold-starting. For production, it would be better to source queries from actual users, have educators write the expected outputs, and include negative test cases for off-domain inputs.

**Results (`gemini-baseline-dfa058d7`):**
- **Factuality & Groundedness:** `5.00` / 5.00
- **Clarity & Structure:** `5.00` / 5.00
- **Tone & Grade Appropriateness:** `5.00` / 5.00
- **Actionability & Completeness:** `2.70` ➔ `3.83`
- **Instruction Following:** `2.90` ➔ `4.00`

**Takeaway:** The search agent gets good scores on structure, tone, and factuality. The system is consistent and factually accurate.

#### Actual Agent Output (Iteration 4 - Grounded with Exa Search):
Agent uses Exa search to get real facts (names, dates, agencies, modules):
```markdown
Key Learnings:

*   **Understand the origins and vision of the ISS.**
    *   Explore early ideas for space stations from visionaries like Tsiolkovsky and von Braun.
    *   Learn how NASA began designing a space station in the 1980s, initially called "Freedom."
    *   Recognize President Reagan's 1984 call for an international partnership to build a permanent space outpost.

*   **Identify the key international partners and their contributions.**
    *   Discover the main space agencies involved: NASA (USA), Roscosmos (Russia), ESA (Europe), JAXA (Japan), and CSA (Canada).
    *   Understand how the ISS evolved from "Freedom" to the "International Space Station" when Russia joined in the 1990s.
    *   Appreciate how countries work together, sharing costs and expertise to build and operate the station.

*   **Learn the timeline of the ISS assembly and continuous habitation.**
    *   Trace the launch of the first modules, starting with Russia's Zarya in November 1998 and the US Unity module shortly after.
    *   Understand the significance of November 2, 2000, marking the arrival of the first resident crew (Expedition 1).
    *   Recognize that the ISS has been continuously inhabited by humans ever since, making it a unique orbiting laboratory.

*   **Recognize the roles and experiences of astronauts and cosmonauts.**
    *   Identify the first crew members, Expedition 1 Commander William M. "Shep" Shepherd, Yuri P. Gidzenko, and Sergei K. Krikalev.
    *   Understand that astronauts and cosmonauts from many nations live and work together on the station.
    *   Learn about the importance of spacewalks for assembly, maintenance, and repairs.

*   **Explore the purpose and achievements of the ISS.**
    *   Discover that the ISS serves as a unique laboratory for scientific research in microgravity, benefiting life on Earth.
    *   Recognize the ISS as a symbol of international cooperation and a stepping stone for future space exploration.
    *   Appreciate that over 280 astronauts and cosmonauts from around the world have visited the station.
```


