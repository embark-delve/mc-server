# The manager runs on the host. This image provides only offline CLI/config inspection.
# It deliberately contains no Docker socket/client and cannot manage host servers.
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --create-home manager
USER manager
ENTRYPOINT ["minecraft-server"]
CMD ["--help"]
