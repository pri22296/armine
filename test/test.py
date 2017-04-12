from arm import ARM, ARMClassifier

def test_arm():
    ar = ARM()
    ar.load_from_csv('data1.csv')
    ar.learn()
    ar.print_rules()

def test_arm_classifier():
    ar = ARMClassifier()
    ar.load_from_csv('raw.csv', -1, False)
    ar.learn()
    ar.print_rules()

def main():
    test_arm()
    test_arm_classifier()

if __name__ == '__main__':
    main()
