FROM python:latest
WORKDIR /csbot
COPY ./bot ./bot
COPY ./configs ./configs
RUN pip install python-valve discord.py discord-py-interactions python-dotenv beautifulsoup4 pillow pynacl
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*
CMD ["python","bot/main.py"]