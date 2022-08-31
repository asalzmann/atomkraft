# Atomkraft: E2E testing for Cosmos blockchains

**Atomkraft** is a model-based testing tool that automatically generates and executes massive end-to-end (E2E) test suites for Cosmos SDK based blockchains. 

The [Cosmos Network](https://cosmos.network) of [IBC](https://ibcprotocol.org)-connected blockchains is growing tremendously fast and our main objective is to improve the **quality assurance** practices and detect security issues in early stages of cosmos projetcs, such as:

- Discovering critical vulnerabilities and corner cases senarios.
- Growing and maintaining regression test suites for SDK modules to insure invariants correctness as the project evolves;
- Automating quality assurance by integrating an E2E testing solution that's executed on every PR.

## Conceptual overview

Atomkraft is a command-line application, which is as easy to obtain for your system by executing `pip install atomkraft` (you can consult the detailed [Installation Instructions](INSTALLATION.md) for the environment set-up). It provides you the commands for the following features:

- Automatic generation of test suites from compact TLA+ models of the system under test.
- Customizable local testnet creation.
- Easy execution of the generated test cases over the local test net.
- Ready-to-execute standard test suites for important Cosmos SDK modules (coming soon!)
- Pytest & poetry explanation TODO
- Generation of reports and dashboards for presentation and analysis of testing results (coming soon!)

![Atomkraft overview](docs/images/atomkraft-overview.svg)

### Atomkraft project creation

After installation, the creation of an _Atomkraft project_, which is initialized via `atomkraft init` command. The command will setup a new project in a given directory and automatically install all necessary software for it.
At the top level, an Atomkraft project contains the following:

- Folders that hold the artifacts if you are willing to generate test cases from formal models;
  - `models` is meant to keep your TLA+ models, 
  - `traces` contain generated test cases, represented in the form of [ITF traces](https://apalache.informal.systems/docs/adr/015adr-trace.html) (a JSON encoding of a sequence of test case steps);
  - `reactors` hold Python functions that interpret ITF traces, and map trace steps to concrete blockchain transactions;
- Folders for tests execution
  - `tests` collects all reproducible Pytest tests;
  - `reports` hold the test reports.
- Configuration files with default configurations, but customization commands are available upon your needs for changes.
  - `atomkraft.toml` contains Atomkraft project configuration;
  - `chain.toml` contains the blockchain configuration parameters, such as the number of nodes or the number of validators;
  - `model.toml` contains the TLA+ model configuration parameters, used to run model checkers;
  - `pyproject.toml` contains the Poetry project configuration.


### Local testnet set-up

With Atomkraft project created, you should be ready to go. By default, we configure local testnets to use the `gaiad` (Cosmos Hub) binary. If it is available via your `PATH`, executing `atomkraft chain testnet` should bring up a local testnet with 2 nodes and 3 validators. If you would like to configure any parameters differently (e.g. to run your custom blockchain binary), you can do it either via `atomkraft chain config` command, or by directly editing `chain.toml` config file. Please make sure your changes are valid by executing `atomkraft chain testnet`; we use the local testnet to run the tests.

### Traces and reactors

For describing test cases we use the [_Informal Trace Format_](https://apalache.informal.systems/docs/adr/015adr-trace.html), which is a JSON encoding of a sequence of steps, and each step encodes values of key state variables; please see [this example trace](examples/cosmos-sdk/transfer/example_trace.itf.json). The trace has been produced by our in-house [Apalache model checker](https://apalache.informal.systems) from [this TLA+ model](examples/cosmos-sdk/transfer/transfer.tla).

ITF traces are abstract; in the example trace above, it holds wallet balances as a simple mapping `balances` from abstract addresses, represented as integers, to their balances, also represented as integers without denomination. There are two abstract actions in this trace: `Init`, and `Transfer`. In order to be able to replay the abstract trace on a blockchain, each of those abstract actions needs to be translated to a concrete transaction, as well as all abstract parameters of an action need to be translated to concrete values (e.g. an abstract integer address needs to be translated into a concrete Cosmos address). This translation step is performed by a component that we call `reactor`: a reactor is a centerpiece for an Atomkraft project, without which it can't function, similar to a nuclear reactor for the atomic power plant. You can see [this example reactor](examples/cosmos-sdk/transfer/reactor.py) that is able to playback the above trace on the blockchain.

This separation between abstract traces and reactors, which apply abstract traces to concrete blockchains, is the crucial aspect of Atomkraft infrastructure; here is why:

- Abstract traces are more maintainable than concrete tests. Concrete tests need to be updated on every small change in encoding, API, etc.; we have seen PRs with thousands of LOC concerning only with updating manually written tests. With the separation into traces and reactors, traces won't need to be updated in most cases; only the relatively small reactors will need small tweaks.
- Abstract traces can be generated by whatever means: from model checkers such as [Apalache](https://apalache.informal.systems), via fuzzing, PBT, BDD, or even manually. How the abstract trace is produced, doesn't matter; it still can be executed using Atomkraft's infrastructure.
- It is much easier to understand the intent of a test case expressed as an abstract trace, because of absence of excessive details.
- Abstract traces are lightweight in terms of storage, which allows us to generate and maintain thousands of them, covering many corner cases, at no extra cost.


We have automated the process of writing a reactor via `atomkraft reactor` command. A user needs only to supply the lists of actions, and of state variables, and the command will generate a reactor stub with a function for each action; what remains is only to fill the body of each such function.

### Generating traces from TLA+ models

As explained above, abstract traces can be obtained by whatever means; we do not constrain the user in this respect. The most time efficient method, from our point of view, is to generate traces from formal models expressed in [TLA+](https://lamport.azurewebsites.net/tla/tla.html), the specification language designed by Leslie Lamport. For a gentle introduction to TLA+ you may use the Informal's [TLA+ Language Reference Manual](https://apalache.informal.systems/docs/lang/index.html) and [TLA+ Basics Tutorial](https://mbt.informal.systems/docs/tla_basics_tutorials/). While TLA+ may look scary for beginners, we can assure you that learning it will greatly improve your productivity when reasoning about (and testing!) both protocols and code.

The good news is that we have done a thorough work in making user's life as easy as possible when working with TLA+ models, and using them to generate abstract test traces. All heavy-lifting work wrt. TLA+ models is done by our [Apalache](https://apalache.informal.systems) model checker. The model checker itself is meant for expert users; Atomkraft tries its best to hide excessive complexity from its users and exposes only the most essential functionality for working with models. You can access this functionality via `atomkraft model` command, which provides you with the functions like listed in the screenshot below:

![Atomkraft model](docs/images/atomkraft-model.png)

The most important command in the scope of test case generation is `atomkraft model sample`. E.g. the command below (assuming you are in the Atomkraft project)

```sh
atomkraft model sample --model-path models/transfer.tla --traces-dir traces --examples Ex
```

will generate an abstract trace from the [transfer.tla](examples/cosmos-sdk/transfer/transfer.tla) model, and store the generated trace in the `traces` directory of your Atomkraft project.

### Running the tests against testnet

Let's assume you've done all the steps outlined above:

1. created a fresh Atomkraft project using `atomkraft init`
2. configured a Cosmos-based blockchain of your choice using `atomkraft chain`
3. created a reactor stub using `atomkraft reactor`, and populated it with code
4. generated abstract traces from a TLA+ model using `atomkraft model sample`, or created abstract traces by some other means

Then you are ready to go, and execute your tests! We provide two commands for doing that:

- `atomkraft test trace` will accept an abstract trace and a reactor, spin the local testnet, and execute the trace against the testnet
- `atomkraft test model` is a convenience shorthand that combines step 4 above (`atomkraft model sample`) with `atomkraft test trace`, and allows you to execute tests directly from a TLA+ model, sidestepping explicit trace generation.

Both of the above `atomkraft test` commands populate the `tests` directory of your project with Pytest-based tests; so executing `pytest` inside your Atomkraft project at any point in time will reproduce all of your tests. In fact, the complete Atomkraft project directory is ready at any point in time to be exported, and used as a Pytest project, for example for reproducing your tests in the CI.

## Tutorials 

Afterwards it's worth following either our [Cosmos SDK Token Transfer tutorial](examples/cosmos-sdk/transfer/transfer.md), or [CosmWasm tutorial](examples/cosmwasm/counter/README.md).

## Atomkraft-Cosmos 

## What's next: Atomkraft's immediate future

Atomkraft's functionality outlined above represents the tool MVP: please feel free to employ it in your projects, and let us know of your experience: we are always ready to assist!

There are many more features that are planned or are already being implemented; so stay tuned. Below is the preview of the future Atomkraft functionality:

- **Standard test suites**: we have already started the effort to provide standard reactors and tests for most important Cosmos SDK modules: [bank](https://docs.cosmos.network/master/modules/bank/), [staking](https://docs.cosmos.network/master/modules/staking/), [authz](https://docs.cosmos.network/master/modules/authz/); you name it! This will serve the community at large, and will allow you, as an Atomkraft user, to easily bootstrap your new Atomkraft projects:
  - running standard test suites in your CI will make sure that your new functionality doesn't break the important blockchain invariants;
  - using standard test suites as blueprints will allow you to easily create your own tests suites via examination and adaptation of already existing tests.
- **Test understanding and debugging**: we started to work in the direction of assisting the user in simplified creation and understanding of the test scenarios, as well as debugging the failed test runs:
  - for the former, we will provide the differential trace viewer, which highlights only the changes between the trace steps;
  - for the latter, we will provide the built-in blockchain explorer, and integrate into it the capabilities to trace back and forth between abstract trace steps and concrete blockchain transactions.
- **Test reports and dashboards**: we plan to implement the functionality for generation of test reports as well as live dashboards that would provide an easy-to-grasp overview and categorization of executed and running tests.
- **Exhaustiveness**: we plan to implement certain coverage metrics (e.g. transaction sequences up to specified length), and to help user achieving full coverage according to those metrics to provide confidence in the code in case no bugs are discovered.
