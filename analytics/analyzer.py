"""
Модуль для анализа данных о недвижимости
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from core.database import DatabaseManager
from config.settings import ANALYSIS_CONFIG, REPORTS_DIR


class RealEstateAnalyzer:
    """Анализатор данных о недвижимости"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = DatabaseManager()
        self.config = ANALYSIS_CONFIG

    def comprehensive_analysis(self) -> Dict:
        """Комплексный анализ рынка недвижимости"""
        self.logger.info("Запуск комплексного анализа рынка")

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'market_overview': self._get_market_overview(),
            'price_analysis': self._analyze_prices(),
            'location_analysis': self._analyze_locations(),
            'trends': self._analyze_trends(),
            'investment_opportunities': self._find_investment_opportunities(),
            'report_path': None
        }

        # Генерация отчета
        analysis['report_path'] = self.generate_market_report(analysis)

        return analysis

    def _get_market_overview(self) -> Dict:
        """Обзор рынка недвижимости"""
        properties = self.db.get_properties(limit=1000)

        if not properties:
            return {}

        df = pd.DataFrame(properties)

        overview = {
            'total_active_properties': len(df),
            'avg_price': df['price'].mean(),
            'median_price': df['price'].median(),
            'price_range': {
                'min': df['price'].min(),
                'max': df['price'].max()
            },
            'property_type_distribution': df['property_type'].value_counts().to_dict(),
            'avg_price_per_sqm': df['price_per_sqm'].mean()
        }

        return overview

    def _analyze_prices(self) -> Dict:
        """Анализ ценовой политики"""
        properties = self.db.get_properties(limit=1000)

        if len(properties) < self.config['min_data_points']:
            return {}

        df = pd.DataFrame(properties)

        # Удаляем выбросы
        price_series = df['price'].dropna()
        Q1 = price_series.quantile(0.25)
        Q3 = price_series.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        filtered_df = df[(df['price'] >= lower_bound) & (df['price'] <= upper_bound)]

        price_analysis = {
            'price_distribution': {
                'q1': Q1,
                'q2': price_series.quantile(0.5),
                'q3': Q3,
                'iqr': IQR
            },
            'price_by_rooms': filtered_df.groupby('rooms')['price'].agg(['mean', 'median', 'count']).to_dict(),
            'price_by_district': filtered_df.groupby('district')['price'].mean().to_dict(),
            'outliers_removed': len(df) - len(filtered_df)
        }

        return price_analysis

    def _analyze_locations(self) -> Dict:
        """Анализ по локациям"""
        properties = self.db.get_properties(limit=1000)

        if not properties:
            return {}

        df = pd.DataFrame(properties)

        location_analysis = {
            'top_districts_by_count': df['district'].value_counts().head(10).to_dict(),
            'avg_price_by_district': df.groupby('district')['price'].mean().sort_values(ascending=False).head(
                10).to_dict(),
            'avg_price_per_sqm_by_district': df.groupby('district')['price_per_sqm'].mean().sort_values(
                ascending=False).head(10).to_dict()
        }

        return location_analysis

    def _analyze_trends(self) -> Dict:
        """Анализ рыночных трендов"""
        # Здесь можно добавить анализ исторических данных
        # Пока возвращаем заглушку
        return {
            'note': 'Анализ трендов требует исторических данных за продолжительный период',
            'recommended_period': '30+ дней'
        }

    def _find_investment_opportunities(self) -> List[Dict]:
        """Поиск инвестиционных возможностей"""
        properties = self.db.get_properties(limit=500)

        if not properties:
            return []

        df = pd.DataFrame(properties)

        # Критерии для инвестиционных возможностей
        opportunities = []

        for _, prop in df.iterrows():
            score = 0
            reasons = []

            # Низкая цена за квадратный метр относительно среднего по району
            district_avg = df[df['district'] == prop['district']]['price_per_sqm'].mean()
            if prop['price_per_sqm'] and district_avg:
                price_ratio = prop['price_per_sqm'] / district_avg
                if price_ratio < 0.9:  # Дешевле на 10% чем среднее по району
                    score += 30
                    reasons.append(f"Цена ниже среднего по району на {((1 - price_ratio) * 100):.1f}%")

            # Хорошее расположение (центральные районы)
            premium_districts = ['центр', 'центральный', 'пресненский', 'арбат']
            if any(district in prop['district'].lower() for district in premium_districts):
                score += 20
                reasons.append("Премиальное расположение")

            # Оптимальное количество комнат
            if prop['rooms'] in [1, 2]:  # Наиболее ликвидные
                score += 15
                reasons.append(f"Оптимальное количество комнат: {prop['rooms']}")

            if score >= 40:  # Порог для включения в рекомендации
                opportunities.append({
                    'title': prop['title'],
                    'price': prop['price'],
                    'price_per_sqm': prop['price_per_sqm'],
                    'district': prop['district'],
                    'rooms': prop['rooms'],
                    'url': prop['url'],
                    'investment_score': score,
                    'reasons': reasons
                })

        # Сортировка по инвестиционному потенциалу
        opportunities.sort(key=lambda x: x['investment_score'], reverse=True)

        return opportunities[:10]  # Топ-10 opportunities

    def generate_market_report(self, analysis: Dict) -> str:
        """Генерация отчета по анализу рынка"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORTS_DIR / f"market_analysis_{timestamp}.md"

        report_content = self._build_report_content(analysis)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        self.logger.info(f"Отчет сохранен: {report_path}")
        return str(report_path)

    def _build_report_content(self, analysis: Dict) -> str:
        """Построение содержания отчета"""
        content = [
            "# Анализ рынка недвижимости",
            f"**Дата генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Обзор рынка",
            f"- Всего активных объектов: {analysis['market_overview'].get('total_active_properties', 0)}",
            f"- Средняя цена: {analysis['market_overview'].get('avg_price', 0):.0f} руб.",
            f"- Медианная цена: {analysis['market_overview'].get('median_price', 0):.0f} руб.",
            "",
            "## Распределение по типам недвижимости"
        ]

        # Добавляем распределение по типам
        for prop_type, count in analysis['market_overview'].get('property_type_distribution', {}).items():
            content.append(f"- {prop_type}: {count} объектов")

        # Добавляем инвестиционные возможности
        if analysis['investment_opportunities']:
            content.extend([
                "",
                "## Инвестиционные возможности",
                "| Объект | Цена | Район | Оценка |",
                "|--------|------|-------|--------|"
            ])

            for opportunity in analysis['investment_opportunities'][:5]:
                content.append(
                    f"| {opportunity['title'][:50]}... | "
                    f"{opportunity['price']:,.0f} руб. | "
                    f"{opportunity['district']} | "
                    f"{opportunity['investment_score']}/100 |"
                )

        return '\n'.join(content)