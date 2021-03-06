# Workflow API version
apiVersion: io.orquestra.workflow/1.0.0

# Prefix for workflow ID
name: dingo8

imports:
- name: isingdata
  type: git
  parameters:
    repository: "git@github.com:kottmanj/isingdata.git"
    branch: "master"

steps:
{% set steps = 1 %}
{% set n_qubits = 4 %}
{% set n_circuits = 10 %}
{% set n_trials = 10 %}
{% for n in range(0, steps, 1) %}
- name: ising-{{n}}
  config:
    runtime:
      language: python3
      imports: [isingdata]
      parameters:
        file: isingdata/steps/run.py
        function: run_ising_circuits
  inputs:
    - n_qubits: {{n_qubits}}
      type: int
    - n_circuits: {{n_circuits}}
      type: int
    - n_trials: {{n_trials}}
      type: int
    - generators: '["XY", "Y"]'
      type: string
    - fix_angles: '{"XY": 1.5707963267948966}'
      type: string
    - fix_mean_field: True
      type: bool
    - only_samples: True
      type: bool
  outputs:
    - name: isingdata
      type: isingdata
{% endfor %}

types:
  - isingdata

