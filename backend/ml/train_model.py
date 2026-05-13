"""
Disease Prediction Model Training Script
Smart Patient Healthcare System

This script trains a Multinomial Naive Bayes classifier to predict diseases
based on symptoms. The model is saved using pickle for later use in production.

Why Naive Bayes?
1. Works well with text/categorical data
2. Fast training and prediction
3. Performs well even with limited training data
4. Good baseline for medical classification tasks
5. Provides probability estimates for predictions
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns

# Get the directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

def load_and_preprocess_data():
    """Load and preprocess the symptom-disease dataset"""
    
    # Load the dataset
    dataset_path = os.path.join(PROJECT_DIR, 'dataset.csv')
    print(f"Loading dataset from: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    print(f"Dataset shape: {df.shape}")
    print(f"Diseases found: {df['Disease'].nunique()}")
    
    # Combine all symptom columns into a single text column
    symptom_cols = [col for col in df.columns if 'Symptom' in col]
    
    def combine_symptoms(row):
        symptoms = []
        for col in symptom_cols:
            if pd.notna(row[col]) and str(row[col]).strip():
                symptom = str(row[col]).strip().lower().replace(' ', '_')
                symptoms.append(symptom)
        return ' '.join(symptoms)
    
    df['symptoms_text'] = df.apply(combine_symptoms, axis=1)
    
    # Remove rows with empty symptoms
    df = df[df['symptoms_text'].str.strip() != '']
    
    print(f"Dataset after preprocessing: {df.shape}")
    print(f"\nSample data:")
    print(df[['Disease', 'symptoms_text']].head())
    
    return df

def train_model(df):
    """Train the Naive Bayes model"""
    
    # Prepare features and labels
    X = df['symptoms_text']
    y = df['Disease']
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    print(f"\nNumber of classes: {len(label_encoder.classes_)}")
    print(f"Classes: {list(label_encoder.classes_)}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    print(f"\nTraining set size: {len(X_train)}")
    print(f"Test set size: {len(X_test)}")
    
    # Create CountVectorizer
    vectorizer = CountVectorizer(
        lowercase=True,
        token_pattern=r'[a-z_]+',
        max_features=500
    )
    
    # Fit and transform training data
    X_train_vectorized = vectorizer.fit_transform(X_train)
    X_test_vectorized = vectorizer.transform(X_test)
    
    print(f"\nVocabulary size: {len(vectorizer.vocabulary_)}")
    
    # Train Multinomial Naive Bayes
    print("\nTraining Multinomial Naive Bayes classifier...")
    model = MultinomialNB(alpha=1.0)
    model.fit(X_train_vectorized, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_vectorized)
    accuracy = accuracy_score(y_test, y_pred)
    train_accuracy = accuracy_score(y_train, model.predict(X_train_vectorized))
    
    print(f"\n{'='*50}")
    print(f"Model Accuracy: {accuracy * 100:.2f}%")
    print(f"{'='*50}")
    
    # Detailed classification report
    print("\nClassification Report:")
    y_test_labels = label_encoder.inverse_transform(y_test)
    y_pred_labels = label_encoder.inverse_transform(y_pred)
    print(classification_report(y_test_labels, y_pred_labels, zero_division=0))
    
    # --- Generate Charts ---
    print("\nGenerating evaluation charts...")
    ml_dir = SCRIPT_DIR
    os.makedirs(ml_dir, exist_ok=True)
    classes = label_encoder.classes_
    
    # 1. Accuracy Comparison Chart
    plt.figure(figsize=(8, 6))
    bars = plt.bar(['Training Accuracy', 'Test Accuracy'], [train_accuracy, accuracy], color=['#4CAF50', '#2196F3'])
    plt.title('Model Accuracy Comparison')
    plt.ylim(0, 1.1)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f'{yval*100:.2f}%', ha='center', va='bottom')
    plt.tight_layout()
    plt.savefig(os.path.join(ml_dir, 'accuracy_comparison.png'))
    plt.close()
    
    # 2. Confusion Matrix
    plt.figure(figsize=(16, 12))
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=False, cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title('Confusion Matrix')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(ml_dir, 'confusion_matrix.png'))
    plt.close()
    
    # 3. Training History (Learning Progress across Dataset Sizes)
    # Naive Bayes learns without epochs, so we simulate history by progressively training on more data.
    plt.figure(figsize=(10, 6))
    train_history_acc = []
    val_history_acc = []
    fractions = np.linspace(0.1, 1.0, 10)
    
    for frac in fractions:
        subset_size = max(1, int(frac * X_train_vectorized.shape[0]))
        X_sub = X_train_vectorized[:subset_size]
        y_sub = y_train[:subset_size]
        
        temp_model = MultinomialNB(alpha=1.0)
        temp_model.fit(X_sub, y_sub)
        
        train_history_acc.append(accuracy_score(y_sub, temp_model.predict(X_sub)))
        val_history_acc.append(accuracy_score(y_test, temp_model.predict(X_test_vectorized)))

    plt.plot(fractions * 100, train_history_acc, 'o-', color='r', label='Training Accuracy')
    plt.plot(fractions * 100, val_history_acc, 'o-', color='g', label='Validation (Test) Accuracy')
    plt.title('Training History (Accuracy vs Data Volume)')
    plt.xlabel('Percentage of Training Data Used (%)')
    plt.ylabel('Accuracy')
    plt.legend(loc='lower right')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(ml_dir, 'training_history.png'))
    plt.close()
    
    # 4. Fast One More: F1-Scores per Disease
    plt.figure(figsize=(14, 6))
    report = classification_report(y_test_labels, y_pred_labels, output_dict=True, zero_division=0)
    classes_only = {k: v['f1-score'] for k, v in report.items() if k not in ['accuracy', 'macro avg', 'weighted avg']}
    sorted_classes = sorted(classes_only.items(), key=lambda x: x[1], reverse=True)
    top_classes = [x[0] for x in sorted_classes[:30]] 
    top_f1s = [x[1] for x in sorted_classes[:30]]
    
    plt.bar(top_classes, top_f1s, color='coral')
    plt.title('F1-Score per Disease Model Performance (Top 30)')
    plt.xlabel('Disease')
    plt.ylabel('F1-Score')
    plt.xticks(rotation=90)
    plt.ylim(0, 1.1)
    plt.tight_layout()
    plt.savefig(os.path.join(ml_dir, 'f1_scores_per_disease.png'))
    plt.close()
    
    print("Charts saved successfully as PNG files in the ml directory.")
    
    return model, vectorizer, label_encoder

def save_model(model, vectorizer, label_encoder):
    """Save the trained model and preprocessors"""
    
    # Create ml directory if it doesn't exist
    ml_dir = SCRIPT_DIR
    os.makedirs(ml_dir, exist_ok=True)
    
    # Save model
    model_path = os.path.join(ml_dir, 'model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\nModel saved to: {model_path}")
    
    # Save vectorizer
    vectorizer_path = os.path.join(ml_dir, 'vectorizer.pkl')
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
    print(f"Vectorizer saved to: {vectorizer_path}")
    
    # Save label encoder
    label_encoder_path = os.path.join(ml_dir, 'label_encoder.pkl')
    with open(label_encoder_path, 'wb') as f:
        pickle.dump(label_encoder, f)
    print(f"Label encoder saved to: {label_encoder_path}")

def test_prediction(model, vectorizer, label_encoder):
    """Test the model with sample symptoms"""
    
    print("\n" + "="*50)
    print("Testing predictions with sample symptoms:")
    print("="*50)
    
    test_cases = [
        "itching skin_rash nodal_skin_eruptions",
        "continuous_sneezing shivering chills",
        "stomach_pain acidity ulcers_on_tongue vomiting",
        "chest_pain breathlessness sweating",
        "fatigue weight_loss restlessness high_fever"
    ]
    
    for symptoms in test_cases:
        symptoms_vec = vectorizer.transform([symptoms])
        prediction = model.predict(symptoms_vec)
        proba = model.predict_proba(symptoms_vec)
        disease = label_encoder.inverse_transform(prediction)[0]
        confidence = max(proba[0]) * 100
        
        print(f"\nSymptoms: {symptoms}")
        print(f"Predicted Disease: {disease}")
        print(f"Confidence: {confidence:.2f}%")

def main():
    """Main function to train and save the model"""
    
    print("="*60)
    print("Smart Patient Healthcare System - ML Model Training")
    print("="*60)
    
    # Load and preprocess data
    df = load_and_preprocess_data()
    
    # Train model
    model, vectorizer, label_encoder = train_model(df)
    
    # Save model
    save_model(model, vectorizer, label_encoder)
    
    # Test predictions
    test_prediction(model, vectorizer, label_encoder)
    
    print("\n" + "="*60)
    print("Model training completed successfully!")
    print("="*60)

if __name__ == "__main__":
    main()
