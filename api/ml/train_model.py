"""
ML Dropout Risk Training Script
- Connects to SQLite/PostgreSQL
- Extracts feature matrix for all students
- Trains a scikit-learn RandomForestClassifier
- Serializes the model to .pkl
"""
import os
import sys
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Ensure backend root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
from models import Student, School, Facility

def extract_features(db: Session):
    """Query database and construct a pandas DataFrame of features."""
    # Simplified extraction using raw dict generation
    data = []
    
    # Pre-fetch facilities and schools to avoid N+1 queries
    schools = {s.id: s for s in db.query(School).all()}
    facilities = {f.school_id: f for f in db.query(Facility).all()}
    
    students = db.query(Student).all()
    
    if not students:
        print("Error: No students found in database. Please run seed_data.py first.")
        sys.exit(1)
        
    for st in students:
        sch = schools.get(st.school_id)
        fac = facilities.get(st.school_id)
        
        # Ground truth proxy for training: risk >= 60 is high risk (1)
        # In a real system, this would be actual historical dropout data (1/0)
        target = 1 if st.dropout_risk >= 60 else 0
        
        data.append({
            "attendance_rate": st.attendance_rate,
            "academic_score": st.academic_score,
            "disability_type": st.disability_type,
            "socio_economic": st.socio_economic,
            "school_type": sch.school_type if sch else "Urban",
            "has_ramps": fac.has_ramps if fac else False,
            "has_assistive_tech": fac.has_assistive_tech if fac else False,
            "has_special_educator": fac.has_special_educator if fac else False,
            "target": target
        })
        
    return pd.DataFrame(data)

def train():
    print("1. Connecting to database...")
    db = SessionLocal()
    df = extract_features(db)
    db.close()
    
    print(f"2. Extracted {len(df)} records. Training model...")
    
    # Feature engineering strategy
    numeric_features = ["attendance_rate", "academic_score"]
    categorical_features = ["disability_type", "socio_economic", "school_type"]
    boolean_features = ["has_ramps", "has_assistive_tech", "has_special_educator"]
    
    # Simple boolean to int conversion
    for col in boolean_features:
        df[col] = df[col].astype(int)
        
    X = df.drop(columns=["target"])
    y = df["target"]
    
    # Build preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
            ('bool', 'passthrough', boolean_features)  # Already 0/1
        ])
        
    # Combine preprocessing and Random Forest classifier
    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, class_weight="balanced"))
    ])
    
    # Split data (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"   Training size: {len(X_train)}, Testing size: {len(X_test)}")
    
    # Train
    model_pipeline.fit(X_train, y_train)
    
    # Evaluate
    print("\n3. Evaluating Model:")
    y_pred = model_pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"   Accuracy: {accuracy:.2f}")
    print("\n   Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Extract feature importance (from the Random Forest step)
    # Get one-hot encoded feature names mapping step
    classifier = model_pipeline.named_steps["classifier"]
    encoded_feature_names = numeric_features.copy()
    
    # scikit-learn API to get encoded feature names
    try:
        cat_encoder = preprocessor.named_transformers_['cat']
        encoded_cats = cat_encoder.get_feature_names_out(categorical_features)
        encoded_feature_names.extend(encoded_cats)
        encoded_feature_names.extend(boolean_features)
        
        importances = classifier.feature_importances_
        feature_importance = list(zip(encoded_feature_names, importances))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        print("\n   Top 5 Feature Importances:")
        for name, imp in feature_importance[:5]:
            print(f"     - {name}: {imp:.4f}")
    except Exception as e:
        print(f"   (Could not extract feature importances: {e})")
    
    # Serialize the model
    save_path = os.path.join(os.path.dirname(__file__), "dropout_model.pkl")
    joblib.dump(model_pipeline, save_path)
    print(f"\n4. Success! Model saved to: {save_path}")

if __name__ == "__main__":
    train()
