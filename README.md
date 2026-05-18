# Nexus

> A proudly Bittensor-gnostic framework for building production-ready subnets.

**Subnets should be one-shotted, not hand-built.**

[Const's Chi](https://github.com/unconst/Chi) turns a subnet idea into **Bittensor-native mechanism design**. Nexus turns that design into **production-grade validator software**: reusable subnet machinery, local verification, and guardrails for teams that want to ship real subnets.

Together, Chi and Nexus create a **path from prompt to production**: design the subnet, build the validator, test it locally, and keep evolving it without rebuilding the same plumbing every time.

The larger promise is leverage: **solve common subnet plumbing once**, turn it into shared best practice, then let every Nexus-based subnet inherit it instead of reimplementing it alone.

Nexus is for **software developers**. It can deliver a lot, but it is not a no-code promise: developers still need to understand the framework, review generated code, and own the software they ship.

## Usage

1. Clone this repo into your AI coding agent of choice.
2. Ask: "How do I make [your subnet idea]?"
3. Use Chi deeply for mechanism design.
4. Let Nexus take over once the design is ready to implement and verify locally.

## Read On

- [What Nexus offers](#what-nexus-offers) - recurring subnet machinery moved into shared framework code.
- [What is in it for me?](#what-is-in-it-for-me) - check what Nexus changes for Bittensor, subnet owners, validators, and miners.
- [Catnet demo](#catnet-demo) - the same cat demo subnet as direct Chi prototype and as Chi design implemented with Nexus.
- [Why this matters](#why-this-matters) - why "something runs" is not enough for a real subnet.
- [Current state](#current-state) - the current template, localnet, and Catnet artifacts.
- [Funding ask](#funding-ask) - the next production-grade capabilities.

## What Nexus Offers

Bittensor subnet teams should not have to rediscover the same production pitfalls every time:

- weight setting and commit-reveal with on-chain verification
- localnet setup and reproducible testing
- miner communication, request routing, and protection against abusive traffic
- chain synchronization and subtensor communication
- async execution, background work, callbacks, and deadlock-prone coordination
- scoring pipelines, persistence, observability, restart recovery, and safe upgrades
- future: even more secure communication, monetization, deployment, observability, and upgrades; see the [Chi, Nexus, and next steps comparison](./docs/index.html) for the fuller roadmap

Nexus turns those concerns into shared framework capabilities instead of bespoke code inside every subnet.

## What Is In It For Me?

### For Bittensor Ecosystem

- shorter path from subnet idea to production subnet
- fewer strong ideas dying in implementation before they can prove their value
- less ecosystem energy lost to repeated technical fights: miner DDoS, unreliable weight setting, validator deployment problems, and opaque vtrust failures
- better test harnesses for incentive mechanisms, leading to safer and cheaper subnet changes
- shared engineering investment that makes the underlying tech work for subnet teams instead of every team fighting it alone
- more software teams able to build responsibly on Bittensor
- more room for participant ingenuity to go into ground-breaking inventions, useful services, and real value creation

### For Subnet Owners

- fastest path from idea to production through a working, locally testable prototype
- less custom subnet machinery to own
- reusable building blocks able to express most subnet shapes
- maintainable subnet code built from small components with clear interfaces and responsibilities
- structure that is easier for both developers and coding agents to understand, extend, and verify
- lower cost for the next subnet once the team understands the Nexus structure and building blocks

### For Validators

- safer, more reliable validator software with fewer lost dividends from failed weight setting, deadlocks, or silently failed background tasks
- easier and cheaper validation of Nexus-based subnets, letting validator teams safely cover more subnets
- structured chain communication through Pylon, making local subtensors and production chain access easier to manage
- observability and autoupdate tooling for faster issue detection, validator-subnet-owner communication, and resolution
- persistence for scores, task results, and validator state, enabling restarts and upgrades without avoidable vtrust loss

### For Miners

- stronger default protection against miner DDoS and abusive validator traffic
- secure validator-miner communication built into Nexus-based subnet machinery
- clearer miner contracts and more consistent communication protocols across Nexus-based subnets
- more robust validator code, making miner contributions easier to evaluate fairly and thoroughly

## Catnet Demo

The [Catnet comparison repo](https://github.com/bittensor-church/nexus-chi-comp) takes one Chi-shaped subnet idea and shows why the handoff matters: a cat-inpainting subnet where miners receive an image and return the same image with one realistic cat added. It contains the direct Chi prototype, the Nexus implementation, prompts, session dumps, localnet artifacts, and the side-by-side Chi/Nexus README.

- Chi is valuable at the design and exploration stage. It gets the subnet idea into Bittensor terms and helps clarify the mechanism.
- Chi can also produce a working prototype, but that is no longer the step to optimize for once Nexus exists. Prototype-quality code tends to leave production concerns such as runtime coordination, chain access, miner communication, scoring queues, state, weight setting, and local verification inside subnet-specific code.
- Nexus is where the project should go once the design is ready to build: the same mechanism expressed through reusable actors and tasks for request entry, miner dispatch, scoring, weighing, error handling, and localnet-backed verification.

This comparison is useful because it does not claim Nexus invents better subnet ideas or replaces Chi. The idea and mechanism direction come first. Nexus shows the benefit of handing a Chi-designed subnet over to a production framework once the team needs software that is easier to test, operate, and extend.

The Catnet comparison also exposed the practical difference in development experience:

- Chi reached a working prototype, but the implementation had to manage threads, async I/O, SDK access, queues, and HTTP lifecycles directly.
- The Chi run exposed a real Bittensor SDK thread-safety/concurrency issue during localnet verification.
- Nexus delegates runtime coordination to the framework, so subnet code is more about tasks, scoring, and weighing than "what is waiting on what?"
- Nexus produced a cleaner repository shape with `.env` configuration, gitignored local secrets, updated project docs, tests, and localnet artifacts.
- The benefit compounds after the first subnet: developers see the same structure and runtime concepts again instead of a different one-off validator each time.

## Why This Matters

Today, a strong agentic workflow can get a team to "something runs." That is useful, but it is not enough. A subnet that attracts miners, validators, users, and capital needs to be maintainable after the demo works.

The gap shows up immediately:

- the validator becomes a pile of ad-hoc runtime code
- local testing depends on fragile scripts
- scoring and weighting state is easy to lose
- chain behavior is hard to reproduce and verify
- every team implements miner communication, retries, timeouts, and operational checks differently
- adding the second endpoint, second background task, or second async workflow can turn into architecture work instead of subnet work

Nexus is meant to make the production-grade path the default path.

## Current State

Nexus is an early preview. It already demonstrates the direction:

- a subnet template with agent-friendly workflows and Bittensor knowledge
- a localnet setup with subtensor and Pylon
- reusable validator building blocks
- a Catnet implementation with modular scoring, weighting, local miner fixtures, tests, and end-to-end artifacts
- documentation patterns that update the README and agent instructions with subnet-specific information instead of leaving template context behind

The current work proves the thesis, but it is not the end state.

## Funding Ask

The next phase is to turn Nexus from a promising preview into a production-grade subnet development platform.

Priority areas:

- more reusable subnet patterns
- stronger localnet harnesses with honest, weak, broken, and adversarial miner profiles
- durable persistence for scores, task results, and validator state
- restart recovery good enough for validators to survive process restarts without losing trust-critical history
- observability, health checks, and proof artifacts
- Sentry/Loki/Grafana-style logging and metrics where cost-effective
- secure miner communication, including centralized Epistula/TLS integration
- safer weight-setting and commit-reveal verification
- persistent but expiring weights and scoring history
- synthetic traffic and miner result sampling as first-class framework patterns
- Computehorde plugin to offload compute-heavy validation to SN12
- auto-update and deployment workflows
- monetization primitives that can be added to subnets consistently, such as burning, allowances, and alpha payments
- upgrade workflows that let existing Nexus-based subnets inherit framework improvements
