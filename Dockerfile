FROM python:3.9.13-buster
RUN pip install disnake
RUN pip install requests
RUN pip install pillow
RUN pip install numexpr
COPY bot.py .
COPY utils.py .
COPY database.py .
COPY room_manager.py .
COPY config.ini .
CMD ["python", "bot.py"]