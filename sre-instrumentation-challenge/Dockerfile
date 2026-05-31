FROM python:3.14-slim

RUN useradd -m app
USER app
WORKDIR /home/app/app
ENV PATH=/home/app/.local/bin:$PATH

COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt
COPY src/ ./
  
EXPOSE 5001
CMD ["python", "run.py"]
