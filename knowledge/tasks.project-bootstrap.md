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

**after done:** start setting up production deployment

# Setting Up Deployment

**requires:** localnet works end-to-end
**grounding knowledge:** ./knowledge/tasks.deployment.md
**definition of done:**

- `<OWNER>/<REPO>` and `<OWNER>/<SUBNET>` placeholders replaced everywhere; verified with
  `grep -rn '<OWNER>/<REPO>\|<OWNER>/<SUBNET>' installer/ tools/ envs/ .github/`
- GHCR access configured (default `GITHUB_TOKEN` for public images, PAT for private)
- branch `deploy-build-prod` created; first CI build succeeds; image published in
  `ghcr.io/<owner>/<repo>-prod`
- `tools/update_compose_digest.py` runs locally and pins a digest into `envs/deployed/docker-compose.yml`
- branch `deploy-config-prod` created with the pinned compose committed
- `installer/install.sh` exercised on a clean VM (or VM-like container) end-to-end
- root README.md updated with deployment pointer and post-fork checklist
- `knowledge/tasks.deployment.md` reviewed and verified correct for this subnet

**after done:** subnet is ready for production registration on Bittensor
