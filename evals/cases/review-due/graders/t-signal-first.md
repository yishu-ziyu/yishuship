---
type: llm
group: target
weight: 2
---
Facts: the progress file says success is seen in usage.log (the morning `list` runs and which items got ticked off). usage.log shows `list` on 7 of the 12 days from 2026-09-11 to 2026-09-22, with gaps (09-14, 09-17, 09-19 to 09-21), and `done` only on 3 days.
PASS if, before asking whether it worked, the reply reports what usage.log actually shows with concrete numbers or dates (for example how many mornings `list` was run, or that it stopped after some date), and its recommendation takes that into account.
FAIL if it only asks the user whether it worked without looking at usage.log, or states usage figures that contradict the facts.
