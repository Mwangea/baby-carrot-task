# Agent-environment image (placeholder).
#
# PIN the base image by digest — a bare tag ("latest", "3.12-slim") is not
# reproducible and fails the build check. Resolve the real digest with:
#   docker pull python:3.12-slim
#   docker inspect --format '{{index .RepoDigests 0}}' python:3.12-slim
#
# The digest below is REAL and resolvable, so `docker build environment/`
# works on an unmodified template. It pins the python:3.12-slim multi-arch
# index as of 2026-09-21. Swap in whatever base your task needs, but keep it
# pinned by digest: the format gate only checks the SHAPE
# (repo[:tag]@sha256:<64 hex>), so a digest no registry serves would pass
# intake and first fail much later, at build time.
FROM python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9

WORKDIR /workspace

# The build context is this environment/ directory. Place the task's input
# files beside this Dockerfile (e.g. environment/data/) and stage ONLY them.
# Never COPY tests/ or solution/ into this image — the model must not be able
# to see either.
COPY data/ /workspace/data/
COPY tools/ /workspace/tools/
COPY requirements.txt /tmp/requirements.txt

# Two things are installed here, for two different reasons.
#
#   1. The task's START state. Preinstall only what the task needs to begin;
#      discovering and installing analysis dependencies is legitimate work for
#      the model.
#
#   2. THE VERIFIER'S OWN TOOLING, which MUST be baked into this image. The
#      verifier phase runs with networking denied outright, so tests/test.sh
#      cannot fetch anything at run time — no uvx, no pip install, no wheel
#      download. A verifier that tries scores nothing, the reward file is
#      never written, and the run is reported as a broken PACKAGE rather than
#      as a score. Keep pytest and the CTRF plugin pinned to exact versions so
#      the report format cannot move under the parser in test.sh.
RUN pip install --no-cache-dir -r /tmp/requirements.txt
