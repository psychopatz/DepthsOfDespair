@echo off
echo Starting FastAPI server...
echo Make sure you have run 'pip install -r requirements.txt'

uvicorn main:app --reload