# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**
I should be able to add a pet, schedule a walk, and schedule feeding times. These are core features that are part of the UML design.


- Briefly describe your initial UML design. 
My initial UML design consists of 4 classes with 4 edges connecting the entire design. Owner class is the first class, connecting to pet and schedule classes, schedule classes go to caretask, and caretask goes to pet as well.


- What classes did you include, and what responsibilities did you assign to each?
It features a owner class with attributes name, age, gender, budget, and pets; containing methods addPet which connects to the pet class, remove pet, generateSchedule which uses the schedule class and a date, and adjust budget taking a float amount for budget. There are classes owner which conects to pet and schedule classes, schedule class can have a task added or removed and etc. It connects to the caretask class which details the care in which the pets are recieving, finally connecting back to the pet class.


**b. Design changes**

- Did your design change during implementation?
Yes, the changes were adding a owner reference to the schedule class, and fixing the general schedule only taking a date and adding more thigns like task duration, priority, or budget. I made these changes because these could possibly cause logic breaks especially when a schedule is not contained in the owner class, and a non detailed generating schedule method. 

- If yes, describe at least one change and why you made it.
^^^above
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?


- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
