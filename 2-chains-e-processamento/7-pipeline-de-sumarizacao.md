# 7 - Pipeline de Sumarização (Map-Reduce) — Visual Guide

## 1. The big picture

```mermaid
flowchart TD
    A["📄 long_text<br/><i>str (one big string)</i>"]
    A --> B["✂️ RecursiveCharacterTextSplitter<br/>chunk_size=300, chunk_overlap=50<br/><code>splitter.create_documents([long_text])</code>"]
    B --> C["parts<br/><i>list[Document]</i><br/>[Doc1, Doc2, ..., DocN]"]

    subgraph MAP["🗺️ MAP STAGE — map_stage = prepare_map_inputs | map_chain.map()"]
        direction TB
        D["prepare_map_inputs (RunnableLambda)<br/>Document → {'context': page_content}"]
        E["<i>list[dict]</i><br/>[{'context': chunk1}, ..., {'context': chunkN}]"]
        D --> E

        E --> M1 & M2 & M3

        subgraph PAR["map_chain.map() — runs map_chain once PER item (in parallel)"]
            direction LR
            M1["map_chain(chunk1)<br/>prompt → llm → parser"]
            M2["map_chain(chunk2)<br/>prompt → llm → parser"]
            M3["... map_chain(chunkN)"]
        end

        M1 --> S["<i>list[str]</i><br/>['summary1', 'summary2', ..., 'summaryN']"]
        M2 --> S
        M3 --> S
    end

    C --> D

    subgraph REDUCE["🧩 REDUCE STAGE — reduce_stage = prepare_reduce_inputs | reduce_chain"]
        direction TB
        R1["prepare_reduce_inputs (RunnableLambda)<br/>'\n'.join(summaries)"]
        R2["<i>dict</i><br/>{'context': 'summary1\nsummary2\n...summaryN'}"]
        R3["reduce_chain<br/>reduce_prompt → llm → StrOutputParser"]
        R1 --> R2 --> R3
    end

    S --> R1
    R3 --> F["✅ final_summary<br/><i>str</i>"]

    classDef data fill:#e8f4ff,stroke:#3b82f6,color:#0b2545
    classDef step fill:#fff7e6,stroke:#f59e0b,color:#3d2a00
    classDef llm fill:#eafaf0,stroke:#10b981,color:#05391f
    class A,C,E,S,R2,F data
    class B,D,R1 step
    class M1,M2,M3,R3 llm
```

**Legend:** 🔵 blue = data (what's flowing) · 🟠 orange = plain Python transforms · 🟢 green = LLM calls

---

## 2. What's inside `map_chain` and `reduce_chain`

Both are the same shape (`prompt | llm | parser`); only the prompt text differs.

```mermaid
flowchart LR
    I["{'context': '...'}"] --> P["PromptTemplate<br/>fills {context} in the template"]
    P --> L["ChatOpenAI (gpt-5-nano)<br/>returns AIMessage"]
    L --> O["StrOutputParser<br/>AIMessage → str"]
    O --> R["'summary text'"]
```

| Chain          | Prompt                                                   | Called how many times? |
|----------------|----------------------------------------------------------|------------------------|
| `map_chain`    | "Write a concise summary of the following text:"         | **N** (once per chunk) |
| `reduce_chain` | "Combine the following summaries into a single concise…" | **1**                  |

---

## 3. What does `.map()` do?

`map_chain.map()` takes a chain that handles **one** input and makes it handle a **list** of inputs.
It's the LCEL version of a list comprehension:

```python
# These two do the same thing (except .map() runs the calls in parallel):
map_chain.map().invoke(list_of_dicts)
[map_chain.invoke(d) for d in list_of_dicts]
```

---

## 4. How the data changes shape

```mermaid
flowchart LR
    T1["str"] -->|splitter| T2["list[Document]"]
    T2 -->|prepare_map_inputs| T3["list[dict]"]
    T3 -->|"map_chain.map()"| T4["list[str]"]
    T4 -->|prepare_reduce_inputs| T5["dict"]
    T5 -->|reduce_chain| T6["str"]
```

Most of the confusing parts come from this: each `RunnableLambda` exists only to **reshape the data** so the next step gets the input it expects.
`PromptTemplate` expects a `dict` with a `context` key, so:
- before the map, `Document` objects are turned into `{"context": ...}` dicts
- before the reduce, the list of summaries is joined into one string and wrapped in `{"context": ...}`

---

## 5. The last line, unpacked

```python
final_summary = reduce_stage.invoke(map_stage.invoke(parts))
```

is equivalent to:

```python
summaries     = map_stage.invoke(parts)        # list[str]   (N LLM calls)
final_summary = reduce_stage.invoke(summaries) # str         (1 LLM call)
```

You could also compose them into one pipeline: `(map_stage | reduce_stage).invoke(parts)`.
