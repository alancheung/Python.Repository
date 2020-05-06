import numpy as np
import cv2
import os
from os import path
from numpy.linalg import norm

trainingDirPath = '/home/pi/Desktop/WandTraining/'
trainingShapeDirPath = 'Shapes/circle/'

class StatModel(object):
    def load(self, fn):
        self.model.load(fn)  # Known bug: https://github.com/opencv/opencv/issues/4969
    def save(self, fn):
        self.model.save(fn)

class KNearest(StatModel):
    def __init__(self, k = 3):
        self.k = k
        self.model = cv2.ml.KNearest_create()

    def train(self, samples, responses):
        self.model.train(samples, cv2.ml.ROW_SAMPLE, responses)

    def predict(self, samples):
        _retval, results, _neigh_resp, _dists = self.model.findNearest(samples, self.k)
        return results.ravel()

class SVM(StatModel):
    def __init__(self, C = 1, gamma = 0.5):
        self.model = cv2.ml.SVM_create()
        self.model.setGamma(gamma)
        self.model.setC(C)
        self.model.setKernel(cv2.ml.SVM_RBF)
        self.model.setType(cv2.ml.SVM_C_SVC)

    def train(self, samples, responses):
        self.model.train(samples, cv2.ml.ROW_SAMPLE, responses)

    def predict(self, samples):
        return self.model.predict(samples)[1].ravel()

def createTrainingImgName(count):
    return 'shape1-' + str(count) + '.png'

def preprocess_hog(image):
    samples = []

    gx = cv2.Sobel(image, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(image, cv2.CV_32F, 0, 1)
    mag, ang = cv2.cartToPolar(gx, gy)
    bin_n = 16
    bin = np.int32(bin_n*ang/(2*np.pi))
    bin_cells = bin[:10,:10], bin[10:,:10], bin[:10,10:], bin[10:,10:]
    mag_cells = mag[:10,:10], mag[10:,:10], mag[:10,10:], mag[10:,10:]
    hists = [np.bincount(b.ravel(), m.ravel(), bin_n) for b, m in zip(bin_cells, mag_cells)]
    hist = np.hstack(hists)

    # transform to Hellinger kernel
    eps = 1e-7
    hist /= hist.sum() + eps
    hist = np.sqrt(hist)
    hist /= norm(hist) + eps

    for i in range(0, 499):
        samples.append(hist)
    return np.float32(samples)

datFile = trainingDirPath + 'digits_svm.dat'
svm = SVM(C = 2.67, gamma = 5.383)
svm.load(datFile)

for i in range(1, 10):
    fullPath = trainingDirPath + trainingShapeDirPath + createTrainingImgName(i)
    if path.exists(fullPath):
        print(fullPath)
        image = cv2.imread(fullPath, cv2.IMREAD_GRAYSCALE)
        process = preprocess_hog(image)

        print(process)
        print(process.shape)

        process = np.asmatrix(process)
        process = np.float32(process)
        print(svm.predict(process))

        #h, w = image.shape[:2]
        #image = resizeImage(image, (h,w), 40)
        #process = preprocess_hog(image)
        
        #trainingImages.append(image)
        #trainingImageData.append(process)

        #cv2.imshow('scaled', image)
        #cv2.imshow('hog', process)
        cv2.waitKey(0)
