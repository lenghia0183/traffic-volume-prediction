from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from .train import make_preprocessor
from .config import RANDOM_STATE

def tune_random_forest(X,y,numeric,categorical):
    pipe=Pipeline([("preprocessor",make_preprocessor(numeric,categorical)),("model",RandomForestRegressor(random_state=RANDOM_STATE,n_jobs=-1))])
    params={"model__n_estimators":[120,200,300],"model__max_depth":[16,24,None],"model__min_samples_split":[2,5,10],
            "model__min_samples_leaf":[1,2,4],"model__max_features":[0.7,1.0,"sqrt"]}
    search=RandomizedSearchCV(pipe,params,n_iter=10,scoring="neg_mean_absolute_error",cv=TimeSeriesSplit(n_splits=3),
                              random_state=RANDOM_STATE,n_jobs=-1,verbose=1,return_train_score=True)
    search.fit(X,y)
    return search, params

