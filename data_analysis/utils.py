import numpy as np

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Here is a sample classification algorithm, it is the simple (yet very competitive) one-nearest
# neighbor using the Euclidean distance.
# If you are advocating a new distance measure you just need to change the line marked "Euclidean distance"
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
def Classification_Algorithm(TRAIN, TRAIN_class_labels, unknown_object):
    best_so_far = float('inf')
    predicted_class = None

    for i in range(len(TRAIN_class_labels)):
        compare_to_this_object = TRAIN[i, :]
        distance = np.sqrt(np.sum((compare_to_this_object - unknown_object)**2)) # Euclidean distance

        if distance < best_so_far:
            predicted_class = TRAIN_class_labels[i]
            best_so_far = distance

    return predicted_class


def UCR_time_series_test():
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    TRAIN = np.loadtxt('SyntheticControl_TRAIN.tsv') # Only these two lines need to be changed to test a different data set. %
    TEST = np.loadtxt('SyntheticControl_TEST.tsv')   # Only these two lines need to be changed to test a different data set. %
    # %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    TRAIN_class_labels = TRAIN[:, 0] # Pull out the class labels (0 column in Python).
    TRAIN = TRAIN[:, 1:]             # Remove class labels from training set.

    TEST_class_labels = TEST[:, 0]   # Pull out the class labels.
    TEST = TEST[:, 1:]               # Remove class labels from testing set.

    correct = 0 # Initialize the number we got correct

    for i in range(len(TEST_class_labels)): # Loop over every instance in the test set
        classify_this_object = TEST[i, :]
        this_objects_actual_class = TEST_class_labels[i]

        predicted_class = Classification_Algorithm(TRAIN, TRAIN_class_labels, classify_this_object)

        if predicted_class == this_objects_actual_class:
            correct = correct + 1

        # Report progress (Aggiungo +1 a 'i' per stampare da 1 a N esattamente come fa MATLAB)
        print(str(i + 1) + ' out of ' + str(len(TEST_class_labels)) + ' done')

        # %%%%%%%%%%%%%%%%% Create Report %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    print('The dataset you tested has ' + str(len(np.unique(TRAIN_class_labels))) + ' classes')
    print('The training set is of size ' + str(TRAIN.shape[0]) + ', and the test set is of size ' + str(TEST.shape[0]) + '.')
    print('The time series are of length ' + str(TRAIN.shape[1]))
    error_rate = (len(TEST_class_labels) - correct) / len(TEST_class_labels)
    print('The error rate was ' + str(error_rate))
    # %%%%%%%%%%%%%%%%% End Report %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

