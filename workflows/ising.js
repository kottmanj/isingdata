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
{% set steps = 10 %}
{% set n_qubits = 8 %}
{% set n_circuits = 5 %}
{% set n_trials = 3 %}
{% for n in range(0, steps, 1) %}
- name: ising-{{n}}
  config:
    runtime:
      language: python3
      imports: [isingdata]
      parameters:
        file: isingdata/steps/run.py
        function: run_ising_circuits
      resources:
      cpu: "1000m"
      memory: "1Gi"
      disk: "5Gi"
  inputs:
    - n_qubits: {{n_qubits}}
      type: int
    - n_circuits: {{n_circuits}}
      type: int
    - n_trials: {{n_trials}}
      type: int
  outputs:
    - name: isingdata
      type: isingdata
{% endfor %}

types:
  - isingdata

