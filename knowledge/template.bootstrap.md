# Starting work with this template

The source checkout for this repository is a **Copier template**. Before any
subnet-specific work in a template checkout, it must be parameterized for the
target subnet.

This document is the source of truth for *how* to render the template. Other
docs (`AGENTS.md`, `knowledge/tasks.project-bootstrap.md`) may mention the
`copier copy` command in passing — when in doubt about the mechanics, follow
this file.

## How to detect the repository state

A checkout is in one of three states. Identify it before doing anything else.

### State A — unrendered template checkout

Either of these markers is present:

- Files with the `.jinja` suffix exist (e.g. `installer/install.sh.jinja`,
  `validator/README.md.jinja`, `envs/deployed/docker-compose.yml.jinja`).
- `copier.yml` is present at the repository root.

Action: render the template (see "Render the template" below).

### State B — rendered, in-place, cleanup pending

This is the trap. You see **both** a `*.jinja` file and its rendered sibling
without the suffix in the same directory — for example, `installer/install.sh`
exists alongside `installer/install.sh.jinja`. `copier.yml` is also still at
the root. This means a previous run did `copier copy . .` (in-place render) and
nobody removed the template inputs afterwards.

Action: run the cleanup from the in-place section below — **do not** re-render.

### State C — rendered, not yet adapted

No `*.jinja` files anywhere, no `copier.yml`, but the docs still look generic.
Typical signs:

- The root `README.md` describes the **Nexus** framework rather than a concrete
  subnet.
- `AGENTS.md` opens with "This project is a template for a Bittensor subnet
  project."

Action: skip rendering — go straight to "After rendering — what an agent should
do" below.

## Render the template

There are two ways to invoke Copier. **Always prefer rendering into a fresh
destination directory.** In-place rendering is a fallback only and requires a
mandatory cleanup step.

### Preferred: render into a fresh directory

The destination must be either an empty directory or a path that does not yet
exist. Pick a sibling path next to the template checkout — do **not** render
inside the template checkout.

```sh
# from a local clone of the template (run from the template root)
uv run --with copier copier copy . ../<new-subnet-repo>

# or directly from GitHub
uv run --with copier copier copy gh:bittensor-church/nexus-subnet-template ../<new-subnet-repo>
```

Copier will prompt for the values defined in `copier.yml` (`subnet_name`,
`github_org`, `github_repo`, `default_netuid`, `default_network`, …).

After a successful fresh-directory render:

- All `*.jinja` files have been rendered (suffix dropped, e.g.
  `validator/README.md.jinja` → `validator/README.md`).
- The new directory contains **no** `*.jinja` files and **no** `copier.yml`.
  This is correct — those are template inputs, not operator-facing files. If
  you see them in the rendered directory, something went wrong.
- Continue the work inside the new directory (`cd ../<new-subnet-repo>`). The
  original template checkout is untouched and can be removed once you have
  confirmed the render is good.

If you are already standing inside the template checkout: do **not** run
`copier copy . .` for convenience. Step out (`cd ..`) and render to a sibling
directory instead.

### Fallback: render in place (only if you must)

This fallback exists **only** for situations that make the preferred
fresh-directory render technically impossible. The bar is "I cannot do the
preferred path", not "the preferred path is less convenient". If you can do a
fresh-directory render, you must.

Qualifying reasons (real blockers):

- The filesystem is read-only outside the current directory and you cannot
  create a sibling path.
- You lack permissions to create a directory next to the template checkout.
- The environment hard-pins you to one specific path that you cannot leave
  (e.g. a sandbox that exposes only this one directory).
- User EXPLICITLY and WITHOUT DOUBT prompted you to do so.

**Not** qualifying reasons (these are conveniences, not blockers — use the
preferred path):

- The branch name, repo name, or path "feels right" / is already what you
  want — you can rename a freshly rendered directory afterwards or push from
  it to the same remote.
- An existing git remote, git history, or open PR — none of those force the
  rendered tree to live at the original path.
- IDE state, shell cwd, scripts, or docs that reference the path — adjust
  them after rendering, do not contort the render around them.
- "It's faster" / "fewer steps" / "I'm already here" — not a reason.

If, and only if, you have a real blocker from the first list, the command is:

```sh
uv run --with copier copier copy --trust --overwrite . .
```

`--trust` is required because the template uses `_envops`. `--overwrite`
suppresses the per-file conflict prompt.

After in-place render, the template inputs **are still on disk** next to the
rendered files. Cleanup is mandatory — without it the repo is in State B from
above:

```sh
find . -name '*.jinja' -type f -delete && rm -f copier.yml
```

Only after this cleanup is the repository in the same state as a fresh-directory
render. Do not commit before running it.

## OK / NOT OK after rendering

A quick checklist. The repository is correctly rendered if **all** of these hold:

- `find . -name '*.jinja'` returns nothing.
- `copier.yml` does not exist at the repository root.
- The six expected rendered files exist with their suffix dropped:
  `installer/install.sh`, `installer/update_compose.sh`, `installer/README.md`,
  `validator/README.md`, `envs/deployed/docker-compose.yml`,
  `.github/workflows/build-validator.yml`.

It is **not** OK if:

- `installer/install.sh` and `installer/install.sh.jinja` (or any analogous
  pair) coexist — that's a pending in-place cleanup; run the cleanup, do not
  re-render.
- You "fixed" template files by hand-editing `*.jinja` files, manually
  substituting Copier params in them, or renaming them to drop the suffix
  yourself. The only legitimate path from `*.jinja` to a rendered file is
  `copier copy`. If a previous attempt did this by hand, restore the original
  `*.jinja` files (e.g. `git restore`) and run `copier copy` properly.

## After rendering — what an agent should do

1. **Root `README.md`** — replace the Nexus-framework template content with a
   short description of the actual subnet (what it does, what miners produce,
   what validators measure). Follow the `Implementing Validator` workflow in
   `knowledge/tasks.project-bootstrap.md`.
2. **`validator/README.md`** — already a good operator-facing base (rendered
   with the subnet's name and GitHub coordinates). Extend with subnet-specific
   operator info (hardware requirements, extra env vars, post-install steps)
   if needed. Do **not** duplicate the subnet description here — that belongs
   in the root README.
3. **`AGENTS.md`** — update the `Context` section: drop the "this is a
   template" notice, add a one-line note that the project originated from this
   template, and a short subnet description.
4. **Template config** — rendered repos do not contain `copier.yml`. The
   rendered tree should never grow one back. In the *template* checkout,
   `copier.yml` is touched only when you add new template parameters that
   future renders should configure. Day-to-day subnet work does not modify it.

The source template currently does not keep Copier update metadata
(`.copier-answers.yml`) in rendered repos. If upstream template changes are
needed later, re-render into a fresh directory or port the changes manually
unless the Copier config is extended to support `copier update`.

## What NOT to do

- Do not render in place as a first instinct — always prefer a fresh
  destination directory; in-place is a fallback and requires the cleanup step.
- Do not commit a repository where `*.jinja` files coexist with their
  suffix-less siblings, or where `copier.yml` still exists at the root. That's
  a half-finished render, not a rendered repo.
- Do not delete `*.jinja` files *instead of* running `copier copy` — the
  rendered content has to come out of Copier, not out of a manual edit.
- Do not hand-substitute Copier params inside `*.jinja` files. Run the tool.
- Do not manually copy `copier.yml` or any `*.jinja` files into a rendered
  repo just to preserve the template machinery. They are template inputs, not
  operator-facing subnet files.
- Do not create a separate validator-operator README in the repository root —
  the root README is for the subnet at large; operator-facing install
  documentation lives in `validator/README.md` and `installer/README.md`.
