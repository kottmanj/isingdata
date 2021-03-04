# Orquestra Workflow for the Simplified Ising Model

- For manual run: Install this package and use the `run_ising_circuits` function in [steps/run.py](steps/run.py)
- Example workflow template in [workflows](workflows/ising.js)

## Construct the worflow from the template:
- adapt [template](workflows/ising.js) file
- compile to workflow (you need `pip install jinja2-cli` for this)  
```bash
jinja2 ising.js -o workflow.yaml
```

## Run workflow
- you need the quantum-engine from Zapata (Orquestra interface)
```bash
qe submit workflow workflow.yaml
```
This gives back the workflow ID (keep it)

## Get status
```bash
qe get workflow ID
```

## Get results
```bash
qe get workflowresult ID
```

## Analyze results
- download, extract and run [analyze\_workflow.py](steps/analyze_workflow.py)
 
