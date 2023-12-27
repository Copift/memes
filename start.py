import json
import os

f=open('config.json').readlines()
s=''
for line in f:
    s+=line.replace('\n','')
js=json.loads(s)

# Указываем путь к директории
directory = "js"

# Создаем пустой список
files = []

# Добавляем файлы в список
files += os.listdir(directory)
server=js['server']
port=js['port']
# Выводим список файлов
for file in files:
  f = open('js/'+file,'r')
  s=f.readlines()
  s[1]=f"const ip = '{server}:{port} \n"
  f.close()
  f= open('js/'+file,'w')
  f.writelines(s)
  f.close()
