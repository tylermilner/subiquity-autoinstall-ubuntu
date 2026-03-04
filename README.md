# subiquity-autoinstall-ubuntu
My Subiquity Autoinstall templates for automated Ubuntu installations

## Validation

This repository includes a GitHub Actions workflow that validates YAML syntax for autoinstall template files on every push and pull request.

- Workflow: `.github/workflows/validate-autoinstall-yaml.yml`
- Run locally: `python3 scripts/validate_autoinstall_yaml.py`
