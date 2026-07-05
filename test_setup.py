import os
from dotenv import load_dotenv
load_dotenv()

print("Testing all imports...")

import pandas as pd
print("  pandas OK:", pd.__version__)

import numpy as np
print("  numpy OK:", np.__version__)

import requests
print("  requests OK:", requests.__version__)

import sklearn
print("  scikit-learn OK:", sklearn.__version__)

import xgboost as xgb
print("  xgboost OK:", xgb.__version__)

import plotly
print("  plotly OK:", plotly.__version__)

import dash
print("  dash OK:", dash.__version__)

import fastapi
print("  fastapi OK:", fastapi.__version__)

from neo4j import GraphDatabase
print("  neo4j driver OK")

print("\nAll tests passed! Ready to start.")