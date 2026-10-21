import feedparser
import requests
import json
import os
from datetime import datetime

GROQ_API_KEY = os.environ.get("GROQ_KEY")
NEWS_FILE = "noticias.json"

# Aqui estão os RSS que o robô vai ler (Roraima + Nacional)
RSS_URLS = [
    "https://g1.globo.com/rss/roraima/",
    "https://g1.globo.com/rss/politica/",
    "https://g1.globo.com/rss/economia/",
    "https://g1.globo.com/rss/ciencia-e-saude/",
    "https://g1.globo.com/rss/tecnologia/"
]

def load_news():
    if not os.path.exists(NEWS_FILE):
        return []
    with open(NEWS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def save_news(news):
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)

def rewrite_with_groq(title, content):
    prompt = f"""
    Você é um jornalista do portal BREAK NEWS RR (focado em Boa Vista e Roraima, mas com alcance nacional).
    Reescreva a seguinte notícia para não gerar plágio, otimize para SEO.
    Responda APENAS com um JSON válido no formato:
    {{
      "titulo": "Um título chamativo e otimizado",
      "categoria": "Geral", 
      "resumo": "Um resumo de 2 linhas",
      "conteudo": "O texto completo reescrito em 2 ou 3 parágrafos"
    }}
    A categoria deve ser uma destas: Geral, Segurança, Educação, Agro, Saúde, Tech, Política, Economia.
    
    Título original: {title}
    Conteúdo: {content}
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        text = result['choices'][0]['message']['content']
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    else:
        print("Erro na API Groq:", response.text)
        return None

def main():
    news = load_news()
    existing_titles = [n['titulo'] for n in news]
    
    for rss in RSS_URLS:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:5]: # Pega as 5 últimas notícias de cada RSS
            if entry.title not in existing_titles:
                print(f"Reescrevendo: {entry.title}")
                rewritten = rewrite_with_groq(entry.title, entry.summary)
                
                if rewritten:
                    new_item = {
                        "titulo": rewritten.get("titulo", entry.title),
                        "categoria": rewritten.get("categoria", "Geral"),
                        "resumo": rewritten.get("resumo", ""),
                        "data": datetime.now().isoformat(),
                        "imagem": "", 
                        "conteudo": rewritten.get("conteudo", entry.summary)
                    }
                    news.insert(0, new_item)
    
    # Mantém só as 50 notícias mais recentes para o site não ficar pesado
    news = news[:50]
    save_news(news)
    print("Robô finalizou com sucesso!")

if __name__ == "__main__":
    main()
