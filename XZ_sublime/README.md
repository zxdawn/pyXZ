# XZ_sublime

Some useful settings of my own Sublime Text 3.

## ENV

### System environment variables

```
E:\miniconda3\Library\bin
E:\miniconda3\envs\satpy\Library\bin
E:\SumatraPDF
E:\wkhtmltopdf\bin
E:\imagemagic\ImageMagick-7.0.8-Q16
C:\texlive\2018\bin\win32
C:\texlive\2018\tlpkg\tlgs\bin

```

### satpy.sublime-build

```
{
    "cmd": ["E:\\miniconda3\\envs\\satpy\\python.exe", "$file"],
    "selector": "source.python",
    "file_regex": "^[ ]*File \"(...*?)\", line ([0-9]*)",
}
```

## General settings

```
{
    "dictionary": "Packages/Language - English/en_US.dic",
    "font_size": 18,
    "ignored_packages":
    [
        "Vintage"
    ],
    "spell_check": true,
    "rulers":
    [
        72,
        79
    ],
    "font_size": 18,
    "ensure_newline_at_eof_on_save": true,
    "scroll_past_end": true,
    "tab_size": 4,
    "translate_tabs_to_spaces": true,
    "trim_trailing_white_space_on_save": true,
    "isort.sort_on_save": false,
}
```

### Key Bindings

```
[
	{ "keys": ["ctrl+tab"], "command": "next_view" },
	{ "keys": ["ctrl+shift+tab"], "command": "prev_view" },
]
```

## Packages

### [Package Control](https://packagecontrol.io/installation#Manual)

### Anaconda

```
{
    /*
        No Autoformatting
    */
    "auto_formatting": false,
    "autoformat_ignore":
    [
        "E309",
        "E501"
    ],
    "pep8_ignore":
    [
        "E309",
        "E501"
    ],
    /*
        No Linting (this is done by sublinter-flake8)
    */
    "anaconda_linting": false,
    "anaconda_linter_underlines": false,
    "anaconda_linter_mark_style": "none",
    "display_signatures": true,
    /*
        Use anaconda for code completion
        Suppress sublime completions
    */
    "disable_anaconda_completion": false,
    "suppress_word_completions": true,
    "suppress_explicit_completions": true,
    /*
        Others
    */
    "complete_parameters": false
}
```

### [Sublime linter](https://packagecontrol.io/packages/SublimeLinter)

```
// SublimeLinter Settings - User
{
    "linters": {
        "flake8": {
            "executable": ["E:\\miniconda3\\envs\\satpy\\python.exe", "-m", "flake8"],
        }
    },
    "show_panel_on_save": "never",
"gutter_theme": "Packages/Theme - Monokai Pro/Monokai Pro.gutter-theme",
    "styles": [
        {
            "mark_style": "outline",
            "priority": 1,
            "scope": "region.orangish",
            "icon": "warning",
            "types": [
                "warning"
            ]
        },
        {
            "mark_style": "squiggly_underline",
            "priority": 1,
            "scope": "region.redish",
            "icon": "error",
            "types": [
                "error"
            ]
        }
    ]
}
```

### [GitGutter](https://packagecontrol.io/packages/GitGutter)

```
// GitGutter Settings - User
{
    "theme": "Monokai Pro.gitgutter-theme",
    "protected_regions": [
        "sublimelinter-warning-gutter-marks",
        "sublimelinter-error-gutter-marks",
        "sublime_linter.protected_regions"
    ]
}
```

### [Latex Tools](https://github.com/SublimeText/LaTeXTools)

```
	"windows": {
		// Path used when invoking tex & friends; "" is fine for MiKTeX
		// For TeXlive 2011 (or other years) use
		// "texpath" : "C:\\texlive\\2011\\bin\\win32;$PATH",
		"texpath" : "E:\\texlive_2020\\bin\\win32;$PATH",
		// TeX distro: "miktex" or "texlive"
		"distro" : "texlive",
		// Command to invoke Sumatra. If blank, "SumatraPDF.exe" is used (it has to be on your PATH)
		"sumatra": "E:\\sumatra\\SumatraPDF",
		// Command to invoke Sublime Text. Used if the keep_focus toggle is true.
		// If blank, "subl.exe" or "sublime_text.exe" will be used.
		"sublime_executable": "",
		// how long (in seconds) to wait after the jump_to_pdf command completes
		// before switching focus back to Sublime Text. This may need to be
		// adjusted depending on your machine and configuration.
		"keep_focus_delay": 0.5
	},

     "builder": "simple",
```

### [Terminus](https://packagecontrol.io/packages/Terminus)

### [isort](https://packagecontrol.io/packages/isort)

## References

1. [Ultimate Sublime for Python](https://blog.usejournal.com/ultimate-sublime-for-python-5c531224421b)