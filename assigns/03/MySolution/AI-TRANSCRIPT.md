# Assignment 3: AI Assistance Record

**Tool:** GitHub Copilot in VS Code using MAI-Code-1.1-Flash

## Use of AI

I used GitHub Copilot to read the assignment brief, interpret the stakeholder requirements, draft the requirements specification, and format the final submission under MySolution. The primary source material was Assign03.md and LAMBDA-UI-informal-requirements.md. The assignment instructions and the course brief governed the final content; the AI was used to structure and refine the writing rather than to invent stakeholder decisions.

## Important Prompts and Assistance

| Request | Significant assistance |
| --- | --- |
- Read Assign03.md and explain what is required. Copilot summarized the tasks, the required submission files, the emphasis on requirements engineering, and the distinction between specifying the system and implementing software.
- Read the informal stakeholder brief and identify the main needs. Copilot extracted the user groups, the browser-based testing environment goals, the requirements around compile/run workflows, testing collections, and the need to distinguish environment failures from program errors.
- Draft the requirements specification in MySolution. Copilot organized the document into purpose, scope, assumptions, functional requirements, quality requirements, interfaces, acceptance criteria, and traceability, while keeping the wording testable and tied to the brief.
- Identify clarifying questions and unresolved issues. Copilot produced a set of stakeholder questions and noted where assumptions were needed because the brief left details unspecified, including compiler interfaces, persistence strategy, and timeout behavior.
- Turn the stakeholder brief into concrete, valid requirements. Copilot helped turn ordinary-language needs into numbered functional requirements such as compile/run functionality, cancellation, result-version tracking, error localization, saved tests, and persistence after refresh.
- Create a review section. Copilot mapped requirements to passages in the brief and recorded issues such as ambiguity between sample examples and saved tests and the need to preserve results after edits.
- Prepare the AI transcript in the requested format. Copilot restructured the transcript into a record matching the sample format, then I reviewed it to ensure the content reflected the actual session and not invented AI usage.

## Manual Review

After each step, I manually reviewed the content and refined it to match the assignment brief and the evidence in the actual session. I checked that the requirements remained grounded in the brief, the assumptions were clearly labeled, and that no misunderstandings were created. I reviewed the spec  before finalizing the document.

## Checks and Corrections Performed by AI

Copilot checked the draft against the assignment instructions and the stakeholder brief, helped identify gaps in traceability, and suggested clarifications for ambiguous areas. During the final review step, it helped separate sample examples from saved test collections and record assumptions where the brief did not specify a stakeholder decision. The resulting structure is in REQUIREMENTS.md.
