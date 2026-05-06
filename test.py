from llama_cpp import Llama, LlamaGrammar

from rag_engine import AtomicRAG

from langchain_community.llms import LlamaCpp

from langchain_core.prompts import PromptTemplate

from langchain_huggingface import HuggingFaceEmbeddings

import os

# ── Chemins ────────────────────────────────────────────────────────────────────

base_dir = os.path.dirname(os.path.abspath(__file__))

model_path_llama = os.path.join(base_dir, "models", "Llama-3.2-3B-Instruct-Q4_K_M.gguf")

model_path_llama8 = os.path.join(base_dir, "models", "Llama-3.2-3B-Instruct-Q8.gguf")

model_path_phi3_5 = os.path.join(base_dir, "models", "Phi-3.5-mini-instruct-Q8.gguf")

model_path_phi4 = os.path.join(base_dir, "models", "Phi-4-reasoning-plus-Q8.gguf")

model_path_qwen = os.path.join(base_dir, "models", "Qwen2.5-Coder-7B-Instruct-Q8.gguf")

model_path_qwen3 = os.path.join(base_dir, "models", "Qwen3.5-9B.Q8_0.gguf")

# ── RAG ────────────────────────────────────────────────────────────────────────

rag = AtomicRAG(doc_path="README.md")

# query = (

#    "Génère un modèle atomique nommé 'event_counter' qui compte les événements "

#   "reçus sur le port 'in' et émet le total sur 'out'. Il remet le compteur à 0 "

#  "dès qu'il atteint 10."

# )

# query = (
# "Génère un modèle atomique nommé 'event_generator' qui génère de manière autonome et périodique des messages "
# "A chaque cycle, il émet un message contenant un indice courant (sous forme de liste à un élément) ainsi que cet indice en valeur numérique, puis incrémente son compteur interne "
# "L'intervalle entre deux émissions est configurable via le paramètre `time_step`."
# "#Le composant ne reçoit aucune donnée de l'extérieur : il fonctionne entièrement en autonome, comme une horloge produisant des tokens numérotés séquentiellement"
# )

query = (
    "Génère un modèle atomique nommé 'dynamic_router' qui reçoit un mesage composé d'une liste et d'un indice de destination, "
    "puis redirige ce message vers la sortie correspondante à cet indice. "
    "Il dispose de `N_outputs` sorties possibles. Lorsqu'un message arrive, il est mémorisé temporairement, puis immédiatement" 
    "réémis sur le bon canal de sortie."
    "Seuls les indices strictement compris entre 0 et `N_outputs` sont acceptés ; tout message hors de cette plage est ignoré." 
    "Si un nouveau message arrive pendant que le composant est en train d'en traiter un, il remplace le précédent."
)

query_acc = (
    "Génére un modèle atomique nommée `sensor` qui associe chaque capteur à un étage précis." ""
    "Le capteur surveille en permanence la position de la cabine." ""
    "Dès que la cabine passe à son étage, il envoie immédiatement un signal de détection au contrôleur,"
    "puis retourne en veille jusqu'à la prochaine occurrence."
)

context = rag.get_context(query)

# ── Exemple de référence (injecté dans le prompt pour guider le modèle) ────────

exemple_reference = """\

event_counter {
  P: (max) ∈ (N) = (10);
  S: (phase, count) ∈ (<WAIT, SEND>, N) = (WAIT, 0);
  X: { (in, ()) | (); }
  Y: { (out, (count)) | (N); }
  
  delta_int: {
    (SEND, count) → (WAIT, 0) | count = max;
    (SEND, count) → (WAIT, count);
  }
  
  delta_ext: {
    behavior: {
      (WAIT, count), e, (in, ()) → (SEND, count + 1);
    }
    order: { }
  }
  
  delta_con: delta_ext ∘ delta_int
  
  ta: {
    (SEND, _) → 0;
    (WAIT, _) → +∞;
  }
  
  lambda: {
    (SEND, count) → { (out, (count)) };
  }
  
  obs: { 
    count ← count; 
  }
}
"""

# ── Grammaire GBNF ────────────────────────────────────────────────────────────

gbnf_grammar = r"""
root ::= identifier "{" section-parameters? section-state? section-in-ports? section-out-ports? section-delta-int? section-delta-ext? section-delta-con? section-ta section-output? section-observations? "}"

section-parameters ::= "P" ":" tuple-definition "\u2208" tuple-domain-definition "=" tuple-value ";"

section-state ::= "S" ":" tuple-definition "\u2208" tuple-domain-definition "=" tuple-value ";"

section-in-ports ::= "X" ":" "{" port* "}"

section-out-ports ::= "Y" ":" "{" port* "}"

port ::= "(" identifier ("*" numerical-expression)? "," tuple-definition ")" "|" tuple-domain-definition ";"

section-ta ::= "ta" ":" "{" ta-function* "}"

ta-function ::= "(" expressions ")" "\u2192" numerical-expression for-all-quantifier? exists-quantifier* ("|" boolean-expression)? ";"

section-output ::= "lambda" ":" "{" output-function* "}"

output-function ::= "(" expressions ")" "\u2192" "{" output-event* "}" for-all-quantifier? exists-quantifier* ("|" boolean-expression)? ";"

output-event ::= "(" identifier ("*" port-index)? "," "(" expressions ")" ")"

port-index ::= identifier-value | projection

section-observations ::= "obs" ":" "{" observation* "}"

observation ::= identifier "\u2190" expression ";"

section-delta-int ::= "delta_int" ":" "{" delta-int-function-simple* delta-int-function-composition* "}"

delta-int-function-simple ::= delta-int-function

delta-int-function-composition ::= "{" delta-int-function* "}" for-all-quantifier? exists-quantifier* ("|" boolean-expression)? ";"

delta-int-function ::= "(" expressions ")" "\u2192" "(" expressions ")" for-all-quantifier? exists-quantifier* ("|" boolean-expression)? ";"

section-delta-ext ::= "delta_ext" ":" "{" section-intermediates? delta-ext-functions section-order "}"

section-intermediates ::= "I" ":" tuple-definition "\u2208" tuple-domain-definition "=" tuple-value

section-order ::= "order" ":" "{" order* "}"

order ::= event "<" event "<=>" boolean-expression ";"

delta-ext-functions ::= "behavior" ":" "{" (delta-ext-inter-function | delta-ext-function)* "}"

delta-ext-inter-function ::= "(" expressions ")" "\u222a" "(" expressions ")" "," numerical-expression "," event "," boolean-expression "\u2192" "(" expressions ")" "\u222a" "(" expressions ")" for-all-quantifier? exists-quantifier* ("|" boolean-expression)? ";"

delta-ext-function ::= "(" expressions ")" "," numerical-expression "," event "\u2192" "(" expressions ")" for-all-quantifier? exists-quantifier* ("|" boolean-expression)? ";"

section-delta-con ::= "delta_con" ":" section-delta-con-content

section-delta-con-content ::= "{" delta-con-function-entry* "}" | delta-con-function-ext-int | delta-con-function-int-ext

delta-con-function-ext-int ::= "delta_ext" ("\u2218" "delta_int")?

delta-con-function-int-ext ::= "delta_int" ("\u2218" "delta_ext")?

delta-con-function-entry ::= "(" delta-con-function

delta-con-function ::= "(" expressions ")" "," "{" event "}" ")" "\u2192" "(" expressions ")"

event ::= "(" identifier ("*" typed-identifier)? "," "(" expressions ")" ")"

events ::= event*

domain-definition ::= predefined-set | symbol-set-definition | set | map | array-definition | tuple-definition-in-domain | tuple-domain-definition

predefined-set ::= "R+*" | "R-*" | "R+" | "R-" | "R*" | "R" | "N*" | "N" | "Z+*" | "Z-*" | "Z+" | "Z-" | "Z*" | "Z" | "C" | "B" | "Q"

set ::= "{" set-element-definition "}"

set-element-definition ::= predefined-set | symbol-set-definition | tuple-definition-in-domain | array-definition

symbol-set-definition ::= "<" typed-identifier ("," typed-identifier)* ">"

map ::= "\u226a" tuple-definition-in-domain "\u2192" tuple-definition-in-domain "\u226b"

array-definition ::= "[" set-element-definition ("@" uint)? "]"

tuple-definition-in-domain ::= tuple-definition "\u2208" tuple-domain-definition

tuple-definition ::= "(" (typed-identifier ("," typed-identifier)*)? ")"

tuple-domain-definition ::= "(" (domain-definition ("," domain-definition)*)? ")"

expression ::= array-expression | set-expression | map-expression | tuple-value | boolean-expression | empty-set

empty-set ::= "\u2205"

expressions ::= (expression ("," expression)*)?

boolean-expression ::= and-expression ("\u2228" and-expression)*

and-expression ::= boolean-term ("\u2227" boolean-term)*

boolean-term ::= "\u22a5" | "\u22a4" | "(" boolean-expression ")" | not-expression | comparison-expression

comparison-rest ::= ("=" | "<" | ">" | "\u2260" | "\u2264" | "\u2265") numerical-expression

comparison-expression ::= numerical-expression comparison-rest?

not-expression ::= "\u00ac" boolean-expression

array-expression ::= array-union-left | array-union-right | array-minus | array-literal

array-literal ::= array-value | array-enumerate-value | array-comprehension | array-map-function

array-value ::= "[" (array-head-value | array-tail-value | array-elements) "]"

array-head-value ::= array-element "|" array-sub-set

array-tail-value ::= array-sub-set "$" array-element

array-element ::= identifier | tuple-value | dont-care

array-sub-set ::= identifier | dont-care

array-elements ::= expression ("," expression)*

array-enumerate-value ::= "[" numerical-expression "..." numerical-expression "]"

array-comprehension ::= "[" "\u2200" identifier "\u2208" identifier "/" boolean-expression "]"

array-map-function ::= "map" "[" "\u2200" identifier "\u2208" array-expression "]" "(" expression ")"

array-union-left ::= array-literal "\u222a" array-term

array-union-right ::= array-term "\u222a" array-literal

array-minus ::= array-term "\u2216" array-literal

array-term ::= array-literal | array-sub-literal | identifier-value

array-sub-literal ::= "(" array-expression ")"

set-expression ::= set-union | set-minus | set-literal

set-literal ::= set-enumerate-value | set-value | set-comprehension | set-map-function | set-sub-literal

set-value ::= "{" numerical-expression ("," numerical-expression)* "}"

set-enumerate-value ::= "{" numerical-expression "..." numerical-expression "}"

set-comprehension ::= "{" "\u2200" identifier "\u2208" identifier "/" boolean-expression "}"

set-map-function ::= "map" "{" "\u2200" identifier "\u2208" set-expression "}" "(" expression ")"

set-union ::= set-term "\u222a" set-literal

set-minus ::= set-term "\u2216" set-literal

set-term ::= set-literal | identifier-value

set-sub-literal ::= "(" set-expression ")"

tuple-value ::= "(" (expression ("," expression)*)? ")"

map-expression ::= map-union | map-minus | map-value

map-value ::= "\u226a" map-values? "\u226b"

map-values ::= key-value ("," key-value)*

key-value ::= "(" expression "\u2192" expression ")"

map-union ::= identifier-value "\u222a" map-value

map-minus ::= identifier-value "\u2216" map-value

key-value-definition ::= "(" typed-identifier "\u2192" typed-identifier ")"

numerical-expression ::= numerical-sub-expression | infinity

numerical-sub-expression ::= term (("+"|"-") term)*

term ::= factor (("*"|"/"|"%") factor)*

factor ::= set-function | numerical-function | projection | array-index-value | map-index-value | abs | ceil | floor | literal | "(" numerical-expression ")"

set-function ::= ("min" | "max" | "\u2211" | "\u220f") "{" "\u2200" identifier "\u2208" identifier "}" "(" expression ")"

projection ::= "\u03c0" "_" uint "(" numerical-expression ")"

array-index-value ::= "[" expression ":" numerical-expression (":" numerical-expression)* "]"

map-index-value ::= "\u226a" expression ":" expression "\u226b"

abs ::= "|" expression "|"

ceil ::= "\u2308" expression "\u2309"

floor ::= "\u230a" expression "\u230b"

infinity ::= ("+" | "-") "\u221e"

literal ::= strict-double | uint | identifier-value | complex-value | rational-value | dont-care

complex-value ::= "<" (strict-double | uint) "," (strict-double | uint) ">"

rational-value ::= "<" uint "/" uint ">"

dont-care ::= "_"

numerical-function ::= ("arsinh" | "arcosh" | "artanh" | "arcsin" | "arccos" | "arctan" | "arccot" | "log10" | "log2" | "ln" | "sinh" | "cosh" | "tanh" | "sin" | "cos" | "tan" | "cot" | "sqrt" | "inv" | "abs" | "exp" | "Card") "(" numerical-expression ")"

exists-quantifier ::= ("\u2203" | "\u2204") (typed-identifier | key-value-definition | tuple-definition) "\u2208" typed-identifier ("/" boolean-expression)?

for-all-quantifier ::= "\u2200" (typed-identifier | key-value-definition | tuple-definition) "\u2208" (for-all-domain | "(" for-all-domain ("," for-all-domain)* ")") ("/" boolean-expression)?

for-all-domain ::= array-enumerate-value | set-enumerate-value | identifier

identifier ::= [a-zA-Z] [a-zA-Z0-9_]*

typed-identifier ::= [a-zA-Z] [a-zA-Z0-9_]*

identifier-value ::= [a-zA-Z] [a-zA-Z0-9_]*

uint ::= [0-9]+

strict-double ::= [0-9]+ "." [0-9]+ (([eE] [+-]? [0-9]+))?
"""

# ── Exemple cible (few-shot orienté vers la requête) ──────────────────────────

exemple_binaire = """
toggle {
  # Modèle basculeur binaire ON/OFF.
  # Reçoit une impulsion, bascule son état, et émet le nouvel état.
  # Illustre : états booléens, phase transitoire SEND avec ta=0,
  #            cohérence delta_ext / ta / lambda.

  S: (phase, state) ∈ (< IDLE, SEND >, B) = (IDLE, ⊥);

  X: {
    (in_pulse, ()) | ();
  }

  Y: {
    (out_state, (v)) | (B);
  }

  delta_int: {
    # Après émission, retour en veille passive.
    (SEND, state) → (IDLE, state);
  }

  delta_ext: {
    behavior: {
      # Bascule vers ON et programme l'émission immédiate.
      (IDLE, ⊥), e, (in_pulse, ()) → (SEND, ⊤);
      # Bascule vers OFF et programme l'émission immédiate.
      (IDLE, ⊤), e, (in_pulse, ()) → (SEND, ⊥);
    }
    order: { }
  }

  delta_con: delta_ext ∘ delta_int

  ta: {
    (SEND, _) → 0;   # Émission immédiate après bascule.
    (IDLE, _) → +∞;  # Passif en attente d'impulsion.
  }

  lambda: {
    # Émet le nouvel état sur out_state.
    (SEND, state) → { (out_state, (state)) };
  }

  obs: {
    current_state ← state;
  }
}
"""

exemple_minuterie = """
timer {
  # Reçoit un délai 'd' et déclenche une alarme après ce délai.
  # Sans payload, utilise default_delay.
  # Illustre : gestion de sigma, recharge, default_delay, obs.

  P: (default_delay) ∈ (R+) = (10.0);

  S: (phase, sigma) ∈ (< IDLE, RUNNING >, R) = (IDLE, +∞);
  #                                         ^
  # R et non R+ : sigma vaut +∞ en phase IDLE,
  # ce qui dépasse le domaine strict de R+.

  X: {
    (in_start, (delay)) | (R+);
    (in_start_default, ()) | ();  # Démarre avec default_delay.
    (in_cancel, ()) | ();
  }

  Y: {
    (out_alarm, ()) | ();
  }

  delta_int: {
    (RUNNING, _) → (IDLE, +∞);
  }

  delta_ext: {
    behavior: {
      # Démarrage avec délai explicite (depuis IDLE ou RUNNING).
      (_, _), e, (in_start, (d)) → (RUNNING, d);

      # Démarrage avec délai par défaut.
      (_, _), e, (in_start_default, ()) → (RUNNING, default_delay);

      # Annulation : remet en veille.
      (RUNNING, _), e, (in_cancel, ()) → (IDLE, +∞);

      # Annulation ignorée si déjà IDLE.
      (IDLE, _), e, (in_cancel, ()) → (IDLE, +∞);
    }
    order: {
      # Annulation traitée avant tout démarrage.
      (in_cancel, ()) < (in_start, (_))         <=> ⊤;
      (in_cancel, ()) < (in_start_default, ())  <=> ⊤;
      # Démarrage explicite prioritaire sur le défaut.
      (in_start, (_)) < (in_start_default, ())  <=> ⊤;
    }
  }

  delta_con: delta_ext ∘ delta_int

  ta: {
    (_, sigma) → sigma;
  }

  lambda: {
    (RUNNING, _) → { (out_alarm, ()) };
  }

  obs: {
    remaining_time ← sigma;
    is_running     ← phase = RUNNING;
  }
}
"""

exemple_accumulator = """
accumulator {
  # Reçoit un bag de valeurs numériques et émet leur somme.
  # Illustre : I:, traitement séquentiel du bag, is_last, phase EMIT.

  P: (initial_offset) ∈ (R) = (0.0);

  S: (phase, total) ∈ (< IDLE, EMIT >, R) = (IDLE, initial_offset);

  X: {
    (in_value, (v)) | (R);
    (in_reset, ()) | ();
  }

  Y: {
    (out_sum, (s)) | (R);
  }

  delta_int: {
    # Après émission, retour en veille.
    (EMIT, total) → (IDLE, total);
  }

  delta_ext: {
    I: (partial_sum) ∈ (R) = (0.0);

    behavior: {
      # Événement intermédiaire : accumule dans I:, reste IDLE.
      (IDLE, total) ∪ (partial_sum), e, (in_value, (v)), ⊥
        → (IDLE, total) ∪ (partial_sum + v);

      # Dernier in_value : valide dans S: et programme l'émission.
      (IDLE, total) ∪ (partial_sum), e, (in_value, (v)), ⊤
        → (EMIT, total + partial_sum + v) ∪ (0.0);

      # Reset intermédiaire : remet I: à zéro, S: inchangé.
      (IDLE, total) ∪ (partial_sum), e, (in_reset, ()), ⊥
        → (IDLE, total) ∪ (0.0);

      # Reset final : remet S: à initial_offset et programme l'émission.
      (IDLE, total) ∪ (partial_sum), e, (in_reset, ()), ⊤
        → (EMIT, initial_offset) ∪ (0.0);
    }

    order: {
      # Les valeurs sont comptabilisées avant le reset.
      (in_value, (_)) < (in_reset, ()) <=> ⊤;
    }
  }

  delta_con: delta_ext ∘ delta_int

  ta: {
    (EMIT, _) → 0;   # Émission immédiate après le dernier événement du bag.
    (IDLE, _) → +∞;  # Passif entre les bags.
  }

  lambda: {
    # Émet le total validé sur out_sum.
    (EMIT, total) → { (out_sum, (total)) };
  }

  obs: {
    running_total ← total;
    is_emitting   ← phase = EMIT;
  }
}
"""

exemple_fifo = """
fifo_queue {
  # File d'attente FIFO avec capacité maximale.
  # Illustre : array variable, [H|T], ∪, ∖, |q|, gardes,
  #            phases de notification FULL et EMPTY.

  P: (capacity) ∈ (N*) = (5);

  S: (phase, queue)
     ∈ (< IDLE, SERVING, NOTIFY_FULL, NOTIFY_EMPTY >,
        [ (id, payload) ∈ (N, R) ])
     = (IDLE, ∅);

  X: {
    (in_enqueue, (id, payload)) | (N, R);
    (in_dequeue, ()) | ();
  }

  Y: {
    (out_item,  (id, payload)) | (N, R);
    (out_full,  ()) | ();
    (out_empty, ()) | ();
  }

  delta_int: {
    # Après émission d'un item : retire la tête et retourne IDLE.
    (SERVING, [_ | rest]) → (IDLE, rest);

    # Après notification FULL : retour passif, file inchangée.
    (NOTIFY_FULL, queue) → (IDLE, queue);

    # Après notification EMPTY : retour passif, file vide.
    (NOTIFY_EMPTY, _) → (IDLE, ∅);
  }

  delta_ext: {
    behavior: {
      # Enfilage accepté, file non pleine après ajout.
      (IDLE, queue), e, (in_enqueue, (id, pl))
        → (IDLE, queue ∪ [(id, pl)])
        | | queue | + 1 < capacity;

      # Enfilage qui sature la file : notifie FULL.
      (IDLE, queue), e, (in_enqueue, (id, pl))
        → (NOTIFY_FULL, queue ∪ [(id, pl)])
        | | queue | + 1 = capacity;

      # Défilage sur file non vide : émet l'item.
      (IDLE, [h | t]), e, (in_dequeue, ()) → (SERVING, [h | t]);

      # Défilage qui vide la file : notifie EMPTY.
      # La file a exactement 1 élément : après retrait elle sera vide.
      (IDLE, [(id, pl)]), e, (in_dequeue, ()) → (NOTIFY_EMPTY, ∅);

      # Défilage sur file déjà vide : notifie EMPTY.
      (IDLE, ∅), e, (in_dequeue, ()) → (NOTIFY_EMPTY, ∅);
    }

    order: {
      # Défilage traité avant enfilage.
      (in_dequeue, ()) < (in_enqueue, (_, _)) <=> ⊤;
    }
  }

  delta_con: delta_ext ∘ delta_int

  ta: {
    (SERVING,      _) → 0;  # Émission immédiate de l'item.
    (NOTIFY_FULL,  _) → 0;  # Notification immédiate : file pleine.
    (NOTIFY_EMPTY, _) → 0;  # Notification immédiate : file vide.
    (IDLE,         _) → +∞;
  }

  lambda: {
    # Émet la tête de file.
    (SERVING, [(id, pl) | _]) → { (out_item, (id, pl)) };

    # Notifie que la file est pleine.
    (NOTIFY_FULL, _) → { (out_full, ()) };

    # Notifie que la file est vide.
    (NOTIFY_EMPTY, _) → { (out_empty, ()) };
  }

  obs: {
    queue_length ← | queue |;
    is_full      ← | queue | = capacity;
    is_empty     ← | queue | = 0;
  }
}"""

MODEL_NAME = "dynamic router"

prompt = f"""<|system|>
Tu es un expert du formalisme Parallel-DEVS et du langage FPDEVSML.
Ta tâche est de produire un modèle atomique FPDEVSML complet, correct et lisible
à partir de la description textuelle ci-dessous.

════════════════════════════════════════════
DESCRIPTION DU MODÈLE À PRODUIRE
════════════════════════════════════════════
{query}

════════════════════════════════════════════
CONTRAINTES DE PRODUCTION — À RESPECTER IMPÉRATIVEMENT
════════════════════════════════════════════

Avant d'écrire le moindre code, effectue les étapes suivantes dans l'ordre :

  ÉTAPE 1 — ANALYSE SÉMANTIQUE
  Identifie et liste explicitement :
    • les entités métier du problème (objets, acteurs, ressources)
    • les phases du cycle de vie du composant (états qualitatifs)
    • les variables quantitatives (compteurs, durées, files)
    • les événements entrants et sortants avec leur contenu
    • les règles causales (quand X se produit, Y est déclenché)
    • les contraintes temporelles (délais, timeouts, periodicité)

  ÉTAPE 2 — PLAN DU MODÈLE
  Décris en langage naturel, avant d'écrire le FPDEVSML :
    • la liste des paramètres P: avec leur rôle et leur type
    • la liste des variables d'état S: avec leur domaine
    • les ports X: et Y: avec le type de payload de chaque port
    • le cycle de vie : quelles transitions (int/ext/con) changent quoi
    • la stratégie delta_con choisie et sa justification
    • les invariants que le modèle doit vérifier

════════════════════════════════════════════
RÈGLES DE GÉNÉRATION DU CODE FPDEVSML
════════════════════════════════════════════

A — CONFORMITÉ SYNTAXIQUE (ordre et délimiteurs)

  A1. Respecte strictement l'ordre des sections :
      P: → S: → X: → Y: → delta_int: → delta_ext: → delta_con: → ta: → lambda: → obs:
      Toutes les accolades {{}} doivent être correctement appariées.
      La section ta: est OBLIGATOIRE et ne doit jamais être vide.

  A2. Utilise les bons constructeurs de domaine :
      • ()   → tuple
      • []   → array (ordonné, doublons autorisés) ; [D @ N] si taille fixe
      • {{}}   → set (non ordonné, sans doublons)
      • <>   → symbol set (énumération qualitative)
      • ≪≫   → map (association clé → valeur)
      Ne confonds jamais ces constructeurs entre eux.

  A3. Syntaxe des règles de transition :
      • Format : (pre_state) → (post_state) [quantificateurs] [| garde] ;
      • Dans delta_ext AVEC I: : (S_pre) ∪ (I_pre), e, event, last_flag → (S_post) ∪ (I_post)
      • Dans delta_ext SANS I: : (S_pre), e, event → (S_post)
      • Opérateurs : →  ∘  ∪  ∖  (utiliser les bons caractères Unicode)

  A4. Quantificateurs et gardes :
      • Syntaxe : ∀/∃/∄ var ∈ collection / prédicat
      • La garde | expr se place APRÈS tous les quantificateurs
      • ∄ est distinct de ¬∃ ; ne pas substituer l'un à l'autre
      • Les variables liées par ∃ sont accessibles dans la garde et le post-état

  A5. Expressions :
      • Projection tuple : π_i(expr)  (index base 1)
      • Indexation array : [arr : k]
      • Accès map : ≪map : clé≫
      • Cardinalité : |collection|
      • Ne jamais mélanger types booléens et numériques dans une expression

B — COMPLÉTUDE STRUCTURELLE

  B1. La section ta: doit couvrir toutes les phases possibles de S:.
      Chaque port déclaré en X: doit apparaître dans au moins une règle de delta_ext.
      Chaque port déclaré en Y: doit apparaître dans au moins une règle de lambda.

  B2. Cohérence ports ↔ transitions :
      • Tout port utilisé dans un event pattern ou un output event doit être
        déclaré dans X: ou Y: avec le bon domaine de payload.
      • Les multi-ports (* expr) dans les règles correspondent exactement
        aux multi-ports déclarés.

  B3. (Sans objet pour un modèle purement atomique — s'assurer que les ports
      sont dimensionnés pour s'intégrer dans un couplage logique.)

  B4. Les valeurs par défaut de P: doivent être sémantiquement cohérentes
      avec le problème décrit (pas de 0 là où une durée strictement positive
      est attendue, etc.).

C — CORRECTION SÉMANTIQUE

  C1. Cohérence ta / phases / sigma :
      • ta: retourne +∞ pour tout état passif (en attente d'événement externe)
      • ta: retourne une valeur finie (sigma, ou une expression) pour tout état actif
      • Si sigma ∈ S:, il doit être décrémenté de e dans chaque règle de
        delta_ext qui le concerne : sigma - e

  C2. delta_int :
      • Toute phase active (ta < +∞) a au moins une règle dans delta_int
      • Ordre first-match-wins : règles les plus spécifiques (avec constantes)
        placées avant les règles génériques (avec wildcards)
      • Le post-état doit être typiquement cohérent avec les domaines de S:

  C3. delta_ext :
      • L'event pattern doit correspondre exactement au port et au domaine
        déclarés dans X:
      • Décrémenter sigma de e lorsque le modèle est actif pendant l'attente
      • Si I: est défini, il est ré-initialisé implicitement à chaque appel ;
        combiner avec ∪ en pre et post de chaque règle du behavior:

  C4. delta_con :
      • Choisir la stratégie selon la priorité sémantique :
        - delta_int ∘ delta_ext : l'événement interne se produit d'abord (output émis),
          puis l'entrée externe est traitée sur le nouvel état
        - delta_ext ∘ delta_int : l'entrée externe est prioritaire ; l'interne suit
        - delta_int seul : ignorer l'entrée externe (cas rare, événement critique)
        - delta_ext seul : annuler l'interne (comportement DEVS classique)
      • Commenter le choix.

  C5. lambda :
      • N'émettre des événements que pour les phases où ta est fini
      • Les payloads doivent correspondre exactement aux domaines de Y:
      • Si ∀ est utilisé, chaque itération génère un événement distinct

D — QUALITÉ DE MODÉLISATION

  D1. Le modèle doit capturer fidèlement la dynamique décrite :
      timing, causalité, flux de données. Ni sur-ingénierie (phases inutiles),
      ni simplification (phases manquantes).

  D2. Pas de règles mortes : toute règle de delta_int/delta_ext/lambda doit
      être atteignable depuis l'état initial par au moins un scénario.
      Pas de chevauchement ambigu entre règles sans ordre justifié.

  D3. Si plusieurs événements peuvent arriver simultanément sur des ports
      différents, fournir un order: complet couvrant toutes les paires
      concurrentes avec une condition <=> justifiable.

  D4. Choisir le bon type de collection :
      • map ≪≫ pour des associations clé → valeur (lookup, routing)
      • array [] pour des séquences ordonnées (FIFO, files d'attente)
      • set {{}} pour des collections sans ordre ni doublons
      • Utiliser @ N pour les tableaux à taille fixe connue

E — LISIBILITÉ, NOMMAGE ET COMMENTAIRES

  E1. Conventions de nommage :
      • Variables d'état : noms reflétant leur rôle métier
        (jobs, sigma, capacity — pas x, s1, tmp)
      • Ports : préfixe in_/out_ systématique, nom du signal transporté
        (in_job, out_result — pas p1, p2)
      • Paramètres : nom lisible, unité mentionnée si pertinent
        (processing_time, capacity — pas d, pt)
      • Phases / symbol sets : SCREAMING_SNAKE_CASE
        (WAIT, SEND_AVAILABLE — pas w, sa)
      • Les entités métier du problème doivent être reconnaissables
        dans les identifiants sans traduction (job, machine, patient…)

  E2. Commentaires obligatoires (avec #) :
      • En-tête : bloc décrivant le rôle du composant dans le système
      • P: et S: : explication des champs non évidents
      • X: et Y: : description du payload si complexe
      • delta_con: : justification de la stratégie choisie
      • Règles non triviales : confluences, gardes complexes, priorités,
        usage de I:, quantificateurs imbriqués
      • NE PAS commenter les règles syntaxiquement évidentes
        (ne pas rephraséer ce que le code dit déjà)

  E3. Factorisation :
      • Regrouper les règles similaires ; ne pas dupliquer
      • Utiliser _ (wildcard) systématiquement pour les composants du
        pre-state qui ne sont pas lus dans le post-état
      • Factoriser avec ∀ et multi-ports (* N) partout où c'est pertinent

════════════════════════════════════════════
FORMAT DE SORTIE ATTENDU
════════════════════════════════════════════

Produis ta réponse en TROIS BLOCS dans cet ordre :

  BLOC 1 — ANALYSE (étapes 1 et 2 ci-dessus)
  BLOC 2 — MODÈLE FPDEVSML (code brut, prêt à être parsé)
  BLOC 3 — AUTO-VÉRIFICATION
    Pour chacun des points suivants, indique ✓ ou ✗ + explication si ✗ :
      [ ] ta: couvre toutes les phases de S:
      [ ] Chaque port X: apparaît dans au moins une règle de delta_ext
      [ ] Chaque port Y: apparaît dans au moins une règle de lambda
      [ ] sigma est décrémenté de e dans delta_ext si le modèle est actif
      [ ] delta_con est justifié par un commentaire
      [ ] Aucune règle morte ou chevauchement ambigu
      [ ] order: fourni si événements simultanés possibles
      [ ] Nommage conforme aux conventions E1
      [ ] Commentaires présents aux endroits requis par E2
      [ ] Wildcards _ utilisés pour les champs ignorés

Documentation :
{context}

Exemple 1 (modèle avec entrée) :
{exemple_reference}

Exemple 2 (modèle Basculeur binaire, états booléens, delta_ext simple sans I:, ta passif) :
{exemple_binaire}

Exemple 3 (modèle sigma explicite, delta_ext qui recharge le timer, delta_int qui expire, ta basé sur variable d'état.)
{exemple_minuterie}

Exemple 4 (modèle section I:, traitement de bag d'événements, flag is_last (⊤/⊥), commit final)
{exemple_accumulator}

<|end|>
<|assistant|>
{MODEL_NAME}"""

# ── LLM — PAS de grammaire, génération libre ──────────────────────────────────
llm = Llama(
    model_path=model_path_phi4,
    n_ctx=16384,
    n_gpu_layers=20,
    verbose=False,
)

try:
    grammar = LlamaGrammar.from_string(gbnf_grammar)
    print("Grammaire OK")
except Exception as e:
    print(f"Erreur grammaire : {e}")

output = llm(
    prompt,
#    grammar=grammar,
    max_tokens=16384,
    temperature=0.0,
    repeat_penalty=1.1,
    top_k=40,
    top_p=0.9,
    stop=["<|end|>"],
    echo=False
)

raw = output["choices"][0]["text"]

# ── Post-traitement : extraire le bloc entre la première { et la dernière } ───
def extract_model(raw: str, model_name: str) -> str:
    full = f"{model_name} {{{raw}"
    depth = 0
    end_idx = -1
    for i, ch in enumerate(full):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end_idx = i
                break
    if end_idx != -1:
        return full[:end_idx + 1]
    # Fallback : couper à la dernière }
    last = full.rfind("}")
    return full[:last + 1] if last != -1 else full


final_model = extract_model(raw, MODEL_NAME)

print("─── Modèle ATOMIC généré ───────────────────────────────────────────────")
print(final_model)
print("────────────────────────────────────────────────────────────────────────")
