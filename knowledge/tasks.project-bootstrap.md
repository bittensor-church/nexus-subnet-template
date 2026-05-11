# Designing Subnet

**requires:** user's subnet idea
**grounding knowledge:** bittensor
**do not load:** nexus, pylon, localnet, coding guidelines
**definition of done:**

- all design rules discovered and met
- subnet design approved by user
- subnet design written to a file

**after done:** start implementing validator

# Implementing Validator

**requires:** subnet design approved by user
**grounding knowledge:** subnet design, nexus
**do not load:** localnet
**definition of done:**

- project directory ready for development
- validator implemented
- README.md adapted to subnet; template-related info removed; contains brief subnet description; doesn't
  reiterate subnet design
- `validator/README.md` reviewed: it is a good operator-facing base rendered from Copier params; extend
  with subnet-specific operator info if needed (hardware requirements, extra env vars, post-install
  steps), but do not duplicate the subnet description there — that belongs in root `README.md`
- QA gates pass

**after done:** start setting up localnet

# Setting Up Localnet

**requires:** validator implemented
**grounding knowledge:** localnet
**definition of done:**

- localnet adapting complete as specified by localnet/localnet.adapting-to-subnet.md
- end-to-end flow works as described in localnet/localnet.adapting-to-subnet.md
- no temporary workarounds left
- repo is clean and has good DX
- all localnet components work together and perform the subnet's designed goals
- root README.md updated; added at least: localnet section with steps to run, configure, pointer to localnet
  readme for dev setup
- all claims and instructions in READMEs verified and correct
- subnet-specific artifacts, if relevant, proving the subnet's work prepared and presented to the user (but not
  committed)

**after done:** deploy the validator

# Deploying Validator

**requires:** localnet running end-to-end
**grounding knowledge:** none new (`installer/README.md.jinja` and `copier.yml` describe the inputs;
`knowledge/template.bootstrap.md` is the source of truth for *how* to invoke Copier — fresh-directory
render is preferred, in-place requires a mandatory cleanup)
**definition of done:**

- `copier copy . <dest>` (or `copier copy gh:<org>/<repo> <dest>`) renders cleanly with answers
  appropriate for this subnet; rendered files committed to master
- `validator/Dockerfile` builds locally without errors
- `.github/workflows/build-validator.yml` pushes a validator image to the configured registry on push
  to a `deploy-build-prod` branch
- branch `deploy-config-prod` exists and contains the rendered repo; the operator-critical files are the
  rendered `installer/install.sh`, `installer/update_compose.sh`, and `envs/deployed/docker-compose.yml`
- `envs/deployed/docker-compose.yml` points at the intended environment-scoped validator image
  (`{{ image_basename }}-${ENVIRONMENT}:v0-latest` is acceptable as the first bootstrap placeholder;
  pin `{{ image_basename }}-${ENVIRONMENT}@sha256:...` once a release is promoted)
- `bash installer/install.sh` succeeds on a clean Linux host: validator and pylon services come up
  healthy, `crontab -l` shows the cron line tagged with the configured cron tag
