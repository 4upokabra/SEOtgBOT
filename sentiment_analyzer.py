from transformers import pipeline
import torch
import os
from dotenv import load_dotenv

load_dotenv()

class SentimentAnalyzer:
    def __init__(self):
        # Загружаем предобученную модель для анализа настроений
        self.analyzer = pipeline(
            "sentiment-analysis",
            model="blanchefort/rubert-base-cased-sentiment",
            token=os.getenv('HUGGINGFACE_TOKEN'),
            device=0 if torch.cuda.is_available() else -1
        )

    def analyze_text(self, text):
        try:
            result = self.analyzer(text)[0]
            # Преобразуем метку в числовой score
            if result['label'] == 'POSITIVE':
                score = result['score']
            elif result['label'] == 'NEUTRAL':
                score = 0.0
            else:
                score = -result['score']
            return score
        except Exception as e:
            print(f"Ошибка при анализе текста: {e}")
            return 0.0

    def analyze_batch(self, comments):
        results = []
        for comment in comments:
            score = self.analyze_text(comment.text)
            results.append({
                'text': comment.text,
                'score': score,
                'sentiment': 'positive' if score > 0 else 'negative' if score < 0 else 'neutral'
            })
        
        # Формируем отчет
        positive_count = sum(1 for r in results if r['sentiment'] == 'positive')
        negative_count = sum(1 for r in results if r['sentiment'] == 'negative')
        neutral_count = sum(1 for r in results if r['sentiment'] == 'neutral')
        
        report = f"""
        Анализ настроений:
        Положительных комментариев: {positive_count}
        Нейтральных комментариев: {neutral_count}
        Отрицательных комментариев: {negative_count}
        
        Последние комментарии:
        """
        
        for result in results[-5:]:  # Показываем последние 5 комментариев
            report += f"\n{result['text']} ({result['sentiment']})"
        
        return report 

    def generate_report(self, comments):
        total_comments = len(comments)
        if total_comments == 0:
            return "Нет комментариев для анализа"
            
        # Подсчет статистики
        positive = sum(1 for c in comments if c.sentiment_score > 0)
        negative = sum(1 for c in comments if c.sentiment_score < 0)
        neutral = sum(1 for c in comments if c.sentiment_score == 0)
        
        # Расчет процентов
        positive_pct = (positive / total_comments) * 100
        negative_pct = (negative / total_comments) * 100
        neutral_pct = (neutral / total_comments) * 100
        
        # Формирование отчета
        report = f"""
📊 *Анализ тональности комментариев*
Всего комментариев: {total_comments}

😊 Положительные: {positive_pct:.1f}%
😐 Нейтральные: {neutral_pct:.1f}%
😞 Отрицательные: {negative_pct:.1f}%

💬 *Последние комментарии:*
"""
        
        # Добавляем последние комментарии
        for comment in comments[-5:]:  # Показываем последние 5 комментариев
            sentiment_emoji = "😊" if comment.sentiment_score > 0 else "😐" if comment.sentiment_score == 0 else "😞"
            report += f"\n{sentiment_emoji} {comment.text}"
            
        return report 