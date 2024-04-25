FROM python:latest
WORKDIR /csbot
COPY ./bot .
COPY ./configs .
RUN pip install python-valve discord.py discord-py-interactions python-dotenv beautifulsoup4 pillow pynacl
CMD ["python","/bot/main.py"]