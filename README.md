# CNG Lightning Talk Template (Quarto)

A [Quarto RevealJS](https://quarto.org/docs/presentations/revealjs/) template for 5-minute [Cloud Native Geospatial Forum](https://cloudnativegeo.org) lightning talks. Slides auto-advance every 15 seconds. 20 slides × 15 seconds = 5 minutes.

**Live demo:** [https://cloudnativegeo.github.io/lightning-talk-quarto-TEMPLATE/](https://cloudnativegeo.github.io/lightning-talk-quarto-TEMPLATE/)

---

## Create your own deck

1. Create a new repository under your account:
  - Select from the upper right of the page: **Use this template → Create a new repository**
  - Give the repository a name.
  - Choose Public visibility (so you can create GitHub Pages)
  - Click **Create repository**
2. Wait for the **Publish Slides** workflow to finish (see the **Actions** tab). The `gh-pages` branch only exists after this first run.
3. Enable GitHub Pages:
  - Go to **Settings → Pages** in your new repo
  - Under **Source**, select **Deploy from a branch**
  - Under **Branch**, select `gh-pages` and `/ (root)`, then click **Save**
  - Your deck will be live at `https://<your-username>.github.io/<repo-name>/` after a minute or two
    - You can display this URL on the main page by clicking the gear icon in the **About** section, and checking the **Use your GitHub Pages website** checkbox.
    - [ ] Share this URL with the CNG event organizers



## What to edit

- The main file to edit is the `index.qmd` file which defines the content of the slides.
- Push any changes to `main` either using the GitHub.com website or by editing content locally (see below) — the workflow in `.github/workflows/publish.yml` will rerender the slides, push the resulting website to a `gh-pages` branch, and update the website automatically!



## Local Setup / Development

To develop the content locally, clone your repo and run quarto in "preview" mode:

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
uv sync
uv run quarto preview
```

Open the preview URL in your browser. The deck auto-advances — to turn off auto-advance during editing, add `?autoSlide=0` right after the `/`, **before** the `#` (e.g. `http://localhost:4200/?autoSlide=0#/slide-05`). Anything after the `#` is ignored, so `http://localhost:4200/#/slide-05?autoSlide=0` will not work. The countdown bar is hidden while auto-advance is off.

---

