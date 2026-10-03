# Prototype

**You own the design decision, not the code. The prototype is a throwaway instrument. The real build follows Feature.**

The one playbook where the Laziness Protocol's "smallest change" and the verification bar invert. Speed over polish, code quality does not matter, no planning. The rigor is in picking the right design cheaply. Propose variations the user didn't ask for, throw an approach away and try another.

1. Scope the decision the prototype exists to make: which layout, which interaction, which density, or for an empirical fork which behavior, timing, or approach. No decision means no prototype. Route to Feature.
2. Gather references when the design space is open. Search for prior art, summarize the options, let the user pick directions before building. Skip when the direction is set.
3. Build throwaway in a scratch directory outside the project's source tree (a temp directory, or one the user names). Never in production source, never against a production system. For a visual decision, vanilla HTML/CSS/JS or the lightest stack that renders the idea. For a behavioral or timing decision, the smallest script that exercises the question. No production framework, no tests, no abstractions. Pulling in a new dependency still needs the user's approval.
4. When comparing alternatives, build them behind one switcher (a flag, buttons, or a keypress), each variant labeled. This is **principle-exhaust-the-design-space** made cheap.
5. Verify by observing the thing you are deciding. For a visual decision, render each variant and look at it (a browser the user opens, or a headless screenshot when a tool for it is installed). For a behavioral or timing decision, log the timing, print the output, or watch the run. The observation is the test here, not an assertion.
6. Present alternatives, tradeoffs, and a recommendation. The output is the decision plus the throwaway artifact, not shippable code. Hand the chosen direction to Feature (or `architect` for the shape) for the real build.

**Reply.** The variants explored, the evidence (screenshots or the observed output or timing), tradeoffs, your recommendation, and the scratch path. Say plainly that the prototype is throwaway.
