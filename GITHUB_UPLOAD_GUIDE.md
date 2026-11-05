# Uploading this folder to GitHub

This folder is already arranged as a repository. The user will perform the upload; no credentials are included.

## Recommended repository
`smooth-radar-skill`

## Before publishing
- Review `assets/example_config.json` and `assets/example_presets.json`.
- The example uses model labels Model A–E. Numeric values, axis labels, colors and display anchors are retained from the supplied example configuration.
- Confirm that these numeric benchmark values are approved for public release. Replacing model names does not anonymize the numeric results themselves.
- Confirm no private paths, patient data, tokens, or credentials are present.

## Upload with Git
From the directory containing this README:

```bash
git init
git add .
git status
git commit -m "Initial release: smooth-radar smooth radar skill"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/smooth-radar-skill.git
git push -u origin main
```

Create the public repository on GitHub first, with the name `smooth-radar-skill`. Do not initialize it with a README/license if you are pushing this existing initialized content, to avoid unrelated-history conflicts.

## Use after publishing
A collaborator can clone the repository and copy the folder into their Codex skills directory, or use it as a project-level skill under `.agents/skills/smooth-radar-skill/`.
