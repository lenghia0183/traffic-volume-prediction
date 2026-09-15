from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from .train import make_preprocessor
from .config import RANDOM_STATE

def tune_random_forest(X,y,numeric,categorical):
    pipe=Pipeline([("preprocessor",make_preprocessor(numeric,categorical)),("model",RandomForestRegressor(random_state=RANDOM_STATE,n_jobs=-1))])
    params={"model__n_estimators":[200,300,450,600],"model__max_depth":[18,24,32,None],"model__min_samples_split":[2,4,8,12],
            "model__min_samples_leaf":[1,2,3,5],"model__max_features":[0.65,0.8,1.0,"sqrt"],"model__bootstrap":[True]}
    search=RandomizedSearchCV(pipe,params,n_iter=24,scoring="neg_mean_absolute_error",cv=TimeSeriesSplit(n_splits=5),
                              random_state=RANDOM_STATE,n_jobs=-1,verbose=1,return_train_score=True)
    search.fit(X,y)
    return search, params
