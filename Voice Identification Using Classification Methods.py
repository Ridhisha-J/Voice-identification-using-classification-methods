from google.colab import drive
drive.mount('/content/drive')

"""LIBRARIES"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import os
import pathlib
import csv

import librosa
import librosa.display

import tensorflow as tf

from tensorflow.keras import layers
from tensorflow.keras import regularizers

from keras.models import Sequential
from keras.layers import Dense
from keras.wrappers.scikit_learn import KerasClassifier
from keras.utils import np_utils
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV

#Confusion Matrix
from sklearn.metrics import confusion_matrix
from sklearn.metrics import plot_confusion_matrix

# Preprocessing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

#Keras
import keras

"""EXPLORATORY DATA ANALYSIS FOR RAW AUDIO FILE"""

# SPECTOGRAM 
color_map = plt.get_cmap('magma')
plt.figure(figsize=(8,8))

genres  = 'cat dog female male'.split()

for g in genres :
    pathlib.Path(f'images_data/{g}').mkdir(parents=True, exist_ok=True)
    for filename in os.listdir(f'/content/drive/MyDrive/cluster/{g}'):
        voicename = f'/content/drive/MyDrive/cluster/{g}/{filename}'
        y, sr = librosa.load(voicename, mono=True, duration=5)
        plt.specgram(y, NFFT=2048, Fs=2, noverlap=128, cmap=color_map, scale='dB');
        plt.axis('off');
        plt.savefig(f'images_data/{g}/{filename[:-3].replace("."," ")}.png')
        plt.clf()

# MEL SPECTOGRAM
cmap = plt.get_cmap('inferno')
plt.figure(figsize=(8,8))

genres = 'cat dog female male'.split()

for g in genres:
    pathlib.Path(f'mel_images_data/{g}').mkdir(parents=True, exist_ok=True)
    for filename in os.listdir(f'./drive/My Drive/cluster/{g}'):
        voicename = f'./drive/My Drive/cluster/{g}/{filename}'
        y, sr = librosa.load(voicename,sr=None)
        S = librosa.feature.melspectrogram(y=y, sr=sr)
        librosa.display.specshow(librosa.power_to_db(S, ref=np.max))
        plt.axis('off')
        plt.savefig(f'mel_images_data/{g}/{filename[:-3].replace(".", "")}.png')
        plt.clf()

# DIRECTORY OF CERTAIN AUDIO FILES
cat_path=f'/content/drive/MyDrive/cluster/cat/cat_45.wav'
dog_path=f'/content/drive/MyDrive/cluster/dog/dog_barking_11.wav'
female_path=f'/content/drive/MyDrive/cluster/female/female_21.wav'
male_path=f'/content/drive/MyDrive/cluster/male/male_31.wav'

# LOADING THE AUDIO FILE
cat_audio, sr =librosa.load(cat_path)
dog_audio, sr =librosa.load(dog_path)
female_audio, sr =librosa.load(female_path)
male_audio, sr =librosa.load(male_path)

# SAMPLE CLIPS OF AUDIO FILE
import IPython.display as ipd
def play_audio(file_path):
  play = ipd.Audio(file_path)
  return play

play_audio(cat_path)

play_audio(dog_path)

play_audio(female_path)

play_audio(male_path)

# WAVE PLOT
def waveplot(title,file):
  plt.title(title)
  librosa.display.waveplot(file)
  show = plt.show()
  return show

waveplot("cat",cat_audio)
waveplot("dog",dog_audio)
waveplot("female",female_audio)
waveplot("male",male_audio)

# ZOOM IN PLOT
start = 9000
end = 9100
def zoomin(title,file):
  zero_crossings = librosa.zero_crossings(cat_audio[start:end], pad=False)
  plt.plot(file[start:end])
  plt.title(title)
  zoom = plt.show()
  return zoom

zoomin("cat",cat_audio)
zoomin("dog",dog_audio)
zoomin("female",female_audio)
zoomin("male",male_audio)

# MEL FREQUENCY CEPSTRAL COEFFICIENT (MFCC)
def mfcc(title,file):
  mfccs = librosa.feature.mfcc(file, sr=sr)
  color_map = plt.get_cmap('inferno')
  plt.figure(figsize=(8,5)) 
  plt.title(title)
  m = librosa.display.specshow(mfccs, sr=sr,cmap=color_map, x_axis='time')
  return m

mfcc("cat",cat_audio)
mfcc("dog",dog_audio)
mfcc("female",female_audio)
mfcc("male",male_audio)

"""AUDIO FEATURE EXTRACTION + EDA """

# HEADER FOR EACH COLUMNS
header = 'filename chroma_stft rmse spectral_centroid spectral_bandwidth rolloff zero_crossing_rate'
for i in range(1, 21):
    header += f' mfcc{i}'
header += ' label'
header = header.split()

# FEATURE EXTRACTED FILE
file = open('dataset.csv', 'w', newline='')
with file:
    writer = csv.writer(file)
    writer.writerow(header)
genres = 'cat dog female male'.split()
for g in genres:
    for filename in os.listdir(f'./drive/My Drive/cluster/{g}'):
        voicename = f'./drive/My Drive/cluster/{g}/{filename}'
        y, sr = librosa.load(voicename, mono=True, duration=3)
        rmse = librosa.feature.rms(y=y)
        chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
        spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)
        spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        zcr = librosa.feature.zero_crossing_rate(y)
        mfcc = librosa.feature.mfcc(y=y, sr=sr)
        to_append = f'{filename} {np.mean(chroma_stft)} {np.mean(rmse)} {np.mean(spec_cent)} {np.mean(spec_bw)} {np.mean(rolloff)} {np.mean(zcr)}'    
        for e in mfcc:
            to_append += f' {np.mean(e)}'
        to_append += f' {g}'
        file = open('dataset.csv', 'a', newline='')
        with file:
            writer = csv.writer(file)
            writer.writerow(to_append.split())

# PREVIEW OF DATASET
AudioData=pd.read_csv('dataset.csv')
AudioData.head()

# DIMENSION OF THE DATASET
AudioData.shape

# INFORMATION ABOUT DATASET
AudioData.info()

# SUMMARY OF DATASET
AudioData.describe().T

# COUNT PLOT FOR TARGET CLASS
import seaborn as sns
sns.countplot(x=AudioData['label'] ,data=AudioData)
plt.ylabel("Count of each Target class")
plt.xlabel("Target classes")
plt.show()

# PRINCIPLE COMPONENT SCATTER PLOT

data = AudioData.iloc[0:, 1:]

X = data.loc[:, data.columns != 'label']
y = data['label']

import sklearn.preprocessing as skp
# normalize
cols = X.columns
min_max_scaler = skp.MinMaxScaler()
np_scaled = min_max_scaler.fit_transform(X)
X = pd.DataFrame(np_scaled, columns = cols)

# Top 2 pca components
from sklearn.decomposition import PCA
import seaborn as sns
sns.set_style('whitegrid')

pca = PCA(n_components=2)
principalComponents = pca.fit_transform(X)
principalDf = pd.DataFrame(data = principalComponents, columns = ['pc1', 'pc2'])

# concatenate with target label
finalDf = pd.concat([principalDf, y], axis = 1)

plt.figure(figsize = (16, 9))
sns.scatterplot(x = "pc1", y = "pc2", data = finalDf, hue = "label", alpha = 0.7, s = 100);

plt.title('PCA on Genres', fontsize = 20)
plt.xticks(fontsize = 14)
plt.yticks(fontsize = 10);
plt.xlabel("Principal Component 1", fontsize = 15)
plt.ylabel("Principal Component 2", fontsize = 15)
plt.savefig("PCA_Scattert.png")

# HEAT MAP
plt.figure(figsize=(15,15))
p=sns.heatmap(AudioData.corr(), annot=True,cmap='RdYlGn',center=0) 
plt.savefig("Corr_Heatmap.png")

# HISTOGRAM
AudioData.hist(figsize=(15,12),bins = 15)
plt.title("Features Distribution")
plt.show()

# CHECKING MISSING VALUES
AudioData.isnull().sum()

# EXPLORE TARGET VARIABLE
AudioData['label'].value_counts()

"""DATASET + PRE-PROCESSING"""

import copy
data = copy.deepcopy(AudioData)

# ENCODE TARGET CLASS
data['label'],class_names = pd.factorize(data['label'])
class_names

# DROP OF UNUSED COLUMN
data.drop('filename',inplace=True,axis=1)

genre_list = data.iloc[:, -1]

from sklearn.preprocessing import LabelEncoder
encoder = LabelEncoder()
y = encoder.fit_transform(genre_list)

# SCALE THE FEATURES COLUMNS
scaler = StandardScaler()
X = scaler.fit_transform(np.array(data.iloc[:, :-1], dtype = float))

# SPLIT DATA INTO TRAIN AND TEST
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 24)

"""ANN MODEL"""

# SPLIT DATA INTO TRAIN AND TEST
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20, random_state = 24)

from sklearn.preprocessing import StandardScaler
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)


# MODEL BUILDING
classifier = Sequential()
classifier.add(Dense(256, activation='relu', input_shape=(X_train.shape[1],)))
classifier.add(Dense(128, activation = 'relu'))
classifier.add(Dense(64, activation='relu'))
classifier.add(Dense(32, activation = 'softmax'))
#classifier.summary()

# COMPILE
classifier.compile(optimizer = 'adam', loss = 'sparse_categorical_crossentropy', metrics = ['accuracy'])

# FITTING THE ANN
model = classifier.fit(X_train, y_train, batch_size = 128, epochs = 100,verbose = 0)

# MODEL EVALUATION
Score , Accuracy= classifier.evaluate(X_test, y_test,batch_size=25)
print("ACCURACY OF ANN MODEL : ",Accuracy*100)

import copy
data = copy.deepcopy(AudioData)

# ENCODE TARGET CLASS
data['label'],class_names = pd.factorize(data['label'])
class_names

# DROP OF UNUSED COLUMN
data.drop('filename',inplace=True,axis=1)

genre_list = data.iloc[:, -1]

from sklearn.preprocessing import LabelEncoder
encoder = LabelEncoder()
y = encoder.fit_transform(genre_list)

# SCALE THE FEATURES COLUMNS
scaler = StandardScaler()
X = scaler.fit_transform(np.array(data.iloc[:, :-1], dtype = float))

# SPLIT DATA INTO TRAIN AND TEST
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20, random_state = 24)

from sklearn.preprocessing import StandardScaler
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)


# MODEL BUILDING
classifier = Sequential()
classifier.add(Dense(256, activation='relu', input_shape=(X_train.shape[1],)))
classifier.add(Dense(128, activation = 'relu'))
classifier.add(Dense(64, activation='relu'))
classifier.add(Dense(32, activation = 'softmax'))
#classifier.summary()

# COMPILE
classifier.compile(optimizer = 'adam', loss = 'sparse_categorical_crossentropy', metrics = ['accuracy'])

# FITTING THE ANN
model = classifier.fit(X_train, y_train, batch_size = 128, epochs = 100,verbose = 0)

# MODEL EVALUATION
Score , Accuracy= classifier.evaluate(X_test, y_test,batch_size=25)
print("ACCURACY OF ANN MODEL : ",Accuracy*100)

#PREDICTION WITH CLASSIFIER 
ann_pred = classifier.predict(X_test)

#PREDICTION WITH CLASSIFIER 
#y_pred = (y_pred > 0.5) 
predict = np.argmax(ann_pred, axis=1)
predict

"""KNN MODEL"""

# FEATURE SCALING
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

from sklearn.neighbors import KNeighborsClassifier
knn = KNeighborsClassifier(n_neighbors=3)

knn.fit (X_train, y_train)

knn_pred=knn.predict(X_test)

from sklearn.metrics import accuracy_score
# Predict the labels for the test data

acc = accuracy_score(y_test, knn_pred)
print("Accuracy : ",acc*100)

"""DECISION TREE MODEL"""

# FEATURE SCALING
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

# DECISION TREE CLASSIFIER
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
dectree = DecisionTreeClassifier ()

# FITTING MODEL
dectree.fit(X_train, y_train)

# MODEL PREDICTION
dec_pred=dectree.predict(X_test)

from sklearn.metrics import accuracy_score
# Predict the labels for the test data
acc = accuracy_score(y_test, dec_pred)
print("Accuracy : ",acc*100)

# TEST SET ACCURACY SCORE 
print("Test Score",dectree.score(X_test,y_test))

# TRAIN SET ACCURACY SCORE 
print("Train Score",dectree.score(X_train,y_train))

from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier
from sklearn import metrics
# ADABOOST CLASSIFIER
adaboost = AdaBoostClassifier(n_estimators=100,learning_rate=1.0)
adaboost.fit(X_train, y_train)
# EVALUATION
print("Train score: ",adaboost.score(X_train, y_train))
print("Test score: ",adaboost.score(X_test, y_test))
y_pred = adaboost.predict(X_test)
print("\nAccuracy of Adaboost : ",metrics.accuracy_score(y_test, y_pred))

"""LOGISTIC REGRESSION"""

# FEATURE SCALING
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression

logreg = LogisticRegression(random_state=24)
logreg.fit(X_train, y_train)
pred_logit = logreg.predict(X_test)

accuracy = accuracy_score(y_test, pred_logit)
print("Accuracy : ",accuracy*100)

"""MODEL EVALUATION"""

from sklearn.model_selection import cross_val_score,cross_val_predict,KFold

# ACCURACY
def accuracy(model):
 y_pred = model.predict(X_test)
 acc = metrics.accuracy_score(y_test,y_pred)
 return acc

print("\t\tACCURACY SCORE")
Accuracy= classifier.evaluate(X_test, y_test,batch_size=25)
print("\nANN MODEL      :",Accuracy[1])
print("\nKNN CLASSIFIER :",accuracy(knn))
print("\nDECISION TREE  :",accuracy(dectree))
print("\nADABOOST       :",accuracy(adaboost))
print("\nLOGISTIC REGRESSION :",accuracy(logreg))

# BAR PLOT FOR ACCURACY
import matplotlib.pyplot as plt

acc = []
ANN = classifier.evaluate(X_test, y_test,batch_size=25)
KNN = metrics.accuracy_score(y_test,knn_pred)
DT = metrics.accuracy_score(y_test,dec_pred)
LR = metrics.accuracy_score(y_test,pred_logit)

acc.append(ANN[1])
acc.append(KNN)
acc.append(DT)
acc.append(LR)

models = ['ANN', 'KNN' ,'DT', 'LR']

# creating the bar plot
fig, axes = plt.subplots(figsize=(7,5))
plt.bar(models,acc,color="dodgerblue")
plt.xlabel("CLASSIFICATION MODELS")
plt.ylabel("PERCENTAGE OF ACCURACY")
plt.title("ACCURACY OF CLASSIFICATION MODELS")
plt.show()

# K-FOLD CROSS VALIDATION
def kfold_cross_validation(num,model):
 kfold = KFold(n_splits=num)
 results = cross_val_score(model, X, y,cv=kfold)
 r = results.mean()
 return r

print("KFOLD CROSS VALIDATION SCORE\n")

print("\nLOGISTIC REGRESSION :",kfold_cross_validation(30,logreg))
print("\nDECISION TREE  :",kfold_cross_validation(30,dectree))
print("\nKNN CLASSIFIER :",kfold_cross_validation(30,knn))

print("\n\n\n\n")

# K-FOLD CROSS VALIDATION FOR ANN

import warnings
warnings.filterwarnings('ignore')

from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.model_selection import cross_val_score

def build_classifier():
  model = Sequential()
  model.add(Dense(256, activation='relu', input_shape=(X_train.shape[1],)))
  model.add(Dense(128, activation='relu'))
  model.add(Dense(64, activation='relu'))
  model.add(Dense(32, activation='softmax'))
  model.compile(optimizer='adam',loss='sparse_categorical_crossentropy',metrics=['accuracy'])
  return model 

kfold = KFold(n_splits=30)

classifier = KerasClassifier(build_fn = build_classifier, batch_size = 25, epochs = 100)
accuracies = cross_val_score(estimator = classifier, X = X_train, y = y_train, cv = kfold)
mean = accuracies.mean()
print('mean : ' ,mean)

# CROSS VALIDATION
def cross_validation(model):
 score = cross_val_score(model ,X,y,cv=30)
 avg_score = np.average(score)
 return avg_score

print("CROSS VALIDATION SCORE\n")
print("\nLOGISTIC REGRESSION :",cross_validation(logreg))
print("\nDECISION TREE  :",cross_validation(dectree))
print("\nKNN CLASSIFIER :",cross_validation(knn))

# CROSS VALIDATION FOR ANN

import warnings
warnings.filterwarnings('ignore')

from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.model_selection import cross_val_score

def build_classifier():
  model = Sequential()
  model.add(Dense(256, activation='relu', input_shape=(X_train.shape[1],)))
  model.add(Dense(128, activation='relu'))
  model.add(Dense(64, activation='relu'))
  model.add(Dense(32, activation='softmax'))
  model.compile(optimizer='adam',loss='sparse_categorical_crossentropy',metrics=['accuracy'])
  return model 

cclassifier = KerasClassifier(build_fn = build_classifier, batch_size = 25, epochs = 100)
accuracies = cross_val_score(estimator = cclassifier, X = X_train, y = y_train, cv = 30)
mean = accuracies.mean()
print('mean : ' ,mean)

# CLASSIFICATION REPORT
from sklearn.metrics import classification_report

class_rep_tree = classification_report(y_test, dec_pred)
class_rep_log = classification_report(y_test, pred_logit)
class_rep_knn = classification_report(y_test,knn_pred)


print("Decision Tree: \n", class_rep_tree)
print("Logistic Regression: \n", class_rep_log)
print("KNN: \n", class_rep_knn)

from sklearn.metrics import f1_score,recall_score,precision_score
#PREDICTION WITH CLASSIFIER 

print('Recall: %.3f' % recall_score(y_test, predict, average='macro'))
print('F1 Score: %.3f' % f1_score(y_test, predict, average='macro'))
print('Precision: %.3f' % precision_score(y_test, predict, average='macro'))

import numpy as np
import matplotlib.pyplot as plt

# set width of bar
barWidth = 0.25
fig = plt.subplots(figsize =(12, 8))

precision = []
pANN = precision_score(y_test, predict, average='macro')*100
pKNN = precision_score(y_test, knn_pred, average='macro')*100
pDT = precision_score(y_test, dec_pred, average='macro')*100
pLR = precision_score(y_test, pred_logit, average='macro')*100
precision.append(pANN)
precision.append(pKNN)
precision.append(pDT)
precision.append(pLR)

recall = []
rANN = recall_score(y_test, predict, average='macro')*100
rKNN = recall_score(y_test, knn_pred, average='macro')*100
rDT = recall_score(y_test, dec_pred, average='macro')*100
rLR = recall_score(y_test, pred_logit, average='macro')*100
recall.append(rANN)
recall.append(rKNN)
recall.append(rDT)
recall.append(rLR)


f1 = []
fANN = f1_score(y_test, predict, average='macro')*100
fKNN = f1_score(y_test, knn_pred, average='macro')*100
fDT = f1_score(y_test, dec_pred, average='macro')*100
fLR = f1_score(y_test, pred_logit, average='macro')*100
f1.append(fANN)
f1.append(fKNN)
f1.append(fDT)
f1.append(fLR)


# Set position of bar on X axis
br1 = np.arange(len(precision))
br2 = [x + barWidth for x in br1]
br3 = [x + barWidth for x in br2]

# Make the plot
plt.bar(br1, precision, color ='r', width = barWidth,
		edgecolor ='grey', label ='Precision')
plt.bar(br2, recall, color ='g', width = barWidth,
		edgecolor ='grey', label ='Recall')
plt.bar(br3, f1, color ='b', width = barWidth,
		edgecolor ='grey', label ='F1 Score')

# Adding Xticks
plt.xlabel('CLASSIFICATION MODELS')
plt.ylabel('PERCENTAGE OF MODELS')
plt.xticks([r + barWidth for r in range(len(precision))],
		['ANN','KNN', 'DT', 'LR'])

plt.legend()
plt.show()

models = []
models.append(('ANN ',classifier))
models.append(('KNN', KNeighborsClassifier()))
models.append(('Logistic Regression', LogisticRegression(random_state=24)))
models.append(('Decision Tree',DecisionTreeClassifier(random_state=24)))


#Evaluate each model in turn
results = []
names = []
scoring = 'accuracy'
for name, model in models:
  kfold = KFold(n_splits=25)
  cv_results = cross_val_score(model, X,y, cv=kfold, scoring=scoring)
  results.append (cv_results)
  names.append(name)
  print("\n")
  msg = "%s : %f " % (name, cv_results.mean( ))
  print(msg)

#boxplot algorithm comparison
fig=plt.figure()
fig.suptitle( 'Comparison of Models')
ax=fig.add_subplot(111)
plt.boxplot(results)
ax.set_xticklabels(names)
plt.show()

