FROM python:3.12
WORKDIR /bot

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY bot.py .
COPY config.py .
COPY PrivacyPolicy.txt .
COPY cogs ./cogs

CMD ["python", "bot.py"]