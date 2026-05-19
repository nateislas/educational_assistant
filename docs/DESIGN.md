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


## Getting started

Before making any improvements to the prompt, I created an eval pipeline. We are going to judge the LLM responses on criteria include:

I think this gives us a good starting point to measure LLM response quality. 