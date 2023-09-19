from DES2 import new

token = input("암호화할 토큰을 입력해 주세요: ")
key = input("토큰을 암호화할 키를 입력해 주세요: ")

token = token.encode("utf-8")

encipher = new(key)
encrypted_token = encipher.encrypt(token)

with open("youtube.bot/bot.token", "wb") as f:
    f.write(encrypted_token)