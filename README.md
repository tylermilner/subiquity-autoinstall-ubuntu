# subiquity-autoinstall-ubuntu

My Subiquity Autoinstall templates for automated Ubuntu installations

## Templates

Autoinstall templates are located in the `autoinstall-templates` directory, organized by device/target. Each template is a YAML file named `user-data.yaml` that follows the Subiquity Autoinstall specification.

## Validation

This repository includes a GitHub Actions workflow that validates autoinstall templates on every push and pull request.

- Workflow: `.github/workflows/validate-autoinstall-yaml.yml`
- Basic YAML syntax check (local): `scripts/validate_autoinstall_yaml.py`
- Official Subiquity validator (CI): `scripts/validate-autoinstall-user-data.py` from the Subiquity project

### Local Python setup

Install local Python dependencies:

1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `python3 -m pip install --upgrade pip`
4. `python3 -m pip install -r requirements.txt`

### Run YAML validation locally

1. Activate the Python virtual environment if not already active:
    - `source .venv/bin/activate`
2. Run YAML validation:
    - `python3 scripts/validate_autoinstall_yaml.py`

### Run Subiquity validation locally

The official Subiquity validator requires a Subiquity checkout and Ubuntu dependencies.

The official Subiquity validator requires a Subiquity checkout and **Ubuntu** dependencies.

1. Clone Subiquity and install dependencies (must be running on **Ubuntu/Linux**):
	- `git clone https://github.com/canonical/subiquity.git`
	- `make -C subiquity install_deps`
2. Run the local wrapper from this repository:
	- `python3 scripts/validate_autoinstall_subiquity.py --subiquity-dir subiquity`

If your template is not wrapped in cloud-config format, pass `--no-expect-cloudconfig`.

When `source.id` is set to a value other than `synthesized` (for example `ubuntu-desktop-minimal`), the wrapper script automatically uses Subiquity's `--legacy` mode to avoid [known runtime-validator limitations](https://canonical-subiquity.readthedocs-hosted.com/en/latest/howto/autoinstall-validation.html#validator-limitations). When running in legacy mode, only autoinstall schema validation is performed rather than full Subiquity server instance instantiation/validation.
