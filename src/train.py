import time
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from .config import RANDOM_STATE, TEST_FRACTION

def make_preprocessor(numeric, categorical, scale=False):
    num_steps=[("imputer",SimpleImputer(strategy="median"))]
    if scale: num_steps.append(("scaler",StandardScaler()))
    return ColumnTransformer([("num",Pipeline(num_steps),numeric),
        ("cat",Pipeline([("imputer",SimpleImputer(strategy="most_frequent")),("onehot",OneHotEncoder(handle_unknown="ignore",sparse_output=False))]),categorical)])

def metrics(model,X,y):
    pred=model.predict(X)
    return {"mae":float(mean_absolute_error(y,pred)),"rmse":float(mean_squared_error(y,pred)**0.5),"r2":float(r2_score(y,pred))},pred

def train_baselines(X, y, numeric, categorical):
    cut=int(len(X)*(1-TEST_FRACTION)); Xtr,Xte=X.iloc[:cut],X.iloc[cut:]; ytr,yte=y.iloc[:cut],y.iloc[cut:]
    defs={"Dummy":DummyRegressor(strategy="mean"),"Linear Regression":LinearRegression(),
          "Decision Tree":DecisionTreeRegressor(max_depth=18,min_samples_leaf=3,random_state=RANDOM_STATE),
          "Random Forest Default":RandomForestRegressor(n_estimators=160,n_jobs=-1,random_state=RANDOM_STATE,max_features=1.0)}
    results={}; fitted={}
    for name,est in defs.items():
        pipe=Pipeline([("preprocessor",make_preprocessor(numeric,categorical,scale=name=="Linear Regression")),("model",est)])
        start=time.time(); pipe.fit(Xtr,ytr); elapsed=time.time()-start
        tr,_=metrics(pipe,Xtr,ytr); te,pred=metrics(pipe,Xte,yte)
        results[name]={"train":tr,"test":te,"fit_seconds":elapsed}; fitted[name]=(pipe,pred)
    return (Xtr,Xte,ytr,yte),results,fitted

