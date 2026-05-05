# Parallel-DEVS Algorithms

## Introduction to the Parallel-DEVS Simulation Hierarchy

In the Parallel-DEVS (P-DEVS) formalism, the simulation architecture is organized into a **hierarchical structure** consisting of three main types of simulation entities: the **Root Coordinator**, the **Coordinator**, and the **Simulator**. Each of these elements plays a specific role in orchestrating and executing the dynamics of models, and each is directly associated with a type of DEVS model—either **coupled** or **atomic**.

### Root Coordinator

The **Root Coordinator** serves as the entry point of the simulation. Its primary role is to manage the execution of the **top-level coupled model** by delegating all simulation tasks to the corresponding **top-level coordinator**. It maintains the global simulation time and controls the overall simulation loop, ensuring that the simulation progresses until a specified maximum time. The Root Coordinator itself does not handle event dispatching; this responsibility is delegated to the coordinators associated with coupled models.

### Coordinator

A **Coordinator** is associated with a **coupled model** and is responsible for managing the interactions among its child models, which may be atomic or further coupled. Its tasks include:

* Computing outputs of imminent child models at each scheduled event time.
* Dispatching events to child models according to the coupling structure.
* Advancing the state of each child model by applying internal, external, or confluent transitions as appropriate.

Coordinators therefore act as the bridge between the abstract coupled model and the concrete simulation of its components, recursively managing nested coupled structures.

### Simulator

A **Simulator** is associated with an **atomic model** and encapsulates its state and transition logic. It is responsible for:

* Initializing the atomic model and scheduling its first event.
* Computing outputs via the atomic model's output function.
* Handling internal, external, and confluent transitions according to the DEVS formalism.
* Communicating events to its parent coordinator for further propagation.

Simulators provide the execution engine for atomic models, translating their theoretical DEVS behavior into discrete simulation events.

---

## Parallel-DEVS Algorithms

Below are the formal algorithms for the **Root Coordinator**, **Coordinator**, and **Simulator** in the Parallel-DEVS abstract simulator.

### **Root Coordinator**

```text
// ===========================
// Root Coordinator – start
// ===========================

// When receiving (START, t):
//   Initialize the simulation by forwarding the start message to the top-level child.
send (START, 0) to child

// Main simulation loop:
// Continue executing as long as the next time advance tn is less than the simulation horizon.
while (tN_child ≠ ∞) do

    // Compute the output of all models at the global next event time.
    send (OUTPUT, tN_child) to child

    // Apply the transition function of all models at time tN_child.
    // φ denotes the external input received at this time (if any).
    send (TRANSITION, tN_child, φ) to child

end while
```

### **Coordinator**

#### **Coordinator: start**

```text
// =================================
// Coordinator – start (i-message)
// =================================

// When receiving an i-message (i, t) at time t:
for each child d ∈ D do
    // Initialize each child simulator or sub-coordinator
    send (i-message) to child d
end for

// Sort the event list according to each child's next scheduled internal time tn,d.
sort event-list by tn,d

// Update last-event time and compute the earliest next event.
tl ← t
tn ← min{ tn,d | d ∈ D }
```

#### **Coordinator: output**

```text
// ============================================
// Coordinator – output (*-message)
// ============================================

// When receiving a *-message (*, t):
if t ≠ tn then
    Error   // Output message received at an incorrect time
end if

// Identify all imminent models (those whose next event time equals tn)
IMM = { d | (d, tn,d) ∈ event-list AND tn,d = tn }

// Forward the *-message to each imminent child.
for each r ∈ IMM do
    send (*, t) to r
end for
```

#### **Coordinator: transition**

```text
// ==================================================
// Coordinator – transition (x-message)
// ==================================================

// When receiving an x-message (x, t):
if NOT (tl ≤ t ≤ tn) then
    Error   // Events must occur within the correct time window
end if

// Determine which children should receive the input x,
// based on the coupling structure and the translation function Z.
receivers = { r | r ∈ children AND N ∈ Ir AND Z(N, r)(x) ≠ empty }

// Propagate translated input to all determined receivers.
for each r ∈ receivers do
    send x-message( Z(N, r)(x), t ) to r
end for

// For imminent models not in the receiver set, send empty input.
for each r ∈ IMM AND r ∉ receivers do
    send x-message( empty, t ) to r
end for

// Update event list after children complete their transitions.
sort event-list by tn,d

// Update local simulation times.
tl ← t
tn ← min{ tn,d | d ∈ D }
```

### **Simulator**

#### **Simulator: start**

```text
// =============================
// Simulator – start (i-message)
// =============================

// When receiving an i-message at time t:
tl = t - e            // e is elapsed time (often 0 at initialization)
tn = tl + ta(s)       // Schedule next internal transition
```

#### **Simulator: output**

```text
// =================================
// Simulator – output (*-message)
// =================================

// When receiving a *-message at time t:
if t = tn then
    y = lambda(s)                   // Compute the model's output
    send y-message(y, t) to parent  // Send result to its coordinator
end if
```

#### **Simulator: transition**

```text
// =========================================
// Simulator – transition (x-message)
// =========================================

// When receiving an x-message (x, t):

if (x is empty AND t = tn) then
    // Internal transition: no external event
    s = delta_int(s)

else if (x is not empty AND t = tn) then
    // Confluent transition: internal and external coincide
    s = delta_conf(s, x)

else if (x is not empty AND t < tn) then
    // External transition: interrupt before scheduled internal event
    e = t - tl              // elapsed time since last event
    s = delta_ext(s, e, x)

end if

// Schedule next internal transition
tn = t + ta(s)

// Update last-event time
tl = t
```

## Variables and Notation

| Variable                   | Description                                                                  |
|----------------------------|------------------------------------------------------------------------------|
| $D$                        | Set of models (atomic or coupled).                                           |
| $S_\text{root}$            | State of the Root Coordinator (its top-level coordinator).                   |
| $s_d$                      | State of model $d \in D$ (atomic or coupled).                                |
| $t_l$                      | Last event time of a coordinator or simulator.                               |
| $t_n$                      | Next scheduled internal event time of a coordinator or simulator.            |
| $t_{n,d}$                  | Next scheduled event time of child $d$.                                      |
| $t_\text{max}$             | Maximum simulation time.                                                     |
| $\text{IMM}$               | Imminent models at current time $t_n$ ($t_{n,d} = t_n$).                     |
| $\lambda_d(s_d)$           | Output function of model $d$.                                                |
| $\delta_\text{int}(s)$     | Internal transition function of an atomic model.                             |
| $\delta_\text{ext}(s,e,x)$ | External transition function with elapsed time $e$ and input $x$.            |
| $\delta_\text{conf}(s,x)$  | Confluent transition function for simultaneous internal and external events. |
| $\text{ta}(s)$             | Time advance function of an atomic model.                                    |
| $Z$                        | Coupling function of a coupled model.                                        |

## Simulator (Atomic Model)

**State:**

$$
S_d = s, \quad t_l, t_n
$$

**Link:**

$$
\text{Simulator} \longleftrightarrow \text{Atomic Model}
$$

**Start (i-message):**

$$
s \gets s_0, \quad t_l \gets t
$$

$$
t_n \gets t_l + \text{ta}(s)
$$

**Output ($*$-message):**

$$
\text{if } t = t_n \text{ then } y \gets \lambda(s)
$$

**Event Dispatching:**

$$
\text{Send } y \text{ to parent coordinator}
$$

**Transition (x-message):**

$$
s \gets
\begin{cases}
\delta_\text{int}(s), & t = t_n \text{ and no input} \\
\delta_\text{conf}(s, x), & t = t_n \text{ and input exists} \\
\delta_\text{ext}(s, t - t_l, x), & t < t_n \text{ and input exists}
\end{cases}
$$

$$
t_l \gets t, \quad t_n \gets t_l + \text{ta}(s)
$$

**Key Notes:**

1. Simulator ↔ atomic model, handles internal, external, and confluent transitions.
2. Event order for simulators:

$$
\text{Output} \rightarrow \text{Dispatch} \rightarrow \text{Transition}
$$

---

# A Comprehensive Guide to FPDEVSML Elements — Atomic Models

## Preamble

### Comments (`#`)

FPDEVSML supports **inline comments** using the `#` symbol.
Comments are **ignored by the parser** and serve purely as documentation or annotation within a model file.

**Syntax**

```fpdevsml
# This is a comment
```

* Everything following the `#` symbol on the same line is treated as a comment.
* Comments **cannot span multiple lines** — to comment multiple lines, prefix each line with `#`.

**Placement**

Comments can appear:

* **On a separate line**, before or after a statement.
* **At the end of a line**, following an expression, rule, or declaration.

**Examples**

**Example 1 — Standalone Comment**

```fpdevsml
# Internal transition for active state
(active, count) → (passive, _)
| count < 10;
```

**Example 2 — Inline Comment**

```fpdevsml
(active, count) → (passive, 0);  # Reset counter when reaching 10
```

**Example 3 — In Section Headers**

```fpdevsml
delta_int: {   # Internal transition function
    (phase, sigma) → (next_phase, 0);
}
```

**Semantics**

* Comments are **purely lexical** — they do not affect parsing or model execution.
* They can be inserted anywhere a line break is valid.
* Whitespace before or after the `#` is optional.

## Core Concepts

### Preconditions: Quantifiers and Guards

After the `pre-state` pattern is matched, the rule's applicability is further checked by optional quantifiers and a final guard. These are the rule's preconditions.

#### Quantifiers (`∀`, `∃`, `∄`)

Quantifiers are logical preconditions used when a rule's logic depends on inspecting the contents of a state collection (`set`, `array`, or `map`).

##### `∀` (For All)

* **Syntax:** `∀ var ∈ collection / predicate`
* **Logic:** Checks if **all** elements (`var`) in the `collection` satisfy the `predicate`.
* **Example (using projection):**
  `(...) → (...) ∀ slot ∈ buffer / π_1(slot) == FULL;`
* **Meaning:**
  This expression checks if *every* element (named `slot`) in the `buffer` collection satisfies the predicate. The predicate uses the **projection function `π_1`** to access the **first attribute** of the `slot` tuple and compares it to `FULL`.

##### `∃` (Exists)

* **Syntax:** `∃ var ∈ collection | predicate`
* **Logic:** Checks if **at least one** element (`var`) in the `collection` satisfies the `predicate`. If the predicate is omitted, it simply checks if the collection is non-empty.

* **Example 1 (using projection):**
  `(...) → (...) ∃ job ∈ job_queue | π_1(job) == HIGH;`
* **Meaning 1:**
  This checks if there is *at least one* element (named `job`) in the `job_queue` collection where its **first attribute** (accessed via `π_1`) is equal to `HIGH`.

* **Example 2 (without projection):**
  `(...) → (...) ∃ job ∈ job_queue;`
* **Meaning 2:**
  This checks only if the `job_queue` collection is *not empty*.

##### `∄` (Does Not Exist)

* **Syntax:** `∄ var ∈ collection | predicate`
* **Logic:** Checks if **no** element (`var`) in the `collection` satisfies the `predicate`.

* **Example 1 (using projection):**
  `(...) → (...) ∄ sensor ∈ sensor_list | ¬π_1(sensor);`
* **Meaning 1:**
  This checks that *no* element (named `sensor`) in the `sensor_list` collection has its **first attribute** (accessed via `π_1`) set to `false`.

* **Example 2 (without projection):**
  `(...) → (...) ∄ sensor ∈ sensor_list;`
* **Meaning 2:**
  This checks if the `sensor_list` collection is *empty*.

#### Guard (`|`)

The **Guard** is a final boolean check applied to a transition rule. It is evaluated *after* any quantifiers have been resolved. The transition rule is only considered valid (applicable) if this `boolean_expression` evaluates to `true`.

* **Syntax:** `| boolean_expression`
* **Semantic:** The rule is selected **only if** this expression is `true`. The expression can use state variables, parameters, and standard logical connectors.

##### Examples of Guard Expressions

* **Example 1 (Simple Comparison):**
  `(...) → (...) | count < max_capacity;`

* **Example 2 (Logical AND `∧`):**
  `(...) → (...) | (status == IDLE) ∧ (job_queue_size > 0);`

* **Example 3 (Logical OR `∨`):**
  `(...) → (...) | (priority == HIGH) ∨ is_urgent;`

* **Example 4 (Logical NOT `¬`):**
  `(...) → (...) | ¬(is_full);`

* **Example 5 (Combined Expression):**
  `(...) → (...) | ( (current_load > 0) ∧ ¬(is_locked) ) ∨ is_admin_request;`

#### Rule Evaluation Order: Pattern → Quantifiers → Guard → Order

In FPDEVSML, a transition rule is evaluated in a **strict, deterministic sequence**:

1. **Pattern Matching** — the pre-state pattern is matched against the current state `S`.
2. **Quantifier Evaluation** — any quantifiers (`∀`, `∃`, `∄`) are evaluated.
3. **Guard Evaluation** — the guard (`| boolean_expression`) is checked last.
4. **Order Resolution** — if multiple events could trigger the rule, the `order` section defines the processing sequence.

**Example**

```fpdevsml
delta_ext: {
    behavior: {
        (WAIT, jobs), e, (in_job, (incoming_jobs)) → (WAIT, [j] ∪ jobs)
        ∀ j ∈ incoming_jobs / π_2(j) > 0
        | |jobs| > 0;
    }
    order: {
        (in_job, (j_a)) < (in_job, (j_b)) <=> π_1(j_a) < π_1(j_b);
    }
}
```

### Catalog of Domain Types

#### Simple & Predefined Domains

##### `predefined set`

| Domain | Meaning                                  |
|:-------|:-----------------------------------------|
| `R`    | All real numbers                         |
| `R+`   | Non-negative real numbers (`x ≥ 0`)      |
| `R-`   | Non-positive real numbers (`x ≤ 0`)      |
| `R*`   | Non-zero real numbers (`x ≠ 0`)          |
| `R+*`  | Positive non-zero real numbers (`x > 0`) |
| `R-*`  | Negative non-zero real numbers (`x < 0`) |
| `N`    | Natural numbers (`0, 1, 2, …`)           |
| `N*`   | Positive natural numbers (`1, 2, 3, …`)  |
| `Z`    | Integers (`…, -2, -1, 0, 1, 2, …`)       |
| `Z+`   | Non-negative integers (`x ≥ 0`)          |
| `Z-`   | Non-positive integers (`x ≤ 0`)          |
| `Z*`   | Non-zero integers (`x ≠ 0`)              |
| `Z+*`  | Positive non-zero integers (`x > 0`)     |
| `Z-*`  | Negative non-zero integers (`x < 0`)     |
| `B`    | Boolean values (`⊤`, `⊥`)                |
| `Q`    | Rational numbers (`p/q`)                 |
| `C`    | Complex numbers (`<a, b>`)               |

##### `symbol set`

An enumeration type used to define qualitative or categorical states.

* **Syntax:** `<symbol_1, symbol_2, ...>`
* **Usage Example:** `phase ∈ <idle, busy, processing>`

#### Structured (Complex) Domains

* **`set`** — An **unordered collection** of elements, no duplicates.
  * **Syntax:** `{ domain_element }`
  * **Usage:** `my_set ∈ { N }`

* **`array`** — An **ordered collection**.
  * Fixed-size: `[ domain_element @ size ]`
  * Variable-size: `[ domain_element ]`

* **`map`** — A **key-value structure** (dictionary).
  * **Syntax:** `≪ Key_Domain → Value_Domain ≫`
  * **Usage:** `routing_table ∈ ≪ (id) ∈ (N) → (port) ∈ (N) ≫`

* **`tuple`** — A structured **n-tuple**.
  * **Syntax:** `(name1, ...) ∈ (Domain1, ...)`

#### Composition Examples

**Fixed-Size Array of Tuples**

```fpdevsml
S: (job_queue) ∈ ([ (id, prio) ∈ (N, N) @ 5 ]) = ([(0,0), (0,0), (0,0), (0,0), (0,0)]);
```

**Variable-Size Array of Tuples**

```fpdevsml
S: (task_list) ∈ ([ (id, prio) ∈ (N, N) ]) = (∅);
```

**Set of Tuples**

```fpdevsml
S: (connections) ∈ ({ (ip, port) ∈ (N, N) }) = (∅);
```

### Expression Syntax and Typing Rules

#### Operators

##### Arithmetic

| Operator | Meaning        |
|----------|----------------|
| `+`      | Addition       |
| `-`      | Subtraction    |
| `*`      | Multiplication |
| `/`      | Division       |

##### Comparison

| Operator | Meaning               |
|----------|-----------------------|
| `=`      | Equality              |
| `≠`      | Inequality            |
| `<`      | Strict less-than      |
| `≤`      | Less-than or equal    |
| `>`      | Strict greater-than   |
| `≥`      | Greater-than or equal |

##### Logical

| Operator | Meaning |
|----------|---------|
| `¬`      | NOT     |
| `∧`      | AND     |
| `∨`      | OR      |

##### Collection Operators

| Operator | Meaning                                         |
|----------|-------------------------------------------------|
| `∪`      | Union / concatenation (collection → collection) |
| `∖`      | Difference (collection → collection)            |
| `\|X\|`  | Cardinality of set or array (output type: N)    |

##### Tuple Projection

```
π_i(expr)
```

Returns the i-th field of a tuple (1-based index).

##### Map Access

```
≪ map_expr : key_expr ≫
```

#### Comprehensions

For arrays: `Operator[ var ∈ collection ]( expr )`  
For sets: `Operator{ var ∈ collection }( expr )`

| Operator | Output                            |
|----------|-----------------------------------|
| `map`    | set or array (same size as input) |
| `max`    | numeric                           |
| `min`    | numeric                           |
| `∑`      | numeric sum                       |
| `∏`      | numeric product                   |

#### Operator Precedence (highest → lowest)

1. Tuple projection: `π_i(expr)`
2. Unary: `¬`, unary `-`
3. Multiplicative: `*`, `/`
4. Additive: `+`, `-`
5. Comparison: `<`, `≤`, `>`, `≥`, `=`, `≠`
6. Logical AND: `∧`
7. Logical OR: `∨`
8. Collection operators: `∪`, `∖`

### Special Symbols and Literals

#### `_` — Wildcard / "Don't Care"

Matches any value without binding a variable. Used in pattern matching only.

```fpdevsml
(active, sigma, _) → (waiting, sigma, _);
[h | _]    # ignore the tail
[ _ | t ]  # ignore the head
```

#### `∅` — Empty Collection

Represents the empty set, empty array, or empty map.

```fpdevsml
S: (job_queue) ∈ ([ (id, duration) ∈ (N, R+) ]) = (∅);
```

#### `+∞` / `-∞` — Infinity Literals

Used primarily in time advance functions.

```fpdevsml
ta: {
    (PASSIVE, _) → +∞;
    (ACTIVE, _) → 0;
}
```

#### `⊤` / `⊥` — Boolean Constants

```fpdevsml
S: (is_active) ∈ (B) = (⊥);
```

### Array Manipulation

#### Union (`∪`) and Difference (`∖`)

* **Prepend:** `[ element ] ∪ collection`
* **Append:** `collection ∪ [ element ]`
* **Remove:** `collection ∖ [ element ]`

#### Pattern Matching (Head/Tail)

* `[H | T]` — binds `H` to the first element, `T` to the rest.
* `[H $ T]` — binds `H` to all but the last element, `T` to the last.

```fpdevsml
(sigma, [job | next_jobs], _) → (sigma, next_jobs, job);
(sigma, [prefix $ last_job], current) → (sigma, prefix, last_job);
(ACTIVE, ∅) → (PASSIVE, +∞);
```

### Map Operations

#### Map Union

```fpdevsml
routing_table ∪ ≪ dest_id , next_hop ≫
```

#### Map Difference

```fpdevsml
active_jobs ∖ ≪ job_id , _ ≫
```

#### Map Access

```fpdevsml
≪ durations : (2, 1) ≫
```

#### Iterating Over Maps

```fpdevsml
∀ (sid, (st, val)) ∈ sensor_map / st = OK ∧ val ≥ 0.0;
```

### Array Indexing

```fpdevsml
[buffer : 2]          # second element
π_2([jobs : 3])       # second field of third element
```

### Range Iteration

```fpdevsml
∀ i ∈ {0 ... N-1} / condition;
∀ i ∈ [1 ... 10];
∀ (i, j) ∈ ({0 ... N-1}, {0 ... M-1});
```

### Modulo Operator (`%`)

```fpdevsml
(...) → (...) | (counter % 5 = 0);
```

### Numerical Functions

| Function       | Description                          |
|----------------|--------------------------------------|
| `sin(expr)`    | Sine (radians)                       |
| `cos(expr)`    | Cosine (radians)                     |
| `tan(expr)`    | Tangent (radians)                    |
| `exp(expr)`    | Exponential $e^x$                    |
| `ln(expr)`     | Natural logarithm                    |
| `log10(expr)`  | Base-10 logarithm                    |
| `log2(expr)`   | Base-2 logarithm                     |
| `sqrt(expr)`   | Square root                          |
| `abs(expr)`    | Absolute value                       |
| `inv(expr)`    | Multiplicative inverse (`1/expr`)    |
| `sinh(expr)`   | Hyperbolic sine                      |
| `cosh(expr)`   | Hyperbolic cosine                    |
| `tanh(expr)`   | Hyperbolic tangent                   |

---

## Atomic Models

An atomic model defines the indivisible behavior of a system component. It includes the following sections:

**Mandatory:**
* **`ta:`** — Time Advance Function

**Optional:**
* **`P:`** — Parameters
* **`S:`** — State Variables
* **`X:`** — Input Ports
* **`Y:`** — Output Ports
* **`delta_int:`** — Internal Transition
* **`delta_ext:`** — External Transition
* **`delta_con:`** — Confluent Transition
* **`lambda:`** — Output Function
* **`obs:`** — Observations

### Atomic Model Structure

```ebnf
atomic_model =
    identifier, "{",
        [section_parameters],
        [section_state],
        [section_in_ports],
        [section_out_ports],
        [section_delta_int],
        [section_delta_ext],
        [section_delta_con],
        section_ta,
        [section_output],
        [section_observations],
    "}" ;
```

| Section                   | Keyword      | Required     | Description                                                          |
|:--------------------------|:-------------|:-------------|:---------------------------------------------------------------------|
| **Parameters**            | `P:`         | Optional     | Declares constant parameters (static configuration).                |
| **State Variables**       | `S:`         | Optional     | Declares the dynamic state variables.                               |
| **Input Ports**           | `X:`         | Optional     | Defines the set of input ports and their data domains.              |
| **Output Ports**          | `Y:`         | Optional     | Defines the set of output ports and their data domains.             |
| **Internal Transition**   | `delta_int:` | Optional     | Describes transitions triggered by internal events.                 |
| **External Transition**   | `delta_ext:` | Optional     | Describes transitions triggered by input events.                    |
| **Confluent Transition**  | `delta_con:` | Optional     | Defines behavior when internal and external events are simultaneous.|
| **Time Advance Function** | `ta:`        | **Required** | Defines the time until the next internal event.                     |
| **Output Function**       | `lambda:`    | Optional     | Defines the output behavior before internal transitions.            |
| **Observation Section**   | `obs:`       | Optional     | Exposes internal variables for observation or debugging.            |

### `S:` (State)

The state section is always an n-tuple:

```fpdevsml
S: (var_1, ..., var_n) ∈ (Domain_1, ..., Domain_n) = (Initial_1, ..., Initial_n);
```

### `P:` (Parameters)

Parameters are static, read-only values set at initialization:

```fpdevsml
P: (param_1, ..., param_n) ∈ (Domain_1, ..., Domain_n) = (Default_1, ..., Default_n);
```

**Examples:**

```fpdevsml
P: (duration, limit) ∈ (R, N) = (10.0, 9999);

P: (routing_table) ∈ (≪ (dest_id) ∈ (N) → (port_id) ∈ (N) ≫) = ( ≪ (100, 1), (200, 2) ≫ );

P: (weights) ∈ ([ R @ 5 ]) = ( [0.0, 0.0, 0.0, 0.0, 0.0] );
```

### `X:` (Input Ports) and `Y:` (Output Ports)

#### Single Port Definition

```fpdevsml
(port_name, (var_1, ...)) | (Domain_1, ...)
```

#### Multi-Port (Port Array) Definition

```fpdevsml
(port_name * expression, (var_1, ...)) | (Domain_1, ...)
```

**Example:**

```fpdevsml
X: {
  (in_start, ()) | ();
  (in_channel * N, (data)) | ([N]);
  (in_task, (id, priority)) | (N, N);
}

Y: {
  (out_done, (result)) | (B);
  (out_channel * N, (data)) | ([N]);
}
```

### `delta_int:` (Internal Transition Function)

Triggered when the model's internal timer (`ta(s)`) expires.

#### Simple Block (First-Match-Wins)

```fpdevsml
delta_int: {
  (pre_1) → (post_1); [quant_1;] [| guard_1;]
  (pre_2) → (post_2); [quant_2;] [| guard_2;]
}
```

#### Complex (Multi-Block / Sequential Composition)

```fpdevsml
delta_int: {
  {
    (pre_1_1) → (post_1_1); [q_1_1;] [| g_1_1;]
  } [BLOCK_1_quantifiers;] [| BLOCK_1_guard;]

  {
    (pre_2_1) → (post_2_1); [q_2_1;] [| g_2_1;]
  } [BLOCK_2_quantifiers;] [| BLOCK_2_guard;]
}
```

**Examples:**

```fpdevsml
# Pattern matching with guard
delta_int: {
    (WAITING, _, 0) → (IDLE, +∞, 0);
}

# With existential quantifier
delta_int: {
    (IDLE, _, q) → (URGENT, 0, q)
    ∃ j ∈ q | π_2(j) == HIGH;

    (IDLE, _, q) → (SLEEP, +∞, q);
}

# With universal quantifier
delta_int: {
    (CHECKING, _, p) → (FINISHED, +∞, p)
    ∀ item ∈ p / π_2(item);

    (CHECKING, _, p) → (CHECKING, timeout, p);
}
```

### `delta_ext:` (External Transition Function)

Triggered when one or more events arrive at input ports.

```fpdevsml
delta_ext: {
  I: (i_var_1, ...) ∈ (D_i1, ...) = (init_i1, ...);  # Optional

  behavior: {
    # Rules
  }

  order: {
    # Ordering rules
  }
}
```

#### Rule Syntax Without Intermediate State

```
S_pre_state_tuple, e, event_pattern_tuple → S_post_state_tuple [quantifiers] | [guard];
```

#### Rule Syntax With Intermediate State

```
S_pre_state_tuple ∪ I_pre_state_tuple, e, event_pattern_tuple, last_event_check → S_post_state_tuple ∪ I_post_state_tuple [quantifiers] | [guard];
```

* `last_event_check` is `⊤` if this is the final event in the bag, `⊥` otherwise.

#### Event Pattern

* Single port: `(port_name, payload_tuple)`
* Multi-port: `(port_name * port_index, payload_tuple)`

#### `order:` Section

Defines the priority relation among simultaneous events:

```fpdevsml
order: {
    (in, (id_a, _)) < (in, (id_b, _)) <=> id_a < id_b;
}
```

**Examples:**

```fpdevsml
# Simple (no intermediate state)
delta_ext: {
    behavior: {
        (IDLE), e, (in_admin_stop, ()) → (IDLE);
        (IDLE), e, (in_job, (id)) → (BUSY);
    }
    order: {
        (in_admin_stop, ()) < (in_job, (_)) <=> ⊤;
    }
}

# With intermediate state
delta_ext: {
    I: (temp_sum) ∈ (N) = (0);
    behavior: {
        (total) ∪ (temp_sum), e, (in_value, (val)), _ → (total) ∪ (temp_sum + val);
        (total) ∪ (temp_sum), e, (in_commit, ()), ⊤ → (total + temp_sum) ∪ (0);
    }
    order: {
        (in_value, (_)) < (in_commit, ()) <=> ⊤;
    }
}
```

### `delta_con:` (Confluent Transition Function)

Defines behavior when internal and external events occur simultaneously.

| Syntax                        | Meaning                                               |
|-------------------------------|-------------------------------------------------------|
| `delta_con: delta_int ∘ delta_ext;` | Internal first, then external                   |
| `delta_con: delta_ext ∘ delta_int;` | External first, then internal                   |
| `delta_con: delta_int;`       | Internal only (external events discarded)             |
| `delta_con: delta_ext;`       | External only (internal transition and output aborted)|

### `ta:` (Time Advance Function)

Determines how long the model stays in its current state.

```fpdevsml
ta: {
  (pre-state_tuple) → numerical_expression;
  ...
}
```

**Examples:**

```fpdevsml
# Using sigma variable
ta: {
    (_, sigma) → sigma;
}

# State-based pattern matching
ta: {
    (WAITING) → +∞;
    (PROCESSING) → processing_time;
}

# Combined
ta: {
    (IDLE, _) → +∞;
    (_, sigma) → sigma;
}
```

### `lambda:` (Output Function)

Generates output events just before an internal transition.

```fpdevsml
lambda: {
  (pre-state_tuple) → { output_event_set };
  ...
}
```

**Output event formats:**
* Single port: `(port_name, (value))`
* Multi-port: `(port_name * port_index, (value))`
* No output: `{ }` or `∅`

**Examples:**

```fpdevsml
# Simple output
lambda: {
    (SENDING, _, id) → { (out, (id)) };
    (_, _, _) → { };
}

# Multi-port output
lambda: {
    (ROUTING, port_idx, data_val) → { (out_channel * port_idx, (data_val)) };
    (_, _, _) → { };
}

# Multiple simultaneous outputs
lambda: {
    (PROCESSING, _, res_val) → { (out_data, (res_val)) (out_status, ()) };
    (_, _, _) → { };
}
```

### `obs:` (Observations)

Exposes internal state for monitoring without affecting model behavior.

```fpdevsml
obs: {
    observable_name ← expression;
    ...
}
```

**Examples:**

```fpdevsml
obs: {
    counter ← count;
}

obs: {
    waiting_job_number ← | jobs |;
    current_job_id ← π_1([jobs : 0]);
}

obs: {
    load_factor ← (| jobs | / capacity);
    is_busy ← | jobs | > 0;
}
```

---

## Tables

### Predefined Domains

| Symbol        | Name                                      | Description / Usage                         |
|:--------------|:------------------------------------------|:--------------------------------------------|
| `B`           | **Boolean**                               | Logical values: `⊤` (true) or `⊥` (false).  |
| `N`           | **Naturals**                              | Non-negative integers (`0, 1, 2, …`).       |
| `N*`          | **Naturals (non-zero)**                   | Strictly positive integers (`1, 2, 3, …`).  |
| `Z`           | **Integers**                              | Relative integers (`…, -1, 0, 1, …`).       |
| `R`           | **Reals**                                 | Real numbers.                               |
| `R+` / `R-`   | **Non-negative / Non-positive Reals**     | `R+` (Reals ≥ 0), `R-` (Reals ≤ 0).         |
| `R*`          | **Non-zero Reals**                        | Real numbers except `0`.                    |
| `R+*` / `R-*` | **Strictly Positive / Negative Reals**    | `R+*` (Reals > 0), `R-*` (Reals < 0).       |
| `Q`           | **Rationals**                             | Rational numbers (fractions).               |
| `C`           | **Complex**                               | Complex numbers (`a + bi`).                 |

### Domain Constructors

| Symbol                     | Name / Delimiter Type     | Purpose / Usage                          | Example                                         |
|:---------------------------|:--------------------------|:-----------------------------------------|:------------------------------------------------|
| `{ }` | **Braces**                | Define a **set** (unordered collection). | `S: (ids) ∈ ({N});`                             |
| `< >` | **Angle Brackets**        | Define a **symbol set** (enumeration).   | `S: (phase) ∈ (<wait, send>);`                  |
| `[ ]` | **Square Brackets**       | Define an **array**.                     | `S: (buffer) ∈ ([N]);`                          |
| `@`   | **At Sign**               | Specifies **array size** within `[ ]`.   | `[N @ 10]` → an array of 10 naturals.           |
| `≪ ≫` | **Double Angle Brackets** | Define a **map** (key–value pairs).      | `S: (table) ∈ (≪N → R≫);`                       |

### Logical Connectors and Comparison

| Symbol       | Name                  | Usage   | Example                  |
|:-------------|:----------------------|:--------|:-------------------------|
| `⊤` (U+22A4) | True                  | Value/Guard | `flag = ⊤;`          |
| `⊥` (U+22A5) | False                 | Value/Guard | `S: (active) ∈ (B) = (⊥);` |
| `∧` (U+2227) | Logical AND           | Guards  | `(i > 5) ∧ (j < 2);`    |
| `∨` (U+2228) | Logical OR            | Guards  | `(i = 0) ∨ (j = 0);`    |
| `¬` (U+00AC) | Logical NOT           | Guards  | `¬(flag);`               |
| `=`          | Equality              | Guards  | `phase = <wait>;`        |
| `≠` (U+2260) | Inequality            | Guards  | `phase ≠ <wait>;`        |
| `>`, `<`     | Greater/Less than     | Guards  | `sigma > 0;`             |
| `≥`, `≤`     | Greater/Less or equal | Guards  | `sigma ≥ 0;`             |

### Values, Operators and Symbols

| Symbol             | Name              | Usage                              | Example                                                  |
|:-------------------|:------------------|:-----------------------------------|:---------------------------------------------------------|
| `∅` (U+2205)       | Empty Set         | Value of a set, array or map.      | `S: (ids) ∈ ({N}) = (∅);`                               |
| `∈` (U+2208)       | Belongs to        | Domain assignment.                 | `S: (var) ∈ (Domain);`                                   |
| `∪` (U+222A)       | Union             | Array/Set Expression               | `queue ∪ [ 0 ]` or `{ 0 } ∪ s`                           |
| `∖`                | Difference        | Array/Set Expression               | `queue ∖ [ elem ]`                                       |
| `+∞`               | Positive Infinity | Value.                             | `ta: { (PASSIVE, _) → +∞; }`                            |
| `-∞`               | Negative Infinity | Value.                             | Rare; used in mathematical extensions.                   |
| `∀` (U+2200)       | For all           | Quantification.                    | `∀ item ∈ pool / π_2(item)`                              |
| `∃` (U+2203)       | There exists      | Quantification.                    | `∃ job ∈ queue \| π_1(job) > 0`                          |
| `\|`               | Guard (Condition) | Boolean condition.                 | `\| i > 5`                                               |
| `→` (U+2192)       | Arrow             | Transition definition.             | `(state1) → (state2);`                                   |
| `_` (U+005F)       | Wildcard          | Match-all in transitions.          | `(wait, _, val) → (send, 0, val);`                       |

---

## Examples — Atomic Models

### Passive

The simplest possible FPDEVSML atomic model: remains indefinitely inactive.

```fpdevsml
passive {
  ta: {
    () → +∞;
  }
}
```

### Counter

```fpdevsml
counter {
  P: (initial) ∈ (N) = (0);

  S: (phase, count) ∈ (< passive, active >, N) = (passive, initial);

  X: {
    (in,(id)) | (N);
  }

  Y: {
    (out,(counter)) | (N);
  }

  delta_int: {
    (active, count) → (passive, _)
    | count < 10;

    (active, count) → (passive, 0)
    | count = 10;
  }

  delta_ext: {
    behavior: {
      (passive, count), e, (in, (_)) → (active, count + 1);
    }
    order: { }
  }

  delta_con: delta_ext ∘ delta_int

  ta: {
    (passive, _) → +∞;
    (active, _) → 0;
  }

  lambda: {
    (active, count) → { (out, (count)) };
  }

  obs: {
    counter ← count;
  }
}
```

### Generator

```fpdevsml
generator {
  P: (duration) ∈ (N) = (0);

  S: (phase, sigma, id) ∈ (< wait, send >, R, N) = (wait, duration, 0);

  X: {
    (in,()) | ();
  }

  Y: {
    (out,(id)) | (N);
  }

  delta_int: {
    (wait, sigma, _) → (send, 0, _);
    (send, sigma, id) → (wait, duration, id + 1);
  }

  delta_ext: {
    I: () ∈ () = ()
    behavior: { }
    order: { }
  }

  delta_con: delta_ext ∘ delta_int

  ta: {
    (_, sigma, _) → sigma;
  }

  lambda: {
    (send, _, id) → { (out, (id)) };
  }
}
```

### Processor

```fpdevsml
processor {
  P : (factor) ∈ (R) = (1);

  S: (phase, sigma, jobs) ∈ (< passive, busy, send, next >, R, [ (id,processing_time) ∈ (N,N) ]) = (passive, +∞, ∅);

  X: {
    (in,(job)) | ((id,processing_time) ∈ (N,N));
  }

  Y: {
    (out,(job)) | ((id,processing_time) ∈ (N,N));
  }

  delta_int: {
    (busy, _, jobs) → (send, 0, jobs);
    (send, _, [_|next_jobs]) → (next, 0, next_jobs);
    (next, _, ∅) → (passive, +∞, ∅);
    (next, _, [(id,processing_time)|next_jobs]) → (busy, processing_time * factor, [(id,processing_time)|next_jobs]);
  }

  delta_ext: {
    I: () ∈ () = ()
    behavior: {
      (passive, sigma, jobs), _, (in, ((id,processing_time))) → (busy, processing_time * factor, jobs ∪ [(id,processing_time)]);
      (busy, sigma, jobs), e, (in, (job)) → (busy, sigma - e, jobs ∪ [job]);
    }
    order: {
      (in,(id_a,_)) < (in,(id_b,_)) <=> id_a < id_b;
    }
  }

  delta_con: delta_int ∘ delta_ext

  ta: {
    (_, sigma, _) → sigma;
  }

  lambda: {
    (send, _, [job|next_jobs]) → { (out, (job)) };
  }

  obs: {
    waiting_job_number ← | jobs |;
    current_job_id ← π_1([jobs:0]);
  }
}
```

### GoL Cell

```fpdevsml
cell {
  P: (init) ∈ (<dead,alive>) = (dead);

  S: (status) ∈ (<dead,alive>) = (init);

  X: {
    (in,(v)) | (<dead,alive>);
  }

  Y: {
    (out,(v)) | (<dead,alive>);
  }

  delta_int: {
    (_) → (_);
  }

  delta_ext: {
    I: (i) ∈ (N) = (0);

    behavior: {
      (status) ∪ (i), _, (in, (alive)), ⊥ → (status) ∪ (i+1);
      (status) ∪ (i), _, (in, (dead)), ⊥ → (status) ∪ (i);

      (dead) ∪ (i), _, (in, (alive)), ⊤ → (alive) ∪ (0)
      | i = 2;
      (dead) ∪ (i), _, (in, (dead)), ⊤ → (alive) ∪ (0)
      | i = 3;

      (alive) ∪ (i), _, (in, (alive)), ⊤ → (dead) ∪ (0)
      | i ≠ 2 ∧ i ≠ 1;
      (alive) ∪ (i), _, (in, (dead)), ⊤ → (dead) ∪ (0)
      | i ≠ 3 ∧ i ≠ 2;

      (status) ∪ (i), _, (in, (_)), ⊤ → (status) ∪ (0);
    }
    order: { }
  }

  delta_con: delta_ext;

  ta: {
    (_) → 1;
  }

  lambda: {
    (status) → { (out,(status)) };
  }

  obs: {
    status ← status;
  }
}
```

### SIR Individual

```fpdevsml
individual {
  P: (recovery_duration, contact_interval) ∈ (R+, R+) = (10.0, 1.0);

  S: (phase, sigma, time_remaining_infected) ∈ (< S, I, R >, R+, R+)
    = (S, +∞, 0.0);

  X: {
    (in_exposure, ()) | ();
  }

  Y: {
    (out_contact, ()) | ();
  }

  delta_int: {
    (I, sigma, time_remaining) → (I, contact_interval, time_remaining - sigma)
    | sigma < time_remaining ∧ contact_interval < time_remaining - sigma;

    (I, sigma, time_remaining) → (I, time_remaining - sigma, time_remaining - sigma)
    | sigma < time_remaining;

    (I, sigma, time_remaining) → (R, +∞, 0.0)
    | sigma = time_remaining;
  }

  delta_ext: {
    behavior: {
      (S, _, _), e, (in_exposure, ()) → (I, contact_interval, recovery_duration)
      | contact_interval < recovery_duration;

      (S, _, _), e, (in_exposure, ()) → (I, recovery_duration, recovery_duration);

      (I, sigma, time_remaining), e, (in_exposure, ()) → (I, sigma - e, time_remaining - e);

      (R, _, _), e, (in_exposure, ()) → (R, +∞, 0.0);
    }
    order: { }
  }

  ta: {
    (_, sigma, _) → sigma;
  }

  lambda: {
    (I, sigma, time_remaining) → { (out_contact, ()) }
    | sigma < time_remaining;
  }
}
```

### Traffic Light Controller

```fpdevsml
controller {
  P: (t_min_green, t_orange, t_all_red) ∈ (R+, R+, R+) = (5.0, 3.0, 1.0);

  S: (phase, sigma, car_ns_waiting, car_ew_waiting) ∈
   (< NS_GREEN, NS_ORANGE, NS_RED, EW_GREEN, EW_ORANGE, EW_RED >,
    R+, B, B) = (EW_RED, t_all_red, ⊥, ⊥);

  X: {
    (in_ns_detect, ()) | ();
    (in_ew_detect, ()) | ();
  }

  Y: {
    (out_ns, (cmd)) | (<RED, ORANGE, GREEN>);
    (out_ew, (cmd)) | (<RED, ORANGE, GREEN>);
  }

  delta_int: {
    (NS_GREEN, _, _, _) → (NS_ORANGE, t_orange, ⊥, ⊥);
    (NS_ORANGE, _, _, _) → (NS_RED, t_all_red, ⊥, ⊥);
    (NS_RED, _, car_ns_waiting, ⊤) → (EW_GREEN, t_min_green, car_ns_waiting, ⊤);
    (NS_RED, _, car_ns_waiting, ⊥) → (EW_GREEN, +∞, car_ns_waiting, ⊥);
    (EW_GREEN, _, _, _) → (EW_ORANGE, t_orange, ⊥, ⊥);
    (EW_ORANGE, _, _, _) → (EW_RED, t_all_red, ⊥, ⊥);
    (EW_RED, _, ⊤, car_ew_waiting) → (NS_GREEN, t_min_green, ⊤, car_ew_waiting);
    (EW_RED, _, ⊥, car_ew_waiting) → (NS_GREEN, +∞, ⊥, car_ew_waiting);
  }

  delta_ext: {
    behavior: {
      (NS_GREEN, sigma, _, car_ew_waiting), e, (in_ns_detect, ()) → (NS_GREEN, sigma - e, ⊤, car_ew_waiting);
      (EW_GREEN, sigma, car_ns_waiting, _), e, (in_ew_detect, ()) → (EW_GREEN, sigma - e, car_ns_waiting, ⊤);
      (NS_GREEN, +∞, car_ns_waiting, _), e, (in_ew_detect, ()) → (NS_GREEN, t_min_green, car_ns_waiting, ⊤);
      (EW_GREEN, +∞, _, car_ew_waiting), e, (in_ns_detect, ()) → (EW_GREEN, t_min_green, ⊤, car_ew_waiting);
      (phase, sigma, _, car_ew_waiting), e, (in_ns_detect, ()) → (phase, sigma - e, ⊤, car_ew_waiting);
      (phase, sigma, car_ns_waiting, _), e, (in_ew_detect, ()) → (phase, sigma - e, car_ns_waiting, ⊤);
    }
    order: { }
  }

  delta_con: delta_ext ∘ delta_int

  ta: {
    (_, sigma, _, _) → sigma;
  }

  lambda: {
    (NS_GREEN, _, _, _) → { (out_ns, (GREEN)) (out_ns, (RED)) };
    (NS_ORANGE, _, _, _) → { (out_ns, (ORANGE)) (out_ns, (RED)) };
    (EW_RED, _, _, _) → { (out_ns, (RED)) (out_ns, (RED)) };
    (EW_GREEN, _, _, _) → { (out_ns, (RED)) (out_ew, (GREEN)) };
    (EW_ORANGE, _, _, _) → { (out_ns, (RED)) (out_ew, (ORANGE)) };
    (NS_RED, _, _, _) → { (out_ns, (RED)) (out_ew, (RED)) };
  }
}
```

### Sync

```fpdevsml
sync {
  S: (received_a, received_b) ∈ (B, B) = (⊥, ⊥);

  X: {
    (in_a, ()) | ();
    (in_b, ()) | ();
  }

  Y: {
    (out, ()) | ();
  }

  delta_int: {
    (⊤, ⊤) → (⊥, ⊥);
  }

  delta_ext: {
    I: () ∈ () = ()
    behavior: {
      (_, received_b), _, (in_a, ()) → (⊤, received_b);
      (received_a, _), _, (in_b, ()) → (received_a, ⊤);
    }
    order: { }
  }

  delta_con: delta_ext ∘ delta_int

  ta: {
    (⊤, ⊤) → 0;
    (_, _) → +∞;
  }

  lambda: {
    (⊤, ⊤) → { (out, ()) };
  }
}
```

### Conveyor

```fpdevsml
conveyor {
  P: (length, speed) ∈ (R+, R+) = (1.0, 1.0);

  S: (phase, sigma, queue) ∈ (< passive, moving, send >, R, [ (id, payload) ]) = (passive, +∞, ∅);

  X: { (in, (elem)) | ( (N, N) ); }
  Y: { (out, (elem)) | (N); }

  delta_int: {
    (moving, _, queue) → (send, 0, queue);

    (send, _, queue) → (passive, +∞, ∅)
    | | queue | = 1;

    (send, _, [_ | nexts]) → (moving, length / speed, nexts);
  }

  delta_ext: {
    behaviour: {
      (passive, sigma, queue), _, (in, (elem)) → (moving, length / speed, queue ∪ [ elem ]);
      (moving, sigma, queue), e, (in, (elem)) → (moving, sigma - e, queue ∪ [ elem ]);
      (send, sigma, queue), e, (in, (elem)) → (send, sigma - e, queue ∪ [ elem ]);
    }
  }

  delta_con: delta_ext ∘ delta_int

  ta: { (_, sigma, _) → sigma; }

  lambda: {
    (send, _, [job | _]) → { (out, (π_1(job))) }
  }
}
```

---

## Grammar (EBNF) — Atomic Model Subset

```ebnf
(* ==================================================== *)
(* FPDEVSML – Atomic Model Grammar                      *)
(* ==================================================== *)

model_definition = atomic_model ;

atomic_model = identifier, "{",
  [section_parameters],
  [section_state],
  [section_in_ports],
  [section_out_ports],
  [section_delta_int],
  [section_delta_ext],
  [section_delta_con],
  section_ta,
  [section_output],
  [section_observations],
"}" ;

(* ---------------- Sections ---------------- *)
section_parameters = "P", ":", tuple_definition, "∈", tuple_domain_definition, "=", tuple_value, ";" ;
section_state      = "S", ":", tuple_definition, "∈", tuple_domain_definition, "=", tuple_value, ";" ;

section_observations = "obs", ":", "{", observations, "}" ;
observations = { observation } ;
observation  = identifier, "←", expression, ";" ;

section_in_ports  = "X", ":", "{", ports, "}" ;
section_out_ports = "Y", ":", "{", ports, "}" ;

ports = { port } ;
port  = "(", identifier, [ "*", numerical_expression ], ",", tuple_definition, ")", "|", tuple_domain_definition, ";" ;

(* ---------------- Transition Functions ---------------- *)
section_delta_int = "delta_int", ":", "{", { delta_int_function_simple | delta_int_function_composition }, "}" ;
delta_int_function_simple      = delta_int_function ;
delta_int_function_composition = "{", { delta_int_function }, "}", [ for_all_quantifier ], [ exists_quantifier ], [ "|", boolean_expression ] ;
delta_int_function = "(", expressions, ")", "→", "(", expressions, ")", [ for_all_quantifier ], [ exists_quantifier ], [ "|", boolean_expression ] ;

section_delta_ext = "delta_ext", ":", "{", [section_intermediates], delta_ext_functions, section_order, "}" ;
section_intermediates = "I", ":", tuple_definition, "∈", tuple_domain_definition, "=", tuple_value ;

delta_ext_functions = "behavior", ":", "{", { delta_ext_function | delta_ext_inter_function }, "}" ;
delta_ext_function = "(", expressions, ")", ",", numerical_expression, ",", event,
  "→", "(", expressions, ")", [ for_all_quantifier ], [ exists_quantifier ], [ "|", boolean_expression ] ;

delta_ext_inter_function = "(", expressions, ")", "∪", "(", expressions, ")", ",", numerical_expression, ",", event, ",", boolean_expression,
  "→", "(", expressions, ")", "∪", "(", expressions, ")", [ for_all_quantifier ], [ exists_quantifier ], [ "|", boolean_expression ] ;

section_order = "order", ":", "{", { order }, "}" ;
order = event, "<", event, "<=>", boolean_expression, ";" ;

section_delta_con = "delta_con", ":", section_delta_con_content ;
section_delta_con_content = "{" , delta_con_functions , "}" | delta_con_function_ext_int | delta_con_function_int_ext ;
delta_con_function_ext_int = "delta_ext", ["∘", "delta_int"] ;
delta_con_function_int_ext = "delta_int", ["∘", "delta_ext"] ;

section_ta = "ta", ":", "{", { ta_function }, "}" ;
ta_function = "(", expressions, ")", "→", numerical_expression, [ for_all_quantifier ],[ exists_quantifier ], [ "|", boolean_expression ] ;

section_output = "lambda", ":", "{", { output_function }, "}" ;
output_function = "(", expressions, ")", "→", "{", output_events, "}", [ for_all_quantifier ],[ exists_quantifier ], [ "|", boolean_expression ] ;
output_events = { output_event } ;
output_event  = "(", identifier, [ "*", port_index ], ",", "(", expressions, ")", ")" ;
port_index = identifier_value | projection ;

(* ---------------- Tuples ---------------- *)
tuple_definition        = "(", [ typed_identifier, { ",", typed_identifier } ], ")" ;
tuple_domain_definition  = "(", [ domain_definition, { ",", domain_definition } ], ")" ;
tuple_value              = "(", [ expression, { ",", expression } ], ")" ;
tuple_definition_in_domain = tuple_definition, "∈", tuple_domain_definition ;

(* ---------------- Domains ---------------- *)
domain_definition = predefined_set | symbol_set | set_definition
  | map_definition | array_definition | tuple_definition_in_domain | tuple_domain_definition ;

predefined_set = "R+" | "R-" | "R*" | "R+*" | "R-*"
  | "R"  | "N*" | "N"
  | "Z+" | "Z-" | "Z*" | "Z+*" | "Z-*"
  | "Z"  | "C"  | "B"  | "Q" ;

symbol_set = "<", typed_identifiers, ">" ;
set_definition = "{", set_element_definition, "}" ;
set_element_definition = predefined_set | symbol_set | tuple_definition_in_domain | array_definition ;
map_definition = "≪", tuple_definition_in_domain, "→", tuple_definition_in_domain, "≫" ;
array_definition = "[", set_element_definition, [ "@", uint_ ], "]" ;

(* ---------------- Expressions ---------------- *)
expression = array_expression | set_expression | map_expression | tuple_value | boolean_expression | empty_set ;
expressions = [ expression ], { ",", expression } ;

boolean_expression = and_expression, { "∨", and_expression } ;
and_expression     = boolean_term, { "∧", boolean_term } ;
boolean_term = "⊥" | "⊤" | "(", boolean_expression, ")"
  | not_expression | comparison_expression ;
not_expression = "¬", boolean_expression ;
comparison_expression = numerical_expression, ("=" | "<" | ">" | "≠" | "≤" | "≥"), numerical_expression ;

numerical_expression = numerical_sub_expression | infinity ;
numerical_sub_expression = term, { ("+" | "-"), term } ;
term = factor, { ("*" | "/" | "%"), factor } ;

factor = set_function | numerical_function | projection | array_index_value
  | map_index_value | cardinal | literal | "(", numerical_expression, ")" ;

set_function = ("min" | "max" | "∑" | "∏"),
  "{", "∀", identifier, "∈", identifier, "}",
  "(", expression, ")" ;

projection = "π_", uint_, "(", numerical_expression, ")" ;
array_index_value = "[", expression, ":", numerical_expression, { ":", numerical_expression }, "]" ;
map_index_value = "≪", expression, ":", expression, "≫" ;
cardinal = "|", expression, "|" ;
infinity = ("+" | "-"), "∞" ;

numerical_function = ("abs" | "sqrt" | "inv" | "sin" | "cos" | "tan" |
       "cot" | "arcsin"| "arccos" | "arctan"| "arccot"|
       "exp" | "log10" | "log2" | "ln"|
       "sinh" | "cosh" | "tanh" | "arsinh" | "arcosh" | "artanh"),
      "(", numerical_expression, ")" ;

literal = strict_double | uint_ | identifier_value | complex_value | rational_value | dont_care ;
complex_value = "<", ( strict_double | uint_ ), ",", ( strict_double | uint_ ), ">" ;
rational_value = "<", uint_, "/", uint_, ">" ;
dont_care = "_" ;
empty_set = "∅" ;

digit = "0".."9" ;
nonzero_digit = "1".."9" ;
uint_ = "0" | nonzero_digit, { digit } ;
sign = "+" | "-" ;
frac_part = ".", digit, { digit } ;
strict_double = [ sign ], ( uint_, frac_part | frac_part ) ;

exists_quantifier = ("∃" | "∄"), typed_identifier, "∈", typed_identifier,
  [ "/", boolean_expression ] ;

for_all_quantifier = "∀", (identifier | tuple_definition), "∈",
  ((identifier | array_enumerate_value | set_enumerate_value)
  | "(", (identifier | array_enumerate_value | set_enumerate_value),
  { ",", (identifier | array_enumerate_value | set_enumerate_value) }, ")"),
  [ "/", boolean_expression ] ;

letter  = "A".."Z" | "a".."z" ;
typed_identifier  = letter, { letter | digit | "_" } ;
identifier        = letter, { letter | digit | "_" } ;
identifier_value  = identifier ;
typed_identifiers = typed_identifier, { ",", typed_identifier } ;

event = "(", identifier, [ "*", typed_identifier ], ",", "(", expressions, ")", ")" ;
```


Liste des modèles utilisés :

https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/blob/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf
https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/blob/main/Llama-3.2-3B-Instruct-Q8_0.gguf
https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/blob/main/Phi-3.5-mini-instruct-Q8_0.gguf
https://huggingface.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF