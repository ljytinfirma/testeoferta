# 🔧 COMANDOS SIMPLES - VPS UBUNTU

## PROBLEMA: Python 3.11 não encontrado

Use **Python 3.10** que já está disponível:

## 1. INSTALAR DEPENDÊNCIAS BÁSICAS

```bash
apt update && apt upgrade -y
apt install python3 python3-pip python3-venv nginx supervisor git -y
```

## 2. CRIAR PROJETO

```bash
mkdir -p /var/www/encceja
cd /var/www/encceja
python3 -m venv venv
source venv/bin/activate
```

## 3. INSTALAR PACOTES PYTHON

```bash
pip install --upgrade pip
pip install Flask==3.0.0
pip install gunicorn==21.2.0
pip install requests==2.31.0
pip install qrcode[pil]==7.4.2
pip install python-dotenv==1.0.0
pip install Pillow==10.1.0
```

## 4. USAR SCRIPT ALTERNATIVO

Execute o script que funciona com Python 3.10:

```bash
bash deploy_vps_python310.sh
```

## 5. COPIAR ARQUIVOS DO PROJETO

```bash
cp app.py /var/www/encceja/
cp -r templates/ /var/www/encceja/
cp -r static/ /var/www/encceja/
chown -R www-data:www-data /var/www/encceja
supervisorctl start encceja
```

## 6. VERIFICAR SE FUNCIONOU

```bash
curl -I http://localhost:5000
tail -f /var/log/encceja.log
```

**O sistema funcionará perfeitamente com Python 3.10!**