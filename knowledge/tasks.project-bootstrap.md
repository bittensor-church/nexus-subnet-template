# Template bootstrap

**requires:** repo cloned locally
**grounding knowledge:** knowledge/template.bootstrap.md
**do not load:** bittensor, nexus, pylon, localnet, coding guidelines
**definition of done:**

- repository state detected (unrendered template / in-place cleanup pending / rendered-but-not-adapted)
- post-render checklist passes as described in `knowledge/template.bootstrap.md`

**after done:** start designing the subnet

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
**grounding knowledge:** subnet design, nexus, observability
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

**after done:** build the validator image

# Building Validator

**requires:** localnet running end-to-end; `master` ready for release (QA gates pass; root
`README.md`, `validator/README.md`, `installer/README.md`, and `AGENTS.md` consistent with the
current state of the subnet); `validator/Dockerfile` builds locally without errors
**grounding knowledge:** `knowledge/validator.deploy.md` (procedure 1)
**definition of done:**

- `validator/Dockerfile` built locally without errors as a sanity check before promotion
- procedure 1 (build) ran on `deploy-build-production`: `build-validator.yml` finished successfully
  and pushed `<image_registry>/<github_org>/<image_basename>-production:v0-latest` and
  `...:sha-<commit>` to the configured registry

**after done:** release the validator

# Releasing Validator

**requires:** Building Validator complete (validator image exists in the registry under `:sha-<commit>`)
**grounding knowledge:** `knowledge/validator.deploy.md` (procedures 2 and 3)
**definition of done:**

- procedure 2 (promote validator) ran for the **initial** digest: `envs/deployed/docker-compose.yml`
  on `master` pins the validator image by digest
  (`<image_registry>/.../<image_basename>-${ENVIRONMENT:?}@sha256:<digest>`), replacing the
  placeholder digest shipped by the template, so operators run exactly the image the developer
  smoke-tested
- the pylon digest already pinned in `envs/deployed/docker-compose.yml` by the template is
  current enough for this validator; if the validator requires a newer pylon, procedure 3
  (promote pylon) ran too, updating the pylon digest on `master`
- branch `deploy-config-production` points at the same commit as `master`, so an operator pulling
  `installer/install.sh` from this branch gets a consistent set of installer, `update_compose.sh`,
  and `docker-compose.yml`
- smoke test: `bash installer/install.sh` on a clean Linux host (a fresh VM or container, not
  the developer's laptop) succeeds — validator and pylon services come up healthy and `crontab -l`
  shows the cron line tagged with the configured cron tag

**after done:** workflow is complete; subsequent releases are independent runs of the
build / promote-validator / promote-other-service procedures in `knowledge/validator.deploy.md`,
not always in a fixed combination.
