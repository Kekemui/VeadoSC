# ADR 1: Backend

## Status

Accepted

## Context

VeadoSC requires additional libraries beyond the Python standard library to connect to veadotube.
At this time, this is limited to [`websockets`](https://websockets.readthedocs.io/en/stable/), but
it is certainly possible this will change in the future.

StreamController up to 1.5.0-beta.7 carried unused dependencies in its `venv`, and exposed these
dependencies to plugins. `websockets` was included in this set of unused dependencies. Plugins
could depend on these, intentionally or otherwise, and subject themselves to the whims of the
upstream maintainers, who could at any time for any or no reason clean excess dependencies (and be
well within their rights to do so).

Simultaneously, while plugins are technically permitted to specify requirements
[per the docs](https://streamcontroller.github.io/docs/latest/plugin_dev/modify_template/add_requirements/)
(via `requirements.txt`), this doesn't seem to function with just the `requirements.txt` defined as
directed by the docs
([testing branch](https://github.com/Kekemui/VeadoSC/tree/27-beta-8-compat-frontend)). In addition,
there is strong sentiment against allowing frontend requirements because it both pollutes
StreamController's `venv` and is not cleanable, while a plugin with a backend, and that defines
requirements for that backend, is trivially cleanable if a user uninstalls the plugin (`rm -rf`).
From StreamController's perspective, it is highly desirable for any plugin that requires additional
dependencies to define and use those dependencies within their backend.

Introducing a backend is not desirable from a plugin's perspective, though, as it introduces
complexity to communication between components in the frontend and backend of the plugin.
StreamController attempts to transparently bridge this via
[`RPyC`](https://rpyc.readthedocs.io/en/latest/index.html), however, `RPyC` is neither as magical
nor transparent as its authors should like. Any plugin that introduces a non-trivial backend must
be very conscious of how it communicates between frontend and backend processes.

Until StreamController pruned unused dependencies in 1.5.0-beta.8, VeadoSC was able to operate
purely as a frontend plugin due to the inherited dependencies. However, to continue to operate,
VeadoSC will either need to introduce a backend or lobby the StreamController maintainers to allow
or reintroduce the `websockets` dependency.

## Decision

We will introduce a backend to manage both file system monitoring and veadotube connections. Even if
we lobbied successfully to reintroduce the `websockets` dependency, we would merely punt this
decision until the next time we need a new library. Further, we would leave ourselves in similar
jeopardy should the StreamController maintainers choose to prune their own seemingly-unused
dependencies in the future.

We will also commit to putting any functionality not directly related to configuration of the plugin
or display of or interaction with Stream Deck buttons in the backend.

## Consequences

* (-) We now need to proxy events for use with observers across process boundaries.
    * For unknown reasons, `RPyC` does not seem to like working with our observer pattern. `update`
      is callable directly, but `RPyC` would hang/timeout when attempting to invoke `update` via the
      observer code (either when the `Subject` kept a reference directly to the callback method or
      to the `Observer`).
    * While initially regrettable, this may be a desired pattern to eliminate duplicate or
      otherwise unnecessary communication between process boundaries.
