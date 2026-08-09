# How to Write Good Prompts

## The Problem

❌ **Vague prompt:** `> Explain this file`
- Result: Rambling, repetitive, hard to read

✅ **Specific prompt:** `> What does this file do in 3 bullet points?`
- Result: Clear, organized, readable

## The Formula

```
[ACTION] [SPECIFICS] [CONSTRAINTS]
```

**Example:**
```
Write a Python function that validates emails:
- Returns True/False
- Handles edge cases (empty, no @)
- Keep it under 10 lines
- Include type hints
```

## Rules

### 1. Be Specific
```
❌ Improve this        ✅ Add retry logic with exponential backoff
❌ Write a test        ✅ Write 3 tests: normal, edge case, error
❌ Explain this        ✅ Explain in 3 bullet points what, why, how
```

### 2. Add Constraints
```
✅ Keep it under 15 lines
✅ Maximum 3 parameters
✅ In 2-3 sentences
✅ Under 100 characters
```

### 3. Use @file Context
```
✅ Looking at @src/codesmith/llm.py, add retry logic to generate()
✅ Based on patterns in @src/codesmith/tools.py, write similar function
```

### 4. Specify Format
```
✅ As JSON
✅ As bullet points
✅ As a class
✅ Google docstring style
```

### 5. Show Success Criteria
```
✅ Should return 6 when input is [1,2,3]
✅ Should handle empty list without error
✅ Should raise ValueError if input is None
```

## Templates

### For Code
```
Write a [language] function that:
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]
Keep it under [N] lines, include type hints.
```

### For Tests
```
Write [N] tests for [function]:
- Test [scenario 1]
- Test [scenario 2]  
- Test [scenario 3]
Use [framework], keep focused.
```

### For Docs
```
Write a [style] docstring that includes:
- Purpose
- Parameters
- Return value
- Exceptions
Keep under [N] lines.
```

### With Context
```
Looking at @file, [action]:
- [Specific change 1]
- [Specific change 2]
Keep existing API unchanged.
```

## Real Examples

### Example 1: Explain Code

❌ `> Explain examples/demo.py`
✅ `> What does examples/demo.py do? 4 bullet points: what it imports, main function, how to run, expected output`

### Example 2: Generate Code

❌ `> Write a test`
✅ `> Write 3 unit tests for factorial: test(5)→120, test(0)→1, test(-1)→ValueError. Use unittest, 4 lines each.`

### Example 3: With File Context

❌ `> Improve the error handling`
✅ `> Looking at @src/codesmith/llm.py, add retry logic: retry 3x on timeout, exponential backoff (1s, 2s, 4s), log each retry`

## Common Mistakes

| ❌ Bad | ✅ Good |
|------|-------|
| "Explain this" | "Explain in 3 points" |
| "Write code" | "Write function that validates X" |
| "Add tests" | "Write 3 tests covering normal, edge, error cases" |
| "Improve this" | "Add error handling for FileNotFoundError" |
| "Fix the bug" | "Fix: when input is empty, returns error instead of []" |

## When Response Is Bad

**If response is rambling/repetitive:**
- Add length limit: "2-3 sentences max"
- Specify format: "As bullet points"
- Be more specific about what you want

**If response is off-topic:**
- Add context: "Looking at @file.py..."
- Be clearer: "Fix THIS specific issue"

**If response is incomplete:**
- Add specifics: "Include error handling, logging, type hints"
- Example: "Should work like: input X → output Y"

## How File Context Works

Mention files with `@` in any regular prompt. CodeSmith reads those files for
that prompt only, so mention them again when a later prompt also needs them.

### Valid File Mentions

✅ **Standard format:**
```
"I need to see @src/codesmith/llm.py to understand the integration"
"Can you show me @src/codesmith/tools.py?"
```

✅ **With extension:**
```
"Looking at @config.json, I can see..."
"I need @README.md for context"
```

✅ **Multiple files:**
```
"I need @file1.py and @file2.py to compare"
"Show me @src/codesmith/cli.py, @src/codesmith/tools.py, and @src/codesmith/llm.py"
```

### How CodeSmith Handles Mentions

| Case | Example | Behavior |
|------|---------|----------|
| Valid filename | `"Explain @src/codesmith/cli.py"` | ✓ Includes the file in this prompt |
| Multiple files | `"Compare @file1.py and @file2.py"` | ✓ Includes both in this prompt |
| Unclear request | `"Can you show me @?"` | ⚠️ Skipped - filename not clear |
| Non-existent file | `"@missing.py"` | ⚠️ Error shown - file not found |
| No filename | `"Need @ to help"` | ⚠️ Unclear request - add filename |

### Example

```
> Explain how commands are parsed in @src/codesmith/cli.py
> Compare file handling in @src/codesmith/cli.py and @src/codesmith/tools.py
```

---

## Quick Checklist

Before asking, check:
- [ ] Is it specific? (not just "improve this")
- [ ] Do I have @file context if needed?
- [ ] Did I specify constraints?
- [ ] Could someone else understand what I want?

---

**TL;DR:** Specific, constrained prompts = readable, useful responses ✅
