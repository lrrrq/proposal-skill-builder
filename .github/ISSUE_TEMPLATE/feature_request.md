name: Feature request
about: Suggest a new command, flag, or workflow
title: "[feat] "
labels: ["enhancement"]
body:
  - type: textarea
    id: problem
    attributes:
      label: What problem does this solve?
      description: |
        Explain the workflow that's awkward today. Example: "I want to
        re-build all skills from `compiled/cases/case_0xxx/` but
        `batch-compile` only goes through uncompiled files."
    validations:
      required: true

  - type: textarea
    id: proposed
    attributes:
      label: Proposed solution
      description: |
        Sketch the CLI shape (`python -m skill_builder.cli new-command
        --flag value`) or describe the new behavior.
      placeholder: |
        ```bash
        python -m skill_builder.cli rebuild-all --source compiled/cases --out skills/draft
        ```
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      description: Optional — what else did you try, and why is this better?

  - type: textarea
    id: context
    attributes:
      label: Anything else?
      description: |
        Screenshots, links to example proposals, similar tools, etc.