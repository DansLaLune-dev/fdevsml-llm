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
 