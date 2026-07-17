FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY hfa_brain ./hfa_brain
RUN pip install --no-cache-dir ".[server]"
ENV HFA_BRAIN=mock
EXPOSE 8000
CMD ["hfa-brain", "serve", "--host", "0.0.0.0", "--port", "8000"]
