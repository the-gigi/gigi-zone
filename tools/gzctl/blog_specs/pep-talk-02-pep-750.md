PEP Talk #2. Slug: pep-talk-02-pep-750.

The article covers PEP 750: Template Strings (t-strings), new in Python 3.14. This is one of the most exciting PEPs in recent memory because it adds a fundamentally new string processing primitive to the language.

Key content points:
1. The Problem: f-strings evaluate eagerly and concatenate immediately. There's no way to intercept the values before they become part of the final string. This makes f-strings dangerous for SQL, HTML, and other contexts where naive interpolation causes security vulnerabilities (injection attacks) or correctness bugs.

2. Wait, doesn't Python already have string.Template? Yes, since Python 2.4. Compare and contrast:
   - string.Template does $-placeholder substitution on plain strings
   - It has no access to the actual Python objects, just their string representations
   - No expression support, no format specs, no conversion flags
   - PEP 750's Template is a language-level feature that captures real Python values with full expression syntax
   - The naming overlap is unfortunate (string.Template vs string.templatelib.Template)

3. What t-strings are: same syntax as f-strings but with a t prefix. Produces a Template object instead of a str. The Template holds the static string parts and the interpolated values separately.

4. The Template anatomy: Template has `strings` (the static parts) and `values` (Interpolation objects with value, expression text, conversion, and format_spec). Walk through a concrete example showing what the Template object looks like.

5. Real-world use cases with code examples:
   - SQL parameterization (preventing injection)
   - HTML escaping (XSS prevention)
   - Structured logging (keeping template and values separate for indexing)
   - i18n/localization

6. How to process Templates: writing a function that consumes a Template object. Show the pattern of iterating over strings and values.

7. Connection to PEP 701: the f-string grammar formalization in Python 3.12 (PEP 701) made t-strings possible since they share the same parser infrastructure.

Series format: PEP Talk series structure (emoji-wrapped H2 headers, hook+quote opening, series index, Take Home Points, closing greeting in Swedish).

Categories: Python, PEP, Template Strings
Date: 2026-04-03

Images:
- hero.png: vibrant hero image with Python logo and template/string theme
- template-anatomy.png: xkcd-style diagram showing a t-string being parsed into a Template object with its strings and Interpolation values
- f-vs-t.png: xkcd-style diagram comparing f"..." (eager evaluation to str) vs t"..." (lazy capture to Template object)
