+++
title = 'Auto Web Login - Part II'
date = 2024-10-26T17:00:00-07:00
+++

In this episode, lazy man🚶‍ Gigi can't be bothered to manage two collections of items in a
TamperMonkey 🐒 script, so he is forced to write a Python 🐍 program to generate the script.

If you're impatient the complete source code for the entire project is available here:
https://github.com/the-gigi/auto-web-login

**"Laziness is the mother of invention."**
~ Anonymous

<!--more-->

![](images/hero.png)

# 🔄 Recap 🔄

In [Auto Web Login - Part I](https://the-gigi.github.io/gigi-zone/posts/2024/09/auto-web-login-part-1/)
we learned how to use TamperMonkey to automatically click buttons on a web page. But, the script was
pretty gnarly 🤢. It had two collections of items that must be updated whenever we want to click on a
button in a new page. At the top the target web page must be added with a special comment like:

```shell
// @include      https://device.sso.*.amazonaws.com/*
```

Then, in the config section, we must add a query with nasty regex that includes a lot of escaped
slashes to locate the button on the page like:

```shell
{
  regex: /https:\/\/device\.sso\..*\.amazonaws\.com\/.*/,
  findButton: () => document.getElementById('cli_verification_btn')
},
```

That's waaaaay too much work, man! 😡

Enter Python!

# 🐍 Snakes 🐍

Why keep two things in sync if Python can generate both from a simple config file? Let's make Python
do all the work for us and generate the TamperMonkey script. First, let's define a simple config
file that will contain the URL and the button finding logic. The key is a regex of the page URL (
same as the `@include` in the TamperMonkey script) and the value is a list of JavaScript code
snippets that will find the button on the page. The reason there is a list of expressions is that
there may be multiple different buttons to click on pages that match the same URL pattern.

```python
# The buttons on these pages need to be clicked (keys must use wildcards only)
url_buttons_dict = {
    "https://device.sso.*.amazonaws.com/*": [
        "document.getElementById('cli_verification_btn')"],
    "https://d-*.awsapps.com/start/*": [
        "document.getElementById('cli_login_button')",
        "document.querySelector('button[data-testid=\"allow-access-button\"]')"
    ],
}
```

👍 **Alright**, with that out of the way we can write the Python code to generate the TamperMonkey
script.

🔄 From now on, we never need to touch the TamperMonkey script again. We can just update the config
file and run the Python code to generate the updated **TamperMonkey** script.

👨‍💻 Let's check out the code. The main function is called `generate_tampermonkey_script()`. It has a few
parts:

- generate includes from the Python config file
- generate the url matching config from the Python config file
- embed the generated value in a big text template to generate the TamperMonkey script
- remove trailing spaces and newlines

Let's break it down by piece. First, it gets today's date, which will be used to date the script.
Then
itgenerates all the `@include` lines from the Python config file. Next, it generates the
URL-to-buttons.

```python
def generate_tampermonkey_script():
# Get today's date in YYYY-MM-DD format
today = datetime.now().strftime("%Y-%m-%d")

    # Generate the @include lines and URL-to-buttons mapping for the script
    includes = "\n".join([f"// @include      {pattern}" for pattern in url_buttons_dict])
    generated_config = generate_all_pattern_handling_config(url_buttons_dict)
    # Indent 4 more spaces
    generated_config = generated_config.replace("\n", "\n    ").rstrip()
    delay_ms = int(config.delay_seconds * 1000)
```

The next part is taking all the generated values and embedding them in a big text template that uses
Python's awesome [f-string](https://docs.python.org/3/reference/lexical_analysis.html#f-strings)
feature. Check
out [part I](https://the-gigi.github.io/gigi-zone/posts/2024/09/auto-web-login-part-1/) for a full
explanation of the script.

```python
    # Generate the script with config-based pattern handling
    script = f"""// ==UserScript==
// @name         auto-web-login
// @namespace    http://tampermonkey.net/
// @version      {today}
// @description  Automatically click the buttons when doing web login
// @author       the.gigi@gmail.com
// @grant        none
{includes}
// ==/UserScript==

(function() {{
    'use strict';

    var maxAttempts = 20;
    var attempt = 0;

    function sleep(ms) {{
        return new Promise(resolve => setTimeout(resolve, ms));
    }}    

    async function handleButton(button) {{
        if (!button) {{
            return false;
        }}
        console.log('Found and clicked button');
        await sleep({delay_ms});
        button.click();
        return true;
    }}

    const config = [{generated_config}
    ];

    async function tryClickButtons() {{
        if (attempt >= maxAttempts) {{
            console.log("Max attempts reached. Stopping.");
            return;
        }}
        attempt++;
        console.log("Attempt:", attempt);
        var currentUrl = window.location.href;

        for (const {{ regex, findButton }} of config) {{
            if (regex.test(currentUrl)) {{
                const button = findButton();
                if (await handleButton(button)) {{
                    return;
                }}
            }}
        }}

        console.log("No button found, trying again in 1 second...");
        setTimeout(tryClickButtons, 1000); // Wait for 1 second before trying again        
    }}

    if (document.readyState === 'complete' || document.readyState === 'interactive') {{
        // If the document is already loaded or nearly loaded, call the function immediately
        tryClickButtons();
    }} else {{
        // Otherwise, wait for the load event
        window.addEventListener('load', tryClickButtons);
    }}
}})();
"""
```

The last part is a minor cleanup to remove trailing spaces and newlines.

```python
    lines = script.split("\n")
    lines = [line.rstrip() for line in lines]
    return "\n".join(lines)
```

OK. This is cool 😎, but the actual heavy lifting happens in
the `generate_all_pattern_handling_config()` function. Let's check it out. It's a pretty small
function with a comment larget than the code :-). I like seeing the end result in front of me when
developing code generation code. It takes as input the URL-to-buttons mapping and generates the
config entries by iterating over the mapping and calling `generate_config_entry()` for each entry.
Note that before calling the function, the URL pattern is converted to a Javascript regex pattern,
because the original format expected by TamperMonkey is a wild card expression.

```python
def generate_all_pattern_handling_config(mapping: Mapping):
    r"""Generate the configuration code for regex and button-finding logic as a config object.

    The format should look like this:
    const config = [
        {
            regex: /https:\/\/device\.sso\.*\.amazonaws\.com\/.*/,
            findButton: () => document.getElementById('cli_verification_btn')
        },
        {
            regex: /https:\/\/d-.*\.awsapps\.com\/start\/.*/,
            findButton: () => document.getElementById('cli_login_button') ||
                              document.querySelector('button[data-testid="allow-access-button"]')
        },
        ...
    ];
    """
    return "".join(generate_config_entry(
        p.replace("/", r"\/").replace(".", r"\.").replace("*", ".*"), q)
                   for p, q in mapping.items()).lstrip()
```

OK, let's move on and check out the `generate_config_entry()` function. Again, a simple function
with
a big comment and small code :-). It's self-explanatory.

```python
def generate_config_entry(pattern, queries):
    r"""Generate a single entry of the config object for the specified pattern and queries.

    The format of a config entry is:
    {
        regex: /<pattern>/,
        findButton: () => <button finding logic>
    }

    Example:
    {
        regex: /https:\/\/device\.sso\.*\.amazonaws\.com\/.*/,
        findButton: () => document.getElementById('cli_verification_btn')
    }
    """
    buttons = " ||\n".join(generate_button_finding_logic(query) for query in queries)
    return f"""
        {{
            regex: /{pattern}/,
            findButton: () => {buttons}
        }},
    """
```

# 📌 Take Home Points 📌

First, this is no rocket science 🚀 . It’s just a simple Python script that generates a TamperMonkey.

I really like the idea 💡 of generating code from a simple config file. This is especially true when
the config is updated often. You never have to worry about inadvertently introducing bugs, typos, or
indentation errors in the code itself, which is generated from a boilerplate developed once. Python
is great for such tasks.

Of course, you can mess up the config ⚠️, but you can verify it if it’s causing issues. I didn’t do
it here, but you should do as I say, not as I do. 😅

A presto, i miei amici! 🎉
