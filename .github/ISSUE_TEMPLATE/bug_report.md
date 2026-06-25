name: Bug report
about: Report incorrect behavior or a crash
title: "[bug] "
labels: ["bug"]
assignees: []
body:
  - type: markdown
    attributes:
      value: |
        Thanks for filing a bug. Please fill in as much as you can — the
        `skill_builder status` output and a minimal repro go a long way.

  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      placeholder: |
        Run `python -m skill_builder.cli <command>` and saw X. Expected Y.
    validations:
      required: true

  - type: textarea
    id: repro
    attributes:
      label: Steps to reproduce
      placeholder: |
        1. `python -m skill_builder.cli init`
        2. `python -m skill_builder.cli intake`
        3. ...
    validations:
      required: true

  - type: textarea
    id: env
    attributes:
      label: Environment
      placeholder: |
        - OS: macOS 14.5 / Ubuntu 24.04 / Windows 11
        - Python: 3.11.7 (run `python --version`)
        - skill_builder version: 0.3.0 (run `python -m skill_builder.cli status`)
        - Output of `python -m skill_builder.cli status`:
          ```
          (paste here)
          ```
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Relevant logs / error messages
      placeholder: |
        ```
        Traceback (most recent call last):
          ...
        ```
      render: shell