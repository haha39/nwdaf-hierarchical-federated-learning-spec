# ACM `sigconf` LaTeX preview

This guide covers local presentation checks, not manuscript content or technical scope. Each paper may use its own canonical source, LaTeX filenames, and directory layout. The preview needs a LaTeX entry file and any files it includes, such as section text and figures.

The Dockerfile in `tools/paper_latex_preview/` is the portable build artifact. The image `acm-sigconf-tex:2026` is an optional local cache; build it only if absent. The commands below assume a POSIX-compatible shell. Build from the directory containing `tools/paper_latex_preview/`:

```sh
docker build -t acm-sigconf-tex:2026 tools/paper_latex_preview
```

The Dockerfile pins the validated TeX Live 2026 base and installs the validated package set. Do not install broad TeX Live collections for routine recompilation. From the directory containing your entry file and its relative assets, run the following command twice (substitute your entry filename if it is not `main.tex`):

```sh
docker run --rm --network none --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work acm-sigconf-tex:2026 pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

Check the generated `.log` for errors, unresolved references, and overfull boxes. Inspect the PDF for figure readability, clipping, and pagination. Report layout problems for author judgment rather than silently changing fonts, margins, spacing, or line breaks. Keep figure paths relative to the TeX working directory; regenerate derived figures only when their source changes.

After validation, retain the source files and preview PDF; keep the optional image cache if it will be reused. The generated `.aux`, `.out`, and `.log` files and temporary page-render PNGs may be removed. Preview placeholder metadata is not publication metadata.
