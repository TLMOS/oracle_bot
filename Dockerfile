FROM python:3.9.13-buster

RUN pip install disnake && \
pip install requests && \
pip install pillow && \
pip install numexpr

COPY . .

CMD ["python", "bot.py"]