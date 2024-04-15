FROM python:latest
WORKDIR /home
COPY ./csbot.py .
COPY ./maps.cfg .
RUN pip install python-valve discord.py discord-py-interactions python-dotenv
CMD ["python","./csbot.py"]