# LAMBDA Testing Environment Requirements Specification

## 1. Purpose

This document defines the requirements for a local web-based environment for writing and testing LAMBDA programs. The environment will let students and the instructor enter programs, submit them to the LAMBDA compiler tools, inspect results, and save examples as tests that can be run again after compiler changes.

The goal is to support student practice and classroom demonstrations through reliable editing, clear results, and repeatable tests. These requirements are based on the instructor's brief and will guide development and evaluation of the environment.

## 2. Stakeholders and Goals

Students and the instructor are the primary users of the environment. The compiler interface provider is an external stakeholder whose tools the environment depends on. The roles below may overlap; a student working on the compiler may also use the environment to write programs.

| Stakeholder | Role and main goals |
| --- | --- |
| Students writing LAMBDA programs | Write or load programs, modify examples, compile or run them, understand results and errors, and save work for later use. The environment must also support students who have not used the compiler before. |
| Students modifying the compiler | Maintain named tests with expected outcomes and rerun test collections to identify failures introduced by compiler changes. |
| Course instructor | Demonstrate and modify examples during lectures, inspect available compiler information, and retain examples for future use. The instructor also provides the needs that guide the system's scope and priorities. |
| Compiler interface provider | Coordinate the interface between the LAMBDA tools and the environment, including the supported operations and information available in compiler responses. |

## 3. System Boundary

The environment provides the browser interface for editing and loading programs, managing examples and test collections, submitting compilation or execution requests, and displaying the returned results. It is also responsible for preserving user work and comparing test outcomes with their expected results.

The LAMBDA tools are an external dependency responsible for processing and executing programs and returning results or diagnostics. The environment presents the information these tools provide, including source locations and intermediate representations when available. Developing the compiler itself is a separate project.

The environment team must coordinate with the compiler interface provider to establish how requests and responses are exchanged. The brief does not identify that provider or define the interface. Since the current interpreter uses abstract syntax trees constructed in Python and source notation remains undecided, the environment cannot assume that the tools already accept typed LAMBDA source text. These details remain subject to clarification.

## 4. First-Version Scope

The first version will run locally on a student's or instructor's computer and be accessed through a browser. Its scope prioritizes reliable editing, understandable results, and repeatable tests, as requested in the brief.

The table includes core capabilities and optional candidates. Compiler-information inspection (FR-10) and demonstrations using sample responses (FR-19) are optional under the proposed priorities in Section 6; listing them here does not make them mandatory for the first version.

| Area | Included capabilities |
| --- | --- |
| Programs and examples | Enter, paste, and load programs; modify starter examples while retaining access to the originals; and save work for later use. |
| Compilation and execution | Request compilation without execution or run a program, display results, and inspect compiler information such as ASTs or generated code when available. |
| Errors and ongoing work | Distinguish compilation errors, runtime failures, and compiler unavailability; show source locations when supplied; preserve work during compiler outages; support stopping long-running work; and associate results with the submitted program version. |
| Test collections | Maintain named tests with expected values or expected compilation rejection, rerun collections, and show summaries and individual outcomes. One troublesome test must not prevent use of the remaining collection. Saved examples and collections must remain available across refreshes and sessions. |
| Usability and setup | Provide local setup instructions, keyboard access to main tasks, messages that do not depend only on color, and a usable interface while compilation or execution is in progress. |
| Integration development | Allow demonstrations using clearly labeled sample compiler responses while the tools are unfinished, with eventual connection to the real tools through the agreed interface. |

The accepted program representation, compiler interface, saving behavior, cancellation support, supported browsers, and measurable quality targets remain subject to clarification. Inclusion in this scope does not establish that the compiler already supports every requested operation.

Public hosting, user accounts, and simultaneous collaborative editing are outside the first version, as stated in the brief. Compiler development remains outside the environment project.

Collection sharing is proposed for a later version because the instructor explicitly permits its deferral. Sophisticated visual effects and additional features of a full development environment are also proposed for deferral so that the first version can focus on the stated priorities. These deferrals are scope proposals, not additional stakeholder agreements.

## 5. Clarification Questions and Assumptions

The instructor's brief is the stakeholder input available for this specification. No additional stakeholder answers have been received. The questions below remain open for stakeholder clarification. Where a working assumption supports the draft requirements, it is recorded separately and does not represent a stakeholder decision.

| ID | Clarification question | Why the answer matters | Status |
| --- | --- | --- | --- |
| Q-01 | Who will provide the compiler interface, and what operations and response information will it support, including results, errors, source locations, and intermediate representations? | Identifies the integration contact and establishes what the environment can request and display without requiring it to implement compiler functionality. | Unresolved |
| Q-02 | What program representation should users enter or load in the first version, given that source notation is undecided and the current interpreter accepts Python-constructed ASTs? | Determines the accepted editor and file input and what can be submitted to the language tools. | Unresolved |
| Q-03 | Should programs and test collections be saved automatically or through an explicit save action, and must unfinished edits also survive refreshes and later sessions? | Defines when work is considered saved and exactly what must be restored, rather than assuming that preserving saved programs also preserves every edit. | A-01 proposed; unsaved-edit recovery unresolved |
| Q-04 | Which expected value types must tests support, and should an expected compilation failure match any rejection or a particular diagnostic? | Defines how the environment determines whether a test passed and prevents unrelated failures from being counted as the expected outcome. | A-02 proposed; stakeholder confirmation pending |
| Q-05 | What cancellation support will the tools provide, and should a nonterminating test be stopped automatically after an agreed limit or require user intervention? | Determines how execution can actually be stopped and how the remaining tests can continue. Any time limit would need to be agreed or explicitly proposed. | A-04 proposed; tool support unresolved |
| Q-06 | When a result arrives after the program has been edited, should users be able to inspect the submitted version, or is a clear indication that the result belongs to an earlier version sufficient? | Establishes how users identify the program that produced a result without assuming a full version-history feature. | A-03 proposed; stakeholder confirmation pending |
| Q-07 | Which browsers and operating systems must the first version support, and what local setup prerequisites are acceptable? | Defines the supported environment and the conditions under which setup instructions and compatibility will be evaluated. | Unresolved |
| Q-08 | What task-completion and interface-response targets should define acceptable usability and responsiveness, and under what program sizes and test-collection sizes should they be assessed? | Makes terms such as "straightforward" and "promptly" verifiable while separating ordinary interface response from compiler execution time. | A-05 and QR-01 assessment proposed; stakeholder confirmation pending |

### Working assumptions

The following proposals allow specific behavior to be described while stakeholder answers are unavailable.

| ID | Related question | Proposed assumption and reason |
| --- | --- | --- |
| A-01 | Q-03 | Provide explicit saving of programs and test collections, with saved content available after refresh or reopening in the same browser profile on the same computer. This defines a minimum persistence guarantee. Recovery of unsaved edits and access from other browsers remain unresolved. |
| A-02 | Q-04 | Initially compare integer and Boolean results by both type and value. An expected compilation rejection matches any compiler-reported compilation error, but never a runtime or environment failure. This supports the test examples in the brief without assuming diagnostic-specific matching. |
| A-03 | Q-06 | Retain the submitted program with its result so users can inspect it after editing the current program. This identifies the input that produced a result without requiring a complete edit history. |
| A-04 | Q-05 | Use user-requested cancellation in the first version; no automatic execution time limit is proposed at this stage. Actual termination requires confirmation from the language tools, whose cancellation support remains unresolved. This distinguishes requesting cancellation from successfully stopping execution. |
| A-05 | Q-08 | Propose visible interface feedback within 500 milliseconds for ordinary actions, assessed with programs of up to 100 lines and collections of up to 20 tests. These are proposed evaluation conditions, not input-size limits. Record the test computer, browser, and operating system; the supported configuration remains subject to Q-07. Compiler execution time is excluded. |

## 6. Functional Requirements

Each requirement describes observable system behavior. "Shall" indicates required behavior when the feature is included. Essential requirements support the core editing, execution, and testing workflow. Optional requirements support teaching or early demonstrations and may be deferred without removing the core workflow. These priorities are proposed from the brief's stated goals.

Requirements involving the language tools depend on the interface and input representation identified in Q-01 and Q-02. They specify the needed behavior without assuming that the current interpreter already provides it.

| ID | Priority | Requirement |
| --- | --- | --- |
| FR-01 | Essential | The environment shall allow users to enter, paste, and edit program content. The accepted representation remains subject to Q-02. |
| FR-02 | Essential | The environment shall allow users to load a program from a local file into the editor. Supported program files remain subject to Q-02. |
| FR-03 | Essential | The environment shall provide selectable starter examples (preprovided programs) and allow users to modify a selected example while retaining access to its original content. A user's saved edited version is distinct from that original; preserving the original shall not reset the saved edits. |
| FR-04 | Essential | The environment shall allow users to save a program and select a saved program for further editing or execution. Saving follows A-01. |
| FR-05 | Essential | The environment shall restore saved programs and test collections after a page refresh or a later session under the conditions in A-01. |
| FR-06 | Essential | On a compile-only request, the environment shall submit the current program for compilation and display success or compilation diagnostics without requesting execution. |
| FR-07 | Essential | On a run request, the environment shall submit the current program for execution through the language tools and display the returned result or failure. |
| FR-08 | Essential | The environment shall distinguish compilation errors, runtime failures, and environment failures using text labels and display the available explanation for each failure. |
| FR-09 | Essential | When a diagnostic includes a source location, the environment shall identify that location in the submitted program associated with the diagnostic. |
| FR-10 | Optional | When the compiler supplies an AST or generated code, the environment shall allow users to open and close a view of that information without requiring them to inspect it to run a program. |
| FR-11 | Essential | If the compiler cannot be reached, the environment shall report compiler unavailability, preserve the current editor content and saved work, and allow a new request after connectivity is restored. |
| FR-12 | Essential | The environment shall provide a stop action for an active execution. It shall distinguish a pending cancellation request, confirmed termination, and cancellation failure or unavailability, and shall report execution as stopped only after termination is confirmed, as proposed in A-04. |
| FR-13 | Essential | The environment shall associate each result with the program submitted for that request and allow inspection of that program. If the editor content has changed, the environment shall indicate that the result belongs to an earlier version, as proposed in A-03. |
| FR-14 | Essential | The environment shall allow users to create and edit named tests containing a program and an expected outcome: an integer value, a Boolean value, or compilation rejection, as proposed in A-02. |
| FR-15 | Essential | The environment shall allow users to save and reopen collections of named tests, preserving each test's name, program, and expected outcome under A-01. |
| FR-16 | Essential | The environment shall mark a completed test as passed only when its actual outcome matches the expected outcome under A-02. Other completed outcomes shall be marked failed; cancellation or environment failure shall be reported separately and shall not count as a pass. |
| FR-17 | Essential | The environment shall allow users to run a saved test collection. A failed test or a test whose cancellation is confirmed shall not prevent the remaining tests from running. If the compiler becomes unavailable, the environment shall identify tests that could not run and retain the collection for another attempt. |
| FR-18 | Essential | For a collection run, the environment shall display each test's status and summary counts for the displayed statuses. Users shall be able to inspect each test's expected outcome and actual result, diagnostic, or reason it did not complete. |
| FR-19 | Optional | If a demonstration using sample compiler responses is provided, the environment shall visibly label the mode and its displayed results as simulated. Simulated results shall not be presented as actual compiler execution. |

## 7. Quality Requirements

These requirements define how the environment's usability, accessibility, responsiveness, and reliability will be assessed. All are Essential because they support the brief's priorities for classroom use and dependable work. Numerical targets in A-05 and the save-failure guarantee in QR-05 are proposals, not stakeholder agreements. The checks described here are future evaluations, not completed test results.

| ID | Quality | Requirement and assessment |
| --- | --- | --- |
| QR-01 | Usability and setup | A student who has not used the environment before shall be able to follow the supplied setup instructions, open a starter example, request execution, and locate its result without assistance from the development team. Assess this on a supported configuration with the documented prerequisites installed and the language tools available; record any step requiring additional instructions. Supported configurations remain subject to Q-07. |
| QR-02 | Keyboard access | Users shall be able to edit a program, select an example or saved program, save work, request compilation or execution, request cancellation, and create and run a test collection using only the keyboard. Verify these workflows without a pointing device and check that the focused control is visibly identifiable. |
| QR-03 | Understandable messages | Error categories, execution states, and test outcomes shall remain distinguishable without color. Verify that each displayed state has a text label identifying its meaning when color cues are removed. |
| QR-04 | Responsiveness | Under A-05, typed edits shall appear, example selections shall update the editor, and run or stop requests shall show acknowledgment within 500 milliseconds of the action, including while an earlier execution is pending. Assess each action ten times and require every measurement to meet the proposed target. Acknowledgment does not imply that compilation, execution, or cancellation has completed. |
| QR-05 | Reliability of saving | If a save attempt fails, the environment shall retain the content being saved in the current session, preserve the last successfully saved version if one exists, and report the failure without indicating success. Assess this by causing a storage failure during a save and comparing the retained and previously saved content with their pre-attempt values. This guarantee does not extend to unsaved work after the session ends. |

## 8. External Interfaces and Dependencies

The following interfaces support the requirements above. They describe the information and capabilities needed at the system boundary without prescribing a framework, communication protocol, or storage technology.

| Interface or dependency | Required interaction | Related requirements and open details |
| --- | --- | --- |
| LAMBDA compilation and execution tools | Submit a program with a compile-only or run request. Receive compilation status, execution results with enough type information for test comparison, or diagnostics that distinguish compilation and runtime failures. Associate each response with its originating request and submitted program. Source locations and intermediate representations are used when supplied. | FR-06 through FR-10, FR-13, FR-16. The provider, accepted input, available operations, and response format remain unresolved in Q-01 and Q-02. This interface does not assume a separate server. |
| Execution cancellation | Direct a stop request to the active execution and receive confirmation of termination or an indication that cancellation failed or is unavailable. | FR-12, FR-17; A-04. The language tools' cancellation capability remains unresolved in Q-05. A displayed cancellation request alone does not establish that execution has stopped. |
| Local program files | Read a user-selected program file into the editor for further editing or submission. | FR-02. Supported file formats depend on the program representation in Q-02; no file extension is specified yet. |
| Persistent storage | Save and retrieve program content and test collections, including test names and expected outcomes. Report save failures so the environment can distinguish them from successful saves. | FR-04, FR-05, FR-15, QR-05; A-01. The storage technology is an implementation choice. Recovery of unsaved edits remains unresolved in Q-03. |
| Browser and local runtime | Provide the browser access and local prerequisites needed to operate the environment, with setup instructions for the supported configuration. | QR-01, QR-02, QR-04. Supported browsers, operating systems, and setup prerequisites remain unresolved in Q-07. |

If sample compiler responses are used during development, they represent the same categories of information expected from the real interface and remain visibly identified as simulated under FR-19. Their use does not demonstrate compatibility with the real tools. The environment team and compiler interface provider must resolve the integration details before real compilation, execution, and cancellation can be verified.

## 9. Acceptance Criteria

These scenarios specify future checks; none has been executed. Programs will use the representation agreed under Q-02. Compiler-dependent checks require the agreed interface; controlled responses may be used to check environment behavior, but do not establish that the real compiler is integrated. Each scenario passes only when all of its expected results are observed.

| ID and requirements | Starting conditions | Action or input | Observable expected result |
| --- | --- | --- | --- |
| AC-01: Compile and run (FR-06, FR-07) | A valid factorial program with input 5 is open, and the tools are available. | Request compilation only, then request execution separately. | The first request reports compilation success without requesting execution. The second displays the integer result 120. Inspect the requests sent to the tools to confirm the distinction. |
| AC-02: Preserve starter examples (FR-03, FR-04) | The original factorial example is available with input 5, and saving is available. | Select it, change its input to 6, and save the edited version. Then select the original example and reopen the saved version in turn. | The original contains input 5, while the saved edited version contains input 6. Both remain accessible; preserving the original neither overwrites nor resets the saved edits. |
| AC-03: Restore saved work (FR-04, FR-05, FR-15) | A program and a named test collection have been explicitly saved under A-01. The collection includes expected integer, Boolean, and compilation-rejection outcomes. | Refresh the page and reopen the saved items; then close and reopen the environment in the same browser profile and repeat. | The saved program content and every test's name, program, and expected outcome match the saved values after both operations. The program can be selected for editing. |
| AC-04: Compiler unavailable (FR-08, FR-11) | The editor contains unsaved changes, saved work exists, and the compiler is unreachable. | Request execution, then restore compiler availability and submit again. | The initial request reports compiler unavailability as an environment failure, not a program error. Editor content and saved work remain intact. The later request can complete and display its result. |
| AC-05: Cancel a nonterminating execution (FR-12) | An execution remains active and the interface can provide controlled cancellation responses. | Request a stop. First delay confirmation, then confirm termination. Repeat with a cancellation-failure response. | While confirmation is pending, the environment shows a pending request and does not claim execution has stopped. Confirmation produces a stopped status. The failure case reports cancellation failure without falsely reporting termination. |
| AC-06: Result after an edit (FR-13) | Program version A has been submitted and its response is delayed. | Change the editor to version B, then deliver A's result. | The result is identified as belonging to the earlier submitted version. Users can inspect A, and B remains in the editor. |
| AC-07: Mixed test outcomes (FR-16, FR-17, FR-18) | A saved collection has four tests: one expects integer 120 and returns 120; one expects integer 1 and returns Boolean true; one expects compilation rejection and receives it; one expects compilation rejection but has a runtime failure. | Run the collection, placing the type-mismatch test before at least one passing test. | All four tests complete. Exactly two pass and two fail under A-02. The summary matches the individual statuses, and each test exposes its expected and actual outcome. The earlier failed test does not prevent later execution. |
| AC-08: Save failure (QR-05) | Version A is successfully saved, version B is being edited, and storage can be made to reject a save. | Attempt to save B while storage rejects the operation. | A save-failure message appears without a success indication. B remains available in the current editor, and the stored version remains A. |

AC-04, AC-05, AC-07, and AC-08 include failure or exceptional conditions. The assessment procedures in Section 7 additionally cover the quality requirements; these scenarios do not replace them.

## 10. Traceability

The table maps every functional and quality requirement to the [stakeholder brief](../LAMBDA-UI-informal-requirements.md) and, where applicable, a working assumption or explicit proposal. Section names refer to the brief. No additional stakeholder answers are used as sources. Proposed details explain how this draft makes a broader need assessable; they are not presented as wording supplied by the instructor.

| Requirement | Source and basis |
| --- | --- |
| FR-01 | "Trying a program": type or paste a program and modify its input. The input representation remains open under Q-02. |
| FR-02 | "Trying a program": use programs already saved in files without retyping them. |
| FR-03 | "Trying a program": provide examples, preserve access to originals when examples are modified, and keep written programs for later use. The distinction between the original and saved edits combines these needs without prescribing a copying mechanism. |
| FR-04 | "Trying a program": keep a written program and return to it later; A-01 proposes explicit saving. |
| FR-05 | "Keeping examples as tests": retain prepared examples across refreshes and sessions; A-01 defines the proposed persistence conditions. |
| FR-06 | "Trying a program": check whether a program compiles without running it. |
| FR-07 | "Trying a program": run a program and see its answer. |
| FR-08 | "Understanding what happened": provide useful explanations and distinguish compilation, runtime, and environment failures; "Keeping the project manageable": messages must not depend only on color. |
| FR-09 | "Understanding what happened": help locate a source problem when the compiler supplies its location. |
| FR-10 | "Trying a program": inspect available ASTs or generated code without obstructing simple execution. Making the view optional to open is this draft's interpretation of that need. |
| FR-11 | "Understanding what happened": identify compiler unavailability, preserve work, and allow another attempt after recovery. |
| FR-12 | "Understanding what happened": stop a long-running or nonterminating program; A-04 proposes the cancellation policy and confirmation requirement. |
| FR-13 | "Understanding what happened": identify which program version produced a result after an edit; A-03 proposes retaining the submitted program for inspection. |
| FR-14 | "Keeping examples as tests": maintain named programs with expected values or expected compilation errors; A-02 proposes the initial outcome types. |
| FR-15 | "Keeping examples as tests": retain test collections for later sessions; A-01 proposes explicit saving and reopening. |
| FR-16 | "Keeping examples as tests": determine whether tests behave as expected; A-02 defines matching. "Understanding what happened" supports distinguishing environment failures from program outcomes. |
| FR-17 | "Keeping examples as tests": rerun collections without one troublesome test making the rest unusable; "Understanding what happened": retry after compiler recovery; A-04 governs cancellation. |
| FR-18 | "Keeping examples as tests": provide a quick summary and details for investigating unexpected outcomes. Summary counts are a proposed presentation of that summary. |
| FR-19 | "The compiler is still evolving": allow sample responses for demonstrations while ensuring they cannot be mistaken for actual compilation results. |
| QR-01 | Brief introduction: support users unfamiliar with the compiler; "Keeping the project manageable": another person should be able to follow setup instructions. The independent setup-and-run exercise is a proposed assessment. |
| QR-02 | "Keeping the project manageable": support main tasks with a keyboard. Visible focus is a proposed condition for assessing usable keyboard navigation. |

## 11. Review Notes

The requirements were reviewed for ambiguity, contradictions, and verifiability. The following issues were found and resolved.

1. Initial draft risk: "compiler output and run results" were not clearly separated. This was addressed by requiring explicit distinction between compile-time failure and runtime failure in FR-08 and by creating separate acceptance checks for both.
2. Initial draft risk: "a few examples" and "keep examples as tests" could be confused. The final specification separates sample programs for learning from saved test collections for regression checks, clarifying different purposes in FR-03 and FR-14.
3. Initial draft risk: "results remain available" could be interpreted as a guarantee of exact consistency after interrupts. This was resolved by adding FR-13 so that result provenance is associated with the right program version rather than assuming all results remain equally valid.
4. Initial draft risk: "not all detail should get in the way" was vague. This was converted into a requirement for optional detail views and concise default presentation in FR-10 and QR-03.
5. Initial draft risk: "compiler is still evolving" could lead to over-specifying a single implementation. The requirements therefore state a stable interface contract rather than a fixed technology choice.

## 12. Conclusion

This specification defines a first version of a local, browser-based LAMBDA testing environment. It preserves the teaching and testing needs described in the stakeholder brief while keeping scope manageable. The requirements emphasize clarity, separable responsibilities between the UI and the compiler, and the ability to work even before the real compiler is complete.
