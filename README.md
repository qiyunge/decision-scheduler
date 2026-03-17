# Decision Engine for Task Scheduling  
*A simulation-based decision system where data structures encode structural constraints, algorithms maintain process invariants, and policies implement decision invariants.*

This project implements a decision-oriented scheduling engine designed to study how system behavior emerges from the interaction between data structures, algorithms, and decision policies.

Unlike traditional task managers, this system models scheduling as a **state-transition process** governed by constraints and decision rules, and evaluates outcomes through simulation metrics.

---

## Project Positioning

This is not a CRUD application or a simple OOP exercise.

It is a:

- decision engine  
- scheduling simulator  
- system-design portfolio project  

The goal is to demonstrate:

- object-oriented modeling  
- data-structure-driven constraints  
- algorithmic state transitions  
- policy-based decision making  
- simulation-based evaluation  

---

## Core Concept: Three Levels of Invariants

The system operates under three complementary invariant layers.

### 1. Structural Invariants (Data Structures)

Encoded by the system’s underlying data structures:

- dependency graph remains acyclic  
- priority queue ordering is preserved  
- resource capacity representation remains consistent  

These ensure the **structural correctness** of the system.

---

### 2. Process Invariants (Algorithms)

Maintained dynamically during execution:

- no resource overallocation  
- dependency satisfaction before scheduling  
- schedule state remains valid  

These ensure the **operational correctness** of the system.

---

### 3. Decision Invariants (Policies)

Defined by decision policies guiding system behavior:

- FIFO → arrival order consistency  
- SPT → shortest processing priority  
- EDD → deadline adherence  

These ensure the system’s decisions remain aligned with its **objectives and trade-offs**.

---

## System Architecture

src/
app/ # structural placeholder (no UI implemented)
core/
domain/ # tasks, resources, dependencies, invariants
policies/ # decision invariants (FIFO, SPT, EDD)
planning/ # feasibility + allocation + state transition
simulation/ # event loop and system evolution
metrics/ # evaluation metrics and experiment outputs
infra/
persistence/ # optional outputs
storage/ # optional data loading
shared/
utils/


---

## Domain Model

Key entities:

- Task  
- Resource  
- Dependency  
- Schedule  

Key properties:

- processing time  
- deadlines  
- precedence relations  
- resource constraints  

---

## Decision Policies

Policies represent **decision invariants implemented as executable rules**.

They do not modify system state; they select tasks based on system objectives.

Examples:

- FIFO (First-In-First-Out)  
- SPT (Shortest Processing Time)  
- EDD (Earliest Due Date)  

Interface idea:

select_next(ready_tasks, current_time) -> Task

---

## Planning Layer

Responsible for transforming decisions into executable system state transitions:

- feasibility checks  
- resource allocation  
- schedule update  
- dependency update  

---

## Simulation Engine

The simulation models scheduling as a state-evolving process:

initialize system state

while tasks remain:
update ready task set
policy selects next task
planning allocates resources
update system state
advance time
record execution trace

compute metrics


---

## Metrics

Evaluation focuses on decision effectiveness rather than implementation details.

Possible metrics:

- makespan  
- average waiting time  
- tardiness  
- resource utilization  
- throughput  
- fairness  

---

## Data-Structure-Driven Behavior

System behavior is shaped by structural design choices:

- priority queue → scheduling order  
- DAG → dependency management  
- resource pool → allocation feasibility  
- event queue → time progression  

These structures encode the system’s **structural invariants**.

---

## Project Goals

This project aims to:

- demonstrate how scheduling can be framed as a decision problem  
- explore the interaction between structure, algorithm, and policy  
- build a reusable simulation core for future experimentation  

---

## Non-Goals

- no full UI implementation  
- no CRUD-style task manager features  
- no machine learning required in the initial version  

---

## Future Extensions

- stochastic processing time  
- reinforcement-learning-based policy  
- multi-resource scheduling  
- distributed simulation  
- robustness testing  

---

## Author

Qiyun Ge

---

## Tagline

**Data structures encode constraints.  
Algorithms maintain system validity.  
Policies define decisions.  
Simulation reveals behavior.**
