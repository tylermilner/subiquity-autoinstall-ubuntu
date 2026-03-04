# subiquity-autoinstall-ubuntu
My Subiquity Autoinstall templates for automated Ubuntu installations

## Validation

This repository includes a GitHub Actions workflow that validates autoinstall templates on every push and pull request.

- Workflow: `.github/workflows/validate-autoinstall-yaml.yml`
- Basic YAML syntax check (local): `python3 scripts/validate_autoinstall_yaml.py`
- Official Subiquity validator (CI): `scripts/validate-autoinstall-user-data.py` from the Subiquity project

### Run Subiquity validation locally

The official Subiquity validator requires a Subiquity checkout and Ubuntu dependencies.

1. Clone Subiquity and install dependencies (Ubuntu/Linux):
	- `git clone https://github.com/canonical/subiquity.git`
	- `make -C subiquity install_deps`
2. Run the local wrapper from this repository:
	- `python3 scripts/validate_autoinstall_subiquity.py --subiquity-dir subiquity`

If your template is not wrapped in cloud-config format, pass `--no-expect-cloudconfig`.
