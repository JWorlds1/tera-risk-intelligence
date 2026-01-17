"""
Shared pytest fixtures for mining module tests
"""
import pytest
from typing import Dict


@pytest.fixture
def sample_text_with_temperatures():
    """Sample text containing temperature data"""
    return """
    The temperature in East Africa reached 35°C last week, with some areas hitting 77F.
    The heat wave brought temperatures of 25 degrees celsius in the morning.
    """


@pytest.fixture
def sample_text_with_population():
    """Sample text containing population data"""
    return """
    Over 2 million people are affected by the drought.
    The region has a population of 1,500,000 residents.
    Approximately 3.5 billion people live in vulnerable areas.
    """


@pytest.fixture
def sample_text_with_financial():
    """Sample text containing financial data"""
    return """
    The UN has allocated $500 million USD in funding to address the crisis.
    Total aid amounts to 1.5 billion dollars.
    The project received $250 thousand in initial funding.
    """


@pytest.fixture
def sample_text_with_percentages():
    """Sample text containing percentage data"""
    return """
    The situation has worsened by 25% compared to last year.
    Approximately 75 percent of the population is affected.
    The risk increased by 10 per cent.
    """


@pytest.fixture
def sample_text_with_dates():
    """Sample text containing date data"""
    return """
    The event occurred on January 15, 2025.
    Published on 2025-01-17.
    Last updated: 01/20/2025.
    """


@pytest.fixture
def sample_text_comprehensive():
    """Comprehensive sample text with multiple data types"""
    return """
    The temperature in East Africa reached 35°C last week, with precipitation 
    of only 50mm. Over 2 million people are affected by the drought. 
    The UN has allocated $500 million USD in funding to address the crisis.
    The situation has worsened by 25% compared to last year.
    The event occurred on January 15, 2025.
    """


@pytest.fixture
def sample_record_climate():
    """Sample record with climate risk indicators"""
    return {
        'id': 1,
        'title': 'Severe drought in East Africa causes food crisis',
        'summary': 'Worst drought in 40 years leads to crop failure and water scarcity',
        'full_text': 'The region is experiencing severe drought conditions with famine risk increasing.',
        'region': 'East Africa'
    }


@pytest.fixture
def sample_record_conflict():
    """Sample record with conflict risk indicators"""
    return {
        'id': 2,
        'title': 'Escalating violence leads to mass displacement',
        'summary': 'War and conflict force thousands to flee',
        'full_text': 'The ongoing war has created a refugee crisis with widespread displacement.',
        'region': 'Middle East'
    }


@pytest.fixture
def sample_record_urgency():
    """Sample record with urgency indicators"""
    return {
        'id': 3,
        'title': 'Critical emergency situation requires immediate action',
        'summary': 'Severe crisis worsening rapidly',
        'full_text': 'This is an urgent critical emergency that needs immediate attention.',
        'region': 'South Asia'
    }


@pytest.fixture
def sample_record_mixed():
    """Sample record with mixed risk indicators"""
    return {
        'id': 4,
        'title': 'Flood crisis causes displacement and urgent humanitarian need',
        'summary': 'Severe flooding leads to conflict over resources',
        'full_text': 'The flood has created an emergency situation with violence breaking out.',
        'region': 'Southeast Asia'
    }


@pytest.fixture
def sample_record_empty():
    """Sample record with minimal data"""
    return {
        'id': 5,
        'title': '',
        'summary': '',
        'full_text': '',
        'region': None
    }


@pytest.fixture
def sample_html_content():
    """Sample HTML content for extractor tests"""
    return """
    <html>
        <head>
            <title>Test Article</title>
            <meta name="description" content="This is a test article about climate change in East Africa.">
        </head>
        <body>
            <h1 class="article-title">Severe Drought Hits East Africa</h1>
            <div class="article-summary">The region is experiencing its worst drought in decades.</div>
            <time datetime="2025-01-15">January 15, 2025</time>
            <a href="/tag/climate" class="tag">Climate</a>
            <a href="/tag/drought" class="tag">Drought</a>
        </body>
    </html>
    """
