import sys
sys.stdout.reconfigure(encoding='utf-8')
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print('--- Test 1: Answerable Query ---')
res1 = client.post('/api/chat', json={'question': 'गायत्री को वेदों की माता क्यों कहा गया है?', 'language': 'hi'})
print('Status:', res1.status_code)
d1 = res1.json()
print('Evidence Status:', d1['evidence_status'])
print('Retrieval Confidence:', d1['retrieval_confidence'])
print('Answer:', d1['answer'])
print('Sources count:', len(d1['sources']))
for s in d1['sources']:
    print(f"  Source: {s['book']} | Chapter: {s['chapter']} | Pages: {s['page_start']}-{s['page_end']}")

print('\n--- Test 2: Unanswerable Out-of-Domain Query ---')
res2 = client.post('/api/chat', json={'question': 'What is the current stock price of Apple?', 'language': 'en'})
d2 = res2.json()
print('Evidence Status:', d2['evidence_status'])
print('Answer:', d2['answer'])
print('Sources count:', len(d2['sources']))
