# Take-Home Assignment: Improving AI Output Quality

## 1. Problems with the Original Prompt

The original prompt is a single sentence:

> *"You are an educational AI. Given a description of an educational VR/AR/MR experience, generate a concise summary of the key learnings a student should walk away with."*

Before touching anything, I built an eval pipeline and ran it against 10 test queries. I wanted a baseline to measure every subsequent change against.

The rubric grades responses 1-5 across five dimensions. Each maps to one of the three stated requirements (consistent, high quality, useful for downstream use):

- **Clarity and structure**: is the output consistent enough to be renderable downstream?
- **Tone and grade appropriateness** and **factuality and groundedness**: I split these because they're separate failure modes. You can write something accurate but way above a 3rd grader's level, or perfectly grade-appropriate but hallucinated. Both are quality issues but you need to track them separately.
- **Actionability and completeness**: is the output actually useful for building a product? "Famous astronauts" can't become a 3D label. "William Shepherd, Commander of Expedition 1, November 2000" can.
- **Instruction following**: if the model ignores what the user asked, none of the other scores matter.

Baseline results (`gemini-baseline-65ec9bae`):

| Metric | Score |
|---|:---:|
| Clarity & Structure | 3.20 |
| Tone & Grade Appropriateness | 4.20 |
| Factuality & Groundedness | 4.60 |
| Actionability & Completeness | 2.30 |
| Instruction Following | 2.80 |

First, the format was completely inconsistent. "Concise summary" gives the model no direction, so it just outputs a single paragraph every time with no structure or hierarchy.

Second, the content was too vague. The prompt never asks for specifics, so the model defaults to placeholders like "famous astronauts" and "key milestones".

The model also hallucinated. On the ISS query, it associated Yuri Gagarin and Valentina Tereshkova with the history of the ISS. Gagarin died in 1968 (decades before the first module launched in 1998) and Tereshkova's only spaceflight was in 1963 on Vostok 6. Neither has any connection to the ISS. 

Actual baseline output on the ISS query:

> *"Students will learn about the International Space Station's (ISS) origins as a collaborative project, key construction milestones (e.g., Zarya module launch in 1998, first crew arrival in 2000), and its continuous human presence. They will identify significant astronauts and their contributions (e.g., Yuri Gagarin's pioneering flight, Valentina Tereshkova as the first woman in space, Chris Hadfield's popularization of space life). Students will also understand major events like the Space Shuttle program's role in construction and resupply, the challenges faced (e.g., Columbia disaster), and the scientific research conducted aboard the ISS, covering topics from microgravity effects on the human body to advanced materials science and Earth observation."*

---

## 2. Iteration 1: Rewriting the System Prompt

The first thing I changed was the prompt before adding any tooling.

**Original prompt:**

> *"You are an educational AI. Given a description of an educational VR/AR/MR experience, generate a concise summary of the key learnings a student should walk away with."*

**Iteration 1 prompt:**

> *"You are an expert curriculum designer. You create structured learning plans for immersive AR/VR/MR educational experiences for K-12 students.*
>
> *Given a topic or description of an educational experience, generate a detailed set of Key Learnings the student should walk away with.*
>
> *Format rules:*
> *- Always begin with the header "Key Learnings:"*
> *- List 4 to 7 top-level learning objectives. Each should begin with an action verb (Understand, Learn, Identify, Recognize, Explore, Appreciate).*
> *- Under each objective, add 2 to 4 nested bullet points that provide concrete supporting detail.*
> *- Do not write paragraphs or flowing prose.*
> *- Adjust vocabulary and complexity to the target grade level. If no grade level is specified, target a 6th to 8th grade audience.*
>
> *Quality requirements:*
> *- All facts, figures, and explanations must be accurate. Never fabricate specifics.*
> *- Apply this structure to any topic, not just science or aerospace."*

Key changes: the role shifted from "educational AI" to "expert curriculum designer" to frame the model's output mode. "Concise summary" was replaced with an explicit format contract. A default grade level was added for vague prompts. And a quality rule was added requiring accuracy.

Results (`gemini-baseline-560b3c52`):

| Metric | Before | After |
|---|:---:|:---:|
| Clarity & Structure | 3.20 | **4.90** |
| Factuality & Groundedness | 4.60 | **5.00** |
| Actionability & Completeness | 2.30 | 3.80 |
| Instruction Following | 2.80 | 4.10 |

The structure improved significantly, but the content remained generic. Here is the ISS output after this change:

> *Understand the timeline of the ISS's construction and operation.*
> - *Recognize the initial launch date of the first module (Zarya) in 1998.*
> - *Identify key milestones like the first long-duration crew arrival and the completion of major assembly.*
>
> *Identify famous astronauts and their contributions to the ISS program.*
> - *Learn about the first resident crews and their pioneering work.*
> - *Recognize astronauts who have set records for time in space or conducted significant spacewalks.*

The format was right but the content was not. "The first resident crews" is still a placeholder.
---

## 3. Iteration 2: Adding a Thinking Budget

Next, I gave the model a 1024-token thinking budget to see if a planning scratchpad would improve the detail. I kept the prompt exactly the same.

Results (`gemini-baseline-ef9d4c3f`):

| Metric | Before | After |
|---|:---:|:---:|
| Actionability & Completeness | 3.80 | 4.40 |
| Instruction Following | 4.10 | 4.40 |

Small improvement. But looking at the actual output, the model still used placeholders instead of specific details:

> *Understand the purpose and global collaboration behind the International Space Station (ISS).*
> - *Learn that the ISS is a unique research laboratory orbiting Earth.*
> - *Identify the major countries and space agencies that partnered to build and operate the ISS, including the USA, Russia, Europe, Japan, and Canada.*
>
> *Explore the timeline of the ISS's construction and assembly.*
> - *Identify the launch date of the first ISS module, Zarya, in 1998.*
> - *Understand that the ISS became continuously inhabited by astronauts starting in November 2000.*
>
> *Identify notable astronauts and their contributions.*
> - *Learn about the diverse crews that have lived and worked on the ISS, representing many different nations.*
> - *Recognize astronauts who have set records for time spent in space or performed groundbreaking missions.*

The model still used placeholders like "diverse crews" instead of naming specific astronauts. The thinking budget helped the model structure its reasoning but it didn't solve the underlying problem not including concrete details. 

At this point the eval scores were suspiciously high given how vague the outputs were. That led me to look harder at the judge.

---

## 4. Calibrating the LLM Judge

The LLM judge, running on `gemini-3.1-flash-lite`, had a positivity bias. It was scoring outputs high even when they used vague placeholders instead of concrete facts. A response that said "identify famous astronauts" was getting the same score as one that named them.

I re-evaluated the Iteration 2 run with a calibrated judge. Same agent, same outputs, new rubric constraint: if the output uses generic placeholders instead of named facts, the max score for actionability and instruction following is capped at 2.

Re-evaluated results (`gemini-baseline-afd8999f`):

| Metric | Before Calibration | After Calibration |
|---|:---:|:---:|
| Actionability & Completeness | 4.40 | **2.70** |
| Instruction Following | 4.40 | **2.90** |

The new constraint dropped the actionability and instruction following scores, proving the lenient judge had been masking the model's vague outputs.

---

## 5. Iteration 3: Integrating Exa Search

The prompt wasn't the problem anymore, the model just did not know the facts. Without a search tool, it could not pull up specific names, dates, or measurements.

I upgraded the system from a direct LLM call to a ReAct agent with a live web search tool backed by Exa. The agent searches for facts first, then writes the plan based on what it finds.

Since Exa is not a keyword search engine, it works best with declarative, link-continuation style queries written as natural authoritative sentences. I added these instructions directly to the agent prompt:

> *"You MUST use this search tool to gather real, concrete facts before writing your educational plan.*
>
> *NEURAL DECLARATIVE QUERIES ONLY: Write your query as a natural, authoritative sentence that looks like the text that would immediately lead into a high-quality link perfectly answering the question.*
>
> *Example style: "Here is a comprehensive, chronological timeline of all key assembly dates and resident astronaut crews on the International Space Station (ISS):"*
>
> *SEARCH FOR THE RAW TRUTH: Do NOT include age or grade filters in your search queries. Search for the raw, rigorous scientific, physical, or historical truth. You are the expert instructional designer and you will translate and simplify these facts into K-12 friendly language yourself in the final response.*
>
> *OPTIMIZE SEARCH LATENCY: Perform a maximum of 1 or 2 high-quality, comprehensive searches."*

The first run hit a token limit issue. The thinking budget and search results together consumed most of the budget before the model could finish writing. I adjusted the token ceiling and re-ran.

The trade-off here is latency. Exa adds 5-15 seconds per query. For a real-time product that's a real cost. I kept it because the quality gain was worth it, but it's something to revisit depending on the actual UX requirements.

Results (`gemini-baseline-e754bfa4`):

| Metric | Before | After |
|---|:---:|:---:|
| Actionability & Completeness | 2.70 | 3.30 |
| Instruction Following | 2.90 | 3.50 |
| Factuality & Groundedness | — | 4.80 |

ISS output after the fix:

> *Understand the collaborative origins and evolution of the International Space Station (ISS).*
> - *Learn that the ISS concept was born in September 1993 from a partnership between the United States and Russia, merging earlier, separate station plans like the US's "Freedom" and Russia's "Mir-2".*
> - *Recognize the historical precedent for international space cooperation, including the 1975 Apollo-Soyuz Test Project.*
> - *Identify the five primary space agencies involved: NASA (USA), Roscosmos (Russia), JAXA (Japan), ESA (Europe), and CSA (Canada), who signed the Inter-Governmental Agreement in 1998.*
>
> *Explore the key milestones in the ISS assembly and construction.*
> - *Discover that the first module, Russia's Zarya, was launched in October 1998.*
> - *Learn that the first US module, Unity (Node 1), was delivered by the Space Shuttle Endeavour (STS-88) in December 1998, marking the beginning of physical assembly.*
> - *Identify the Zvezda Service Module, launched in July 2000, as providing essential living quarters for the crew.*
>
> *Recognize the significance of the first resident crews and continuous human presence.*
> - *Understand that the first resident crew, Expedition 1, launched on October 31, 2000, and docked on November 2, 2000.*
> - *Learn that Expedition 1 Commander William M. "Shep" Shepherd, Flight Engineer Yuri P. Gidzenko, and Flight Engineer Sergei K. Krikalev were the first to live aboard the ISS.*
> - *Appreciate that the ISS has maintained a continuous human presence in orbit since November 2, 2000, for over two decades.*
>
> *Identify major modules and their contributions to the ISS.*
> - *Explore the role of the Columbus Laboratory (ESA), launched in 2008, as a key European research facility.*
> - *Learn about the Japanese Experiment Module "Kibo" (JEM), the largest single module on the ISS, which began assembly in 2008.*
> - *Recognize the importance of the Destiny Laboratory (NASA), delivered in 2001, as the primary US research facility.*
>
> *Discover significant events and the ISS's role as a research platform.*
> - *Understand the impact of the Space Shuttle Columbia disaster in 2003, which grounded the shuttle fleet and led to a reduction in ISS crew size to two.*
> - *Learn about the "Year in Space" mission, involving astronaut Scott Kelly and cosmonaut Mikhail Kornienko, who spent nearly a year aboard the ISS starting in 2015 to study long-term spaceflight effects.*
> - *Explore the ISS's function as a unique microgravity laboratory for scientific research across various disciplines, including biology, physics, and Earth observation.*
>
> *Appreciate the ISS's operational lifespan and future plans.*
> - *Recognize that the ISS was originally intended for a 15-year mission but has been extended multiple times due to its success.*
> - *Learn that the US, ESA, Canada, and Japan have committed to ISS operations until 2030, with Russia committed until at least 2028.*
> - *Understand that NASA plans to deorbit the station in 2031, potentially after the development of commercial space stations.*


---

## 6. Iteration 4: Expanded Test Set and Prompt Refinements

Three changes in this iteration.

**Expanding the eval dataset.** I curated a broader dataset with 10 queries spanning different subjects, grade levels, and edge cases. I used Gemini 3.1 Pro to generate diverse queries and reference outputs, then reviewed and corrected the facts manually. 

Pydantic structured output had been in the system from the beginning, initially as a direct binding on the language model. When Exa was added in iteration 3 and the architecture switched to a ReAct agent, the structured schema was passed directly as the agent's required response format. 

**Generalizing and calibrating the evaluator.** When the test set grew to include general subjects like fractions and Shakespeare, I generalized the judge from an aerospace-only specialist to a general K-12 education specialist. At the same time, I noticed the judge was docking points when outputs lacked VR software design and interactive specs. I updated the evaluator instructions to clarify that the agent is only meant to generate curriculum Key Learnings, which kept the judge from docking points for missing software layouts.

**Adding few-shot examples to the prompt.** Without few-shot examples, actionability and instruction following scored 3.83 and 4.00. The model followed the structure and found correct facts, but listed general topics instead of specific names, dates, and measurements. I added two few-shot examples to guide the model's level of detail. 

I added two worked examples directly into the system prompt: a Great Barrier Reef biology lesson and an Apollo 11 VR simulation, both chosen to be topic-neutral relative to the test set.

**System Prompt (`SYSTEM_PROMPT`):**
> You are an expert curriculum designer. You create structured learning plans for immersive AR/VR/MR educational experiences for K-12 students.
> Given a topic or description of an educational experience, generate a detailed set of Key Learnings the student should walk away with.
> 
> **Format rules:**
> - Always begin with the header "Key Learnings:"
> - List 4 to 7 top-level learning objectives. Each should begin with an action verb such as Understand, Learn, Identify, Recognize, Explore, Appreciate, Compare, Analyze, or Discover.
> - Under each objective, add 2 to 4 nested bullet points that provide concrete supporting detail.
> - Do not write paragraphs or flowing prose.
> - Adjust vocabulary and complexity to the target grade level. If no grade level is specified, target a 6th to 8th grade audience.
> 
> **Content requirements:**
> - For every topic, surface the most important concrete facts. This means including:
>     - Named people (scientists, inventors, leaders, historical figures, and their specific role or contribution)
>     - Key dates or milestones
>     - Named organizations, agencies, or institutions
>     - Specific events, discoveries, or breakthroughs
> 
> **Quality requirements:**
> - All facts, figures, and explanations must be accurate. Never fabricate specifics.
> - Each nested bullet should be specific enough that a developer could use it to build a 3D asset, an interactive element, a timeline marker, or an on-screen label in an AR/VR scene.
> 
> ---
> 
> **Example 1:**
> *User query:* "Create an immersive biology lesson about the Great Barrier Reef ecosystem for 6th graders, covering coral types, symbiotic relationships, threats, and conservation efforts."
> 
> *Key Learnings:*
> * Understand the scale and structure of the Great Barrier Reef.
>     * Learn that the Great Barrier Reef stretches over 2,300 km along Australia's Queensland coast, making it the world's largest coral reef system and visible from space.
>     * Identify the two main coral types: hard corals (such as staghorn and brain coral) that form calcium carbonate skeletons to build the reef structure, and soft corals (such as sea fans) that flex with ocean currents.
>     * Recognize that the reef is managed by the Great Barrier Reef Marine Park Authority (GBRMPA), established by Australia in 1975 to protect the ecosystem.
> * Explore symbiotic relationships that keep the reef alive.
>     * Learn how microscopic algae called zooxanthellae live inside coral tissue, producing food through photosynthesis in exchange for shelter. Without them, coral starves and bleaches white.
>     * Identify the mutualistic relationship between clownfish and sea anemones: the fish gains protection from the anemone's stinging cells, while the fish's movement circulates water and removes parasites from the anemone.
> * Recognize the major threats facing the reef.
>     * Understand coral bleaching: when ocean temperatures rise even 1-2°C above normal, corals expel their zooxanthellae. The 1998 mass bleaching event, the worst recorded at that time, damaged 50% of the reef.
>     * Identify how agricultural runoff and rising ocean acidity weaken coral skeletons by interfering with the calcification process corals use to grow.
> * Learn about conservation efforts and the scientists leading them.
>     * Explore the work of marine biologist Sylvia Earle, who has spent decades documenting ocean ecosystem collapse and advocating for marine protected areas.
>     * Identify coral restoration techniques such as coral gardening, where fragments of healthy coral are grown on underwater nursery trees and then transplanted onto damaged reef sections.
> 
> ---
> 
> **Example 2:**
> *User query:* "A VR experience for 9th graders where they step onto the lunar surface alongside the Apollo 11 crew, exploring the mission timeline, the technology that made it possible, and its legacy for human spaceflight."
> 
> *Key Learnings:*
> * Understand the context and goal of the Apollo 11 mission.
>     * Learn that Apollo 11 was the first crewed mission to land on the Moon, launched by NASA on July 16, 1969, as part of the broader Apollo program initiated in response to the Space Race with the Soviet Union.
>     * Recognize that the mission fulfilled President John F. Kennedy's 1961 national goal of landing a human on the Moon before the end of the decade.
> * Identify the crew and their distinct roles.
>     * Learn that Neil Armstrong (Commander) became the first human to walk on the Moon on July 20, 1969, at 10:56 PM UTC, in the Sea of Tranquility.
>     * Identify Buzz Aldrin (Lunar Module Pilot), who joined Armstrong on the surface for 2 hours and 31 minutes of extravehicular activity (EVA).
>     * Recognize that Michael Collins (Command Module Pilot) remained in lunar orbit aboard Columbia while Armstrong and Aldrin descended in the Eagle lunar module.
> * Explore the key technology that enabled the landing.
>     * Identify the Saturn V rocket, standing 111 meters tall and producing 34.5 million newtons of thrust at liftoff, as the most powerful rocket ever successfully flown.
>     * Learn that the Eagle lunar module separated from Columbia in orbit and used a descent propulsion system to achieve a powered landing, with Armstrong manually piloting the final approach after the onboard computer triggered an overload alarm.
> * Recognize what the crew collected and left behind.
>     * Learn that Armstrong and Aldrin collected 21.5 kg of lunar rock and soil samples, which scientists have used to study the Moon's formation and the early solar system.
>     * Identify the scientific instruments left on the surface, including a seismometer to detect moonquakes and a laser-ranging retroreflector still used today to precisely measure the Earth-Moon distance.

**Search Agent System Prompt (`AGENT_SYSTEM_PROMPT`):**
> You are an autonomous Research & Planning Agent. You have access to a neural web search tool (Exa).
> You MUST use this search tool to gather real, concrete facts (specific names, dates, events, numbers, metrics) before writing your educational plan.
> 
> **CRITICAL SEARCH STRATEGY & RULES:**
> 
> **1. NEURAL DECLARATIVE QUERIES ONLY:**
> - Exa is a neural, embeddings-based search engine, NOT a keyword Google search. Do not use keywords or questions (e.g., avoid "history of ISS key dates" or "how do volcanoes erupt?").
> - You must use "Link-Continuation" or "Declarative" prompting. Write your query as a natural, authoritative sentence that looks like the text that would immediately lead into a high-quality link perfectly answering the question.
> - Imagine you are writing a blog post or technical article, and are about to link to the answer. Write the words right before that imaginary link.
> - Example style: "Here is a comprehensive, chronological timeline of all key assembly dates and resident astronaut crews on the International Space Station (ISS):"
> - Example style: "Magma rises from the Earth's mantle and causes a volcanic eruption through the following physical mechanisms:"
> 
> **2. SEARCH FOR THE RAW TRUTH:**
> - Do NOT include age or grade filters in your search queries (e.g., avoid "for kids", "for 3rd graders", "elementary level").
> - Search for the raw, rigorous scientific, physical, or historical truth. You (the LLM) are the expert instructional designer, so you will translate and simplify these highly accurate facts into K-12 friendly language yourself in the final response.
> 
> **3. OPTIMIZE SEARCH LATENCY:**
> - Perform a maximum of 1 or 2 high-quality, comprehensive searches.
> - Craft your declarative query to be broad and authoritative enough to capture all necessary facts (dates, names, metrics) in a single request, avoiding sequential API bloat.


Results (`gemini-baseline-dfa058d7`):

| Metric | Before | After |
|---|:---:|:---:|
| Clarity & Structure | — | **5.00** |
| Tone & Grade Appropriateness | — | **5.00** |
| Factuality & Groundedness | — | **5.00** |
| Actionability & Completeness | 2.70 | 3.83 |
| Instruction Following | 2.90 | 4.00 |

After adding the few-shot examples, I re-ran the full evaluation set.

Final results:

| Metric | Baseline | Final |
|---|:---:|:---:|
| Clarity & Structure | 3.20 | **5.00** |
| Tone & Grade Appropriateness | 4.20 | **5.00** |
| Factuality & Groundedness | 4.60 | **5.00** |
| Actionability & Completeness | 2.30 | **5.00** |
| Instruction Following | 2.80 | **5.00** |

The model used throughout is Gemini 2.5 Flash Lite. It is fast and inexpensive, which made it practical to run repeated evaluation iterations. A larger model might reach these scores without prompt engineering, but it would increase cost and latency. Grounding and structured output on a lighter model is more practical for production.

---

## 7. Example Outputs

### Example 1: ISS History

**Query:**
> "Teach about the history of the International Space Station including important dates, famous astronauts, and interesting events."

**Before (original prompt):**
> *Students will learn about the International Space Station's (ISS) origins as a collaborative project, key construction milestones (e.g., Zarya module launch in 1998, first crew arrival in 2000), and its continuous human presence. They will identify significant astronauts and their contributions (e.g., **Yuri Gagarin's pioneering flight, Valentina Tereshkova as the first woman in space**, Chris Hadfield's popularization of space life)...*
> (Single paragraph. Two hallucinations highlighted: Gagarin and Tereshkova never went to the ISS.)

**After (final agent):**
> *Understand the International Space Station (ISS) as a global collaboration.*
> - *Learn that the ISS is a partnership between five space agencies: NASA (United States), Roscosmos (Russia), JAXA (Japan), CSA (Canada), and ESA (European countries).*
> - *Recognize that the ISS is the largest international cooperative program in science and technology, with over 40 missions required for its assembly in orbit.*
> - *Discover that the ISS weighs nearly 400 tonnes and covers an area as large as a football pitch.*
>
> *Explore the timeline of the ISS construction.*
> - *Identify the launch of the first module, the Russian-built Zarya Control Module, on November 20, 1998.*
> - *Learn about the arrival of the first U.S. module, the Unity Node, on December 6, 1998, marking the beginning of orbital assembly.*
> - *Recognize the addition of key modules like the Zvezda Service Module (July 2000), the U.S. Destiny Laboratory (February 2001), ESA's Columbus laboratory (February 2008), and Japan's Kibo laboratory (March/May 2008).*
>
> *Identify the first crew and the concept of long-duration expeditions.*
> - *Learn that the first resident crew, Expedition 1, arrived on November 2, 2000, consisting of Commander William M. "Shep" Shepherd (NASA), Flight Engineer Yuri P. Gidzenko (Roscosmos), and Flight Engineer Sergei K. Krikalev (Roscosmos).*
> - *Recognize astronauts like Scott Kelly and Mikhail Kornienko who completed year-long missions, and Peggy Whitson who set records for cumulative time in space.*

---

### Example 2: Wright Brothers Flight Simulator (7th Grade)

**Query:**
> "Create a flight simulator experience for 7th graders teaching the Wright Brothers' first successful flight."

**Before (original prompt):**
> *Students will learn about the key challenges faced by the Wright Brothers, including understanding aerodynamics, wing warping for control, and engine power. They will experience the iterative design process through simulated trials and errors, culminating in the successful flight at Kitty Hawk. Key takeaways include the importance of perseverance, scientific inquiry, and the foundational principles of flight that paved the way for modern aviation.*

**After (final agent):**
> *Identify the key components and design of the Wright Flyer I.*
> - *Explore the Wright Flyer I, a biplane aircraft with a 40-foot wingspan, built from wood and fabric.*
> - *Learn about its unique propulsion system: a 12-horsepower engine driving two pusher propellers via a chain system, designed to rotate in opposite directions.*
>
> *Discover the historic first powered flights on December 17, 1903.*
> - *Identify Orville Wright as the pilot of the first flight, which lasted 12 seconds and covered 120 feet (36 meters) in a 27-mph headwind.*
> - *Understand that four flights were made that day, with Wilbur Wright achieving the longest flight of 852 feet (255.6 meters) in 59 seconds.*
>
> *Recognize the critical innovations that made powered flight possible.*
> - *Identify their development of a three-axis control system (pitch, roll, and yaw) as a fundamental contribution to aviation.*
> - *Learn that the famous photograph of the first flight was taken by John T. Daniels, a volunteer from the nearby lifesaving station.*

---

### Example 3: Edge Case "Shakespeare" (no grade or context)

**Query:**
> "Shakespeare"

**Before (original prompt):**
> *This VR experience will immerse students in the world of William Shakespeare, allowing them to explore Elizabethan England, visit the Globe Theatre, and witness key scenes from his plays brought to life. Students will gain a deeper understanding of Shakespeare's historical context, the performance practices of his time, and the enduring themes and language of his works. Key learnings include:*
> *1. Historical Context: Understanding the social, cultural, and political environment in which Shakespeare wrote.*
> *2. The Globe Theatre: Learning about the architecture, audience, and staging conventions of Elizabethan playhouses.*
> *3. Dramatic Interpretation: Analyzing key soliloquies and dialogues, understanding character motivations, and appreciating Shakespeare's use of language.*
> *4. Thematic Exploration: Identifying and discussing universal themes present in Shakespeare's plays, such as love, ambition, revenge, and fate.*

**After (final agent):**
> *Identify Shakespeare's significant role in the London theatre scene.*
> - *Learn that by 1592, Shakespeare was established in London as an actor and playwright, as noted by rival dramatist Robert Greene.*
> - *Discover that Shakespeare was a founding member, actor, playwright, and shareholder of the Lord Chamberlain's Men, which was renamed the King's Men in 1603 under King James I.*
>
> *Explore Shakespeare's prolific body of work.*
> - *Identify key poems such as "Venus and Adonis" (1593) and "The Rape of Lucrece" (1594), and his Sonnets published in 1609.*
> - *Recognize his later tragedies: Hamlet, Othello, King Lear, and Macbeth.*
> - *Understand that by 1598, Francis Meres described Shakespeare as England's greatest writer in both comedy and tragedy.*
>
> *Appreciate Shakespeare's lasting impact on language and literature.*
> - *Learn that Shakespeare coined hundreds of new words and phrases still used today.*
> - *Discover that the First Folio was published in 1623 by actors John Heminge and Henry Condell, containing 36 plays.*

---

### Example 4: Solar System Tour focusing on Mars (3rd Grade)

**Query:**
> "Create an interactive solar system tour for 3rd graders focusing on Mars."

**Before (original prompt):**
> *Students will learn about Mars's position in the solar system, its key characteristics (red color, size, atmosphere), and compare it to Earth. They will also discover interesting facts about Mars, such as its volcanoes and potential for past water.*

**After (final agent):**
> *Understand Mars's place in our solar system.*
> - *Learn that Mars is the fourth planet from the Sun, after Mercury, Venus, and Earth.*
> - *Recognize that Mars is a rocky planet, like Earth, and is often called the "Red Planet" because of its color.*
> - *Discover that Mars takes 687 Earth days to travel all the way around the Sun.*
>
> *Explore the surface and environment of Mars.*
> - *Identify Mars as a dry, rocky, and very cold planet.*
> - *Learn that billions of years ago, Mars was warmer and wetter, with a thicker atmosphere.*
> - *Understand that Mars has giant volcanoes, like Olympus Mons (the largest volcano in the solar system), and deep canyons.*
>
> *Discover the robotic explorers sent to Mars.*
> - *Learn that NASA has sent many robots, called rovers, to explore Mars, like Curiosity and Perseverance.*
> - *Identify that these rovers have special tools, cameras, and even lasers to study rocks and soil.*
> - *Recognize that Mars is the only planet we know of that is currently explored entirely by robots.*
>
> *Learn about the search for water and life on Mars.*
> - *Understand that scientists are looking for signs that Mars might have had tiny life forms in the past.*
> - *Discover that missions like the Spirit and Opportunity rovers were sent to find evidence of water on Mars.*
> - *Appreciate that what we learn about Mars helps us understand our own planet, Earth, better.*

---

### Example 5: James Webb Space Telescope (11th Grade)

**Query:**
> "Explain the James Webb Space Telescope (JWST) for 11th graders."

**Before (original prompt):**
> *Students will learn about the James Webb Space Telescope's (JWST) primary mission: to observe the universe in infrared light. They will understand why infrared is crucial for studying distant and early galaxies, star formation, and exoplanet atmospheres. Key takeaways include JWST's advanced technologies, such as its segmented mirror and sunshield, and how these enable its unprecedented observational capabilities. Students will also grasp the telescope's role in answering fundamental questions about the cosmos, like the formation of the first stars and galaxies and the potential for life beyond Earth.*

**After (final agent):**
> *Understand the James Webb Space Telescope's (JWST) role as a revolutionary observatory.*
> - *Learn that JWST is the premier infrared observatory of the next decade, designed to complement and extend the discoveries of the Hubble Space Telescope.*
> - *Recognize that it was launched by NASA on December 25, 2021, aboard an Ariane 5 rocket.*
> - *Identify that JWST is a joint mission involving NASA, the European Space Agency (ESA), and the Canadian Space Agency (CSA).*
>
> *Explore the advanced technology enabling JWST's deep space observations.*
> - *Identify the primary mirror as a massive 6.5-meter (21.3 ft) diameter structure composed of 18 hexagonal segments made of beryllium coated with gold, designed to fold for launch and unfold in space.*
> - *Understand the function of the 5-layer, tennis-court-sized sunshield (21.197 m x 14.162 m) which protects the telescope from the heat of the Sun, Earth, and Moon, allowing it to operate at extremely cold temperatures (below 50 K or -370 °F).*
> - *Learn that JWST orbits the Sun at the second Lagrange point (L2), approximately 1.5 million kilometers (1 million miles) away from Earth, providing a stable thermal environment.*
>
> *Discover the scientific instruments and their capabilities.*
> - *Identify the four main science instruments: Near Infrared Camera (NIRCam), Near Infrared Spectrograph (NIRSpec), Mid Infrared Instrument (MIRI), and Fine Guidance Sensors/Near Infrared Imager and Slitless Spectrograph (FGS/NIRISS).*
> - *Understand that these instruments allow JWST to capture images and analyze light across a wide range of infrared wavelengths (0.6 to 28.5 microns), enabling it to see through dust clouds and observe distant, redshifted objects.*
>
> *Recognize JWST's primary mission objectives for exploring the universe.*
> - *Learn that JWST aims to observe the first galaxies and luminous objects that formed after the Big Bang, peering back over 13.5 billion years.*
> - *Understand its role in studying the evolution of galaxies from their early formation to the present day.*
> - *Explore how JWST investigates the formation of stars and planetary systems, including the potential for life on exoplanets by measuring their physical and chemical properties.*

---

## 8. Repository and System Overview

Full implementation at: **https://github.com/nateislas/educational_assistant**

The system is built in Python using LangChain and LangGraph to construct the agent workflow. The agent uses Gemini 2.5 Flash Lite as the base model configured with a reasoning thinking budget, Exa for live search, and a Pydantic schema for structured output responses. Evaluation is performed via LangSmith using gemini-3.1-flash-lite as the judge model. Each experiment was run as a separate LangSmith evaluation project, making the entire progression fully traceable and reproducible.
